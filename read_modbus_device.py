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
from modbus_tk import modbus_tcp
import struct

#PORT = 1
PORT = '/dev/ttyUSB0'
#PORT = '/dev/serial/by-id/usb-1a86_USB2.0-Serial-if00-port0'

# Change working dir to the same dir as this script
os.chdir(sys.path[0])

class DataCollector:
    def __init__(self, influx_yaml, device_yaml):
        self.influx_yaml = influx_yaml
        self.influx_map = None
        self.influx_map_last_change = -1
        self.influx_inteval_save = dict()
        log.info('InfluxDB:')
        for influx_config in sorted(self.get_influxdb(), key=lambda x:sorted(x.keys())):
            log.info('\t {} <--> {}'.format(influx_config['host'], influx_config['name']))
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
                new_map = yaml.load(open(self.device_yaml), Loader=yaml.FullLoader)
                self.device_map = new_map['devices']
                self.device_map_last_change = path.getmtime(self.device_yaml)
            except Exception as e:
                log.warning('Failed to re-load device map, going on with the old one.')
                log.warning(e)
        return self.device_map
		
    def get_influxdb(self):
        assert path.exists(self.influx_yaml), 'InfluxDB map not found: %s' % self.influx_yaml
        if path.getmtime(self.influx_yaml) != self.influx_map_last_change:
            try:
                log.info('Reloading influxDB map as file changed')
                new_map = yaml.load(open(self.influx_yaml), Loader=yaml.FullLoader)
                self.influx_map = new_map['influxdb']
                self.influx_map_last_change = path.getmtime(self.influx_yaml)
                list = 0
                for influx_config in sorted(self.get_influxdb(), key=lambda x:sorted(x.keys())):
                    list = list + 1
                    self.influx_inteval_save[list] = influx_config['interval']
            except Exception as e:
                log.warning('Failed to re-load influxDB map, going on with the old one.')
                log.warning(e)
        return self.influx_map

    def collect_and_store(self):
        #instrument.debug = True
        devices = self.get_devices()
        influxdb = self.get_influxdb()
        t_utc = datetime.utcnow()
        t_str = t_utc.isoformat() + 'Z'

        datas = dict()
        device_id_name = dict() # mapping id to name
        device_slave_id = dict() # mapping list to id
        list = 0

        for device in devices:
            list = list + 1
            device_id_name[list] = device['name']
            device_slave_id[list] = device['id']
			
            try:
                if device['conexion'] == 'R':
                    masterRTU = modbus_rtu.RtuMaster(
                        serial.Serial(port=PORT, baudrate=device['baudrate'], bytesize=device['bytesize'], parity=device['parity'], stopbits=device['stopbits'], xonxoff=0)
                    )
					
                    masterRTU.set_timeout(device['timeout'])
                    masterRTU.set_verbose(True)

                    log.debug('Reading device %s.' % (device['name']))
                    start_time = time.time()
                    parameters = yaml.load(open(device['type']), Loader=yaml.FullLoader)
                    datas[list] = dict()

                    for parameter in parameters:
                        # If random readout errors occour, e.g. CRC check fail, test to uncomment the following row
                        time.sleep(0.5) # Sleep for 500 ms between each parameter read to avoid errors
                        retries = 10
                        while retries > 0:
                            try:
                                retries -= 1
                                if device['function'] == 3:
                                    if parameters[parameter][2] == 1:
                                        resultado = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>f')
                                    elif parameters[parameter][2] == 2:
                                        resultado = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>l')
                                    elif parameters[parameter][2] == 3:
                                        resultado = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                    elif parameters[parameter][2] == 4:
                                        resultadoTemp = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = (resultadoTemp[1]<<16)|resultadoTemp[0]
                                    elif parameters[parameter][2] == 5:
                                        resultado = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>I')
                                    elif parameters[parameter][2] == 6:
                                        resultado = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>L')
                                    elif parameters[parameter][2] == 7:
                                        resultadoTemp = masterRTU.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = struct.unpack('f', struct.pack('I', (resultadoTemp[1]<<16)|resultadoTemp[0]))[0]
                                elif device['function'] == 4:
                                    if parameters[parameter][2] == 1:
                                        resultado = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>f')
                                    elif parameters[parameter][2] == 2:
                                        resultado = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>l')
                                    elif parameters[parameter][2] == 3:
                                        resultado = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                    elif parameters[parameter][2] == 4:
                                        resultadoTemp = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = (resultadoTemp[1]<<16)|resultadoTemp[0]
                                    elif parameters[parameter][2] == 5:
                                        resultado = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>I')
                                    elif parameters[parameter][2] == 6:
                                        resultado = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>L')
                                    elif parameters[parameter][2] == 7:
                                        resultadoTemp = masterRTU.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = struct.unpack('f', struct.pack('I', (resultadoTemp[1]<<16)|resultadoTemp[0]))[0]
                                datas[list][parameter] = resultado[0]
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

                    datas[list]['ReadTime'] =  time.time() - start_time
                elif device['conexion'] == 'T':
                    masterTCP = modbus_tcp.TcpMaster(host=device['direction'],port=device['port'])
					
                    masterTCP.set_timeout(device['timeout'])

                    log.debug('Reading device %s.' % (device['name']))
                    start_time = time.time()
                    parameters = yaml.load(open(device['type']), Loader=yaml.FullLoader)
                    datas[list] = dict()

                    for parameter in parameters:
                        # If random readout errors occour, e.g. CRC check fail, test to uncomment the following row
                        #time.sleep(0.01) # Sleep for 10 ms between each parameter read to avoid errors
                        retries = 10
                        while retries > 0:
                            try:
                                retries -= 1
                                if device['function'] == 3:
                                    if parameters[parameter][2] == 1:
                                        resultado = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>f')
                                    elif parameters[parameter][2] == 2:
                                        resultado = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>l')
                                    elif parameters[parameter][2] == 3:
                                        resultado = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                    elif parameters[parameter][2] == 4:
                                        resultadoTemp = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = (resultadoTemp[1]<<16)|resultadoTemp[0]
                                    elif parameters[parameter][2] == 5:
                                        resultado = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>I')
                                    elif parameters[parameter][2] == 6:
                                        resultado = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>L')
                                    elif parameters[parameter][2] == 7:
                                        resultadoTemp = masterTCP.execute(device['id'], cst.READ_HOLDING_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = struct.unpack('f', struct.pack('I', (resultadoTemp[1]<<16)|resultadoTemp[0]))[0]
                                elif device['function'] == 4:
                                    if parameters[parameter][2] == 1:
                                        resultado = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>f')
                                    elif parameters[parameter][2] == 2:
                                        resultado = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>l')
                                    elif parameters[parameter][2] == 3:
                                        resultado = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                    elif parameters[parameter][2] == 4:
                                        resultadoTemp = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = (resultadoTemp[1]<<16)|resultadoTemp[0]
                                    elif parameters[parameter][2] == 5:
                                        resultado = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>I')
                                    elif parameters[parameter][2] == 6:
                                        resultado = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1], data_format='>L')
                                    elif parameters[parameter][2] == 7:
                                        resultadoTemp = masterTCP.execute(device['id'], cst.READ_INPUT_REGISTERS, parameters[parameter][0], parameters[parameter][1])
                                        resultado = [0,0]
                                        resultado[0] = struct.unpack('f', struct.pack('I', (resultadoTemp[1]<<16)|resultadoTemp[0]))[0]
                                datas[list][parameter] = resultado[0]
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

                    datas[list]['ReadTime'] =  time.time() - start_time

            except modbus_tk.modbus.ModbusError as exc:
                log.error("%s- Code=%d", exc, exc.get_exception_code())

        json_body = [
            {
                'measurement': 'ModbusLog',
                'tags': {
                    'id': device_slave_id[device_id],
                    'device': device_id_name[device_id],
                },
                'time': t_str,
                'fields': datas[device_id]
            }
            for device_id in datas
        ]
        if len(json_body) > 0:

#            log.debug(json_body)

            list = 0

            for influx_config in influxdb:
                list = list + 1
                if self.influx_inteval_save[list] > 0:
                    if self.influx_inteval_save[list] <= 1:
                        self.influx_inteval_save[list] = influx_config['interval']

                        DBclient = InfluxDBClient(influx_config['host'],
                                                influx_config['port'],
                                                influx_config['user'],
                                                influx_config['password'],
                                                influx_config['dbname'])
                        try:
                            DBclient.write_points(json_body)
                            log.info(t_str + ' Data written for %d meters in {}.' .format(influx_config['name']) % len(json_body) )
                        except Exception as e:
                            log.error('Data not written! in {}' .format(influx_config['name']))
                            log.error(e)
                            raise
                    else:
                        self.influx_inteval_save[list] = self.influx_inteval_save[list] - 1
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
    parser.add_argument('--influxdb', default='influx_config.yml',
                        help='YAML file containing Influx Host, port, user etc. Default "influx_config.yml"')
    parser.add_argument('--log', default='CRITICAL',
                        help='Log levels, DEBUG, INFO, WARNING, ERROR or CRITICAL')
    parser.add_argument('--logfile', default='',
                        help='Specify log file, if not specified the log is streamed to console')
    args = parser.parse_args()
    interval = int(args.interval)
    loglevel = args.log.upper()
    logfile = args.logfile

    # Setup logging
    log = logging.getLogger('modbus-logger')
    log.setLevel(getattr(logging, loglevel))

    if logfile:
        loghandle = logging.FileHandler(logfile, 'w')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        loghandle.setFormatter(formatter)
    else:
        loghandle = logging.StreamHandler()

    log.addHandler(loghandle)

    log.info('Started app')

    collector = DataCollector(influx_yaml=args.influxdb,
                              device_yaml=args.devices)

    repeat(interval,
           max_iter=collector.max_iterations,
           func=lambda: collector.collect_and_store())
