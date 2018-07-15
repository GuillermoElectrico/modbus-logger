#!/usr/bin/env python3

from influxdb import InfluxDBClient
from datetime import datetime, timedelta
from os import path
import sys
import os
import serial
import time
import yaml
import logging
import modbus_tk
import modbus_tk.defines as cst
from modbus_tk import modbus_rtu

#PORT = 1
PORT = '/dev/ttyUSB0'

# Change working dir to the same dir as this script
os.chdir(sys.path[0])

class DataCollector:
    def __init__(self, influx_client, device_yaml):
        self.influx_client = influx_client
        self.device_yaml = device_yaml
        self.max_iterations = None  # run indefinitely by default
        self.device_map = None
        self.device_map_last_change = -1
        log.info('Devices:')
        for device in sorted(self.get_devices(), key=lambda x:sorted(x.keys())):
            log.info('\t {} <--> {}'.format( device['id'], device['name']))

    def get_devices(self):
        assert path.exists(self.device_yaml), 'Device map not found: %s' % self.device_yaml
        if path.getmtime(self.device_yaml) != self.device_map_last_change:
            try:
                log.info('Reloading device map as file changed')
                new_map = yaml.load(open(self.device_yaml))
                self.device_map = new_map['devices']
                self.device_map_last_change = path.getmtime(self.device_yaml)
            except Exception as e:
                log.warning('Failed to re-load device map, going on with the old one.')
                log.warning(e)
        return self.device_map

    def collect_and_store(self):
        #instrument.debug = True
        devices = self.get_devices()
        t_utc = datetime.utcnow()
        t_str = t_utc.isoformat() + 'Z'

        datas = dict()
        device_id_name = dict() # mapping id to name

        for device in devices:
            device_id_name[device['id']] = device['name']
			
            try:
                master = modbus_rtu.RtuMaster(
                    serial.Serial(port=PORT, baudrate=device['baudrate'], bytesize=device['bytesize'], parity=device['parity'], stopbits=device['stopbits'], xonxoff=0)
                )
					
                master.set_timeout(device['timeout'])
                master.set_verbose(True)

                log.debug('Reading device %s.' % (device['id']))
                start_time = time.time()
                parameters = yaml.load(open(device['type']))
                datas[device['id']] = dict()

                for parameter in parameters:
                    # If random readout errors occour, e.g. CRC check fail, test to uncomment the following row
                    #time.sleep(0.01) # Sleep for 10 ms between each parameter read to avoid errors
                    retries = 10
                    while retries > 0:
                        try:
                            retries -= 1
                            datas[device['id']][parameter] = master.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter], 2)
                            retries = 0
                            pass
                        except ValueError as ve:
                            log.warning('Value Error while reading register {} from device {}. Retries left {}.'
                                   .format(parameters[parameter], device['id'], retries))
                            log.error(ve)
                            if retries == 0:
                                raise RuntimeError
                        except TypeError as te:
                            log.warning('Type Error while reading register {} from device {}. Retries left {}.'
                                   .format(parameters[parameter], device['id'], retries))
                            log.error(te)
                            if retries == 0:
                                raise RuntimeError
                        except IOError as ie:
                            log.warning('IO Error while reading register {} from device {}. Retries left {}.'
                                   .format(parameters[parameter], device['id'], retries))
                            log.error(ie)
                            if retries == 0:
                                raise RuntimeError
                        except:
                            log.error("Unexpected error:", sys.exc_info()[0])
                            raise

                datas[device['id']]['Read time'] =  time.time() - start_time
			
            except modbus_tk.modbus.ModbusError as exc:
                log.error("%s- Code=%d", exc, exc.get_exception_code())

        json_body = [
            {
                'measurement': 'energy',
                'tags': {
                    'id': device_id,
                    'device': device['name'],
                },
                'time': t_str,
                'fields': datas[device_id]
            }
            for device_id in datas
        ]
        if len(json_body) > 0:
            try:
                self.influx_client.write_points(json_body)
                log.info(t_str + ' Data written for %d devices.' % len(json_body))
            except Exception as e:
                log.error('Data not written!')
                log.error(e)
                raise
        else:
            log.warning(t_str, 'No data sent.')


def repeat(interval_sec, max_iter, func, *args, **kwargs):
    from itertools import count
    import time
    starttime = time.time()
    for i in count():
        if interval_sec > 0:
            time.sleep(interval_sec - ((time.time() - starttime) % interval_sec))
        if i % 1000 == 0:
            log.info('Collected %d readouts' % i)
        try:
            func(*args, **kwargs)
        except Exception as ex:
            log.error(ex)
        if max_iter and i >= max_iter:
            return


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', default=60,
                        help='Device readout interval (seconds), default 60')
    parser.add_argument('--devices', default='devices.yml',
                        help='YAML file containing Device ID, name, type etc. Default "devices.yml"')
    parser.add_argument('--log', default='CRITICAL',
                        help='Log levels, DEBUG, INFO, WARNING, ERROR or CRITICAL')
    parser.add_argument('--logfile', default='',
                        help='Specify log file, if not specified the log is streamed to console')
    args = parser.parse_args()
    interval = int(args.interval)
    loglevel = args.log.upper()
    logfile = args.logfile

    # Setup logging
    log = logging.getLogger('energy-logger')
    log.setLevel(getattr(logging, loglevel))

    if logfile:
        loghandle = logging.FileHandler(logfile, 'w')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        loghandle.setFormatter(formatter)
    else:
        loghandle = logging.StreamHandler()

    log.addHandler(loghandle)

    log.info('Started app')

    # Create the InfluxDB object
    influx_config = yaml.load(open('influx_config.yml'))
    client = InfluxDBClient(influx_config['host'],
                            influx_config['port'],
                            influx_config['user'],
                            influx_config['password'],
                            influx_config['dbname'])

    collector = DataCollector(influx_client=client,
                              device_yaml=args.devices)

    repeat(interval,
           max_iter=collector.max_iterations,
           func=lambda: collector.collect_and_store())
