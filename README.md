# Modbus-Logger
Log your modbus-rtu device data on a Raspberry Pi/Orange Pi and plot graphs of your data.
Its been verified to work with a Raspberry Pi with a Linksprite RS485 shield and Orange Pi Zero with USB to RS485 adapter for reading values from ABB ACS310 anda ABB ACS810. By changing the devices.yml file and making a corresponding [model].yml file it should be possible to use other modbus enabled models.

### Requirements

#### Hardware

* Raspberry Pi 3 / Orange Pi Zero
* [Linksprite RS485 Shield V3 for RPi](http://linksprite.com/wiki/index.php5?title=RS485/GPIO_Shield_for_Raspberry_Pi_V3.0) or a simpe [USB RS485 adapter](https://es.aliexpress.com/item/HOT-SALE-2pcs-lot-USB-to-RS485-485-Converter-Adapter-Support-Win7-XP-Vista-Linux-Mac/1699271296.html)
* Modbus based device.

#### Software

* Rasbian or armbian
* Python 3.4 and PIP3
* [modbus_tk](https://github.com/ljean/modbus-tk)
* [InfluxDB](https://docs.influxdata.com/influxdb/v1.3/)
* [Grafana](http://docs.grafana.org/)

### Prerequisite

### Installation
#### Install InfluxDB*

##### Step-by-step instructions
* Add the InfluxData repository
    ```sh
    $ curl -sL https://repos.influxdata.com/influxdb.key | sudo apt-key add -
    $ source /etc/os-release
    $ test $VERSION_ID = "9" && echo "deb https://repos.influxdata.com/debian stretch stable" | sudo tee /etc/apt/sources.list.d/influxdb.list
    ```
* Download and install
    ```sh
    $ sudo apt-get update && sudo apt-get install influxdb
    ```
* Start the influxdb service
    ```sh
    $ sudo service influxdb start
    ```
* Create the database
    ```sh
    $ influx
    CREATE DATABASE db_modbus
    exit 
    ```
[*source](https://docs.influxdata.com/influxdb/v1.3/introduction/installation/)

#### Install Grafana*

##### Step-by-step instructions
* Add APT Repository
    ```sh
    $ echo "deb https://dl.bintray.com/fg2it/deb-rpi-1b jessie main" | sudo tee -a /etc/apt/sources.list.d/grafana.list
    ```
* Add Bintray key
    ```sh
    $ curl https://bintray.com/user/downloadSubjectPublicKey?username=bintray | sudo apt-key add -
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
* Edit meters.yml to match your configuration
* Test the configuration by running:
    ```sh
    ./read_modbus_device.py
    ./read_modbus_device.py --help # Shows you all available parameters
    ```
* To run the python script at system startup. Add to following lines to the end of /etc/rc.local but before exit:
    ```sh
    # Start Energy Meter Logger
    /home/pi/energy-meter-logger/read_modbus_device.py --interval 60 > /var/log/modbus-logger.log &
    ```
    Log with potential errors are found in /var/log/modbus-logger.log
