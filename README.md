# Modbus-Logger
Log your modbus-rtu device data on a Raspberry Pi/Orange Pi and plot graphs of your data.
Its been verified to work with a Raspberry Pi with a Linksprite RS485 shield and Orange Pi Zero with USB to RS485 adapter for reading values from ABB ACS310 anda ABB ACS810. By changing the devices.yml file and making a corresponding [model].yml file it should be possible to use other modbus enabled models.

Add support for ModbusTCP and add bridge RTU to TCP vía ESP8266 and multi Influx_DB databases

### Requirements

#### Hardware

* Raspberry Pi 3 / Orange Pi Zero
* [Linksprite RS485 Shield V3 for RPi](http://linksprite.com/wiki/index.php5?title=RS485/GPIO_Shield_for_Raspberry_Pi_V3.0) or a simpe [USB RS485 adapter](https://es.aliexpress.com/item/HOT-SALE-2pcs-lot-USB-to-RS485-485-Converter-Adapter-Support-Win7-XP-Vista-Linux-Mac/1699271296.html)
* Modbus based device.

#### Software

* Rasbian or armbian
* Python 3.4 and PIP3
* PyYAML 5.1 (pip3 install -U PyYAML if installed)
* [modbus_tk](https://github.com/ljean/modbus-tk)
* [InfluxDB](https://docs.influxdata.com/influxdb/v1.3/)
* [Grafana](http://docs.grafana.org/)

### Prerequisite

### Installation
#### Install InfluxDB*

##### Step-by-step instructions
* Add the InfluxData repository
    ```sh
    $ wget -q https://repos.influxdata.com/influxdata-archive_compat.key
    $ echo '393e8779c89ac8d958f81f942f9ad7fb82a25e133faddaf92e15b16e6ac9ce4c influxdata-archive_compat.key' | sha256sum -c && cat influxdata-archive_compat.key | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg > /dev/null
    $ echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive_compat.gpg] https://repos.influxdata.com/debian stable main' | sudo tee /etc/apt/sources.list.d/influxdata.list
    ```
* Download and install
    ```sh
    $ sudo apt-get update && sudo apt-get install influxdb2
    ```
* Start the influxdb service
    ```sh
    $ sudo systemctl start influxdb
    ```
* Create the database (databases are named buckets in influxdb2)
    ```sh
    $  influx bucket create -n db_modbus --org myorg
    ```
    or user webui at `http://localhost:8086`
* Create a token
    ```sh
    $ influx auth create -o myorg --all-access
    ```
    or user webui at `http://localhost:8086`

[*source](https://docs.influxdata.com/influxdb/v1.8/introduction/installation/)

#### Install Grafana*

##### Step-by-step instructions
* Add APT Repository
    ```sh
    $ echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
    ```
* Add Bintray key
    ```sh
    $ curl https://packages.grafana.com/gpg.key | sudo apt-key add -
    ```
* Now install
    ```sh
    $ sudo apt-get update && sudo apt-get install grafana
    ```
* Start the service using systemd:
    ```sh
    $ sudo systemctl daemon-reload
    $ sudo systemctl start grafana-server
    $ systemctl status grafana-server
    ```
* Enable the systemd service so that Grafana starts at boot.
    ```sh
    $ sudo systemctl enable grafana-server.service
    ```
* Go to http://localhost:3000 and login using admin / admin (remember to change password)
[*source](http://docs.grafana.org/installation/debian/)

#### Install Modbus Logger:
* Download and install from Github and install pip3
    ```sh
    $ git clone https://github.com/GuillermoElectrico/modbus-logger.git
	$ sudo apt-get install python3-pip
    ```
* Run setup script (must be executed as root (sudo) if the application needs to be started from rc.local, see below)
    ```sh
    $ cd modbus-logger
    $ sudo python3 setup.py install
    ```    
* Make script file executable
    ```sh
    $ chmod 777 read_modbus_device.py
    ```
* Edit devices.yml to match your configuration
* Test the configuration by running:
    ```sh
    ./read_modbus_device.py
    ./read_modbus_device.py --help # Shows you all available parameters
    ```
* To run the python script at system startup. Add to following lines to the end of /etc/rc.local but before exit:
    ```sh
    # Start Modbus-Logger
    /home/pi/Modbus-Logger/read_modbus_device.py --interval 60 > /var/log/modbus-logger.log &
    ```
    Log with potential errors are found in /var/log/modbus-logger.log
