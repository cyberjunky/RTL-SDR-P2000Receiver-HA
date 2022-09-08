# RTL-SDR-P2000Receiver-HA
Receiving P2000 messages using RTL-SDR stick and post them to Home Assistant and/or MQTT.

Read the Credits section below.

## Features

- Standalone P2000 messages receiver using a local RTL-SDR compatible receiver
- Linux based only
- Post P2000 message information to a Home Assistant sensor using the REST API (no need to install something on HA side)
- Post P2000 message information to an MQTT topic
- Capcodes database (text based for now), see 'db_capcodes.txt'
- Optional text match filter (white-list), see 'match_text.txt'
- Capcode ignore filter (black-list), see 'ignore_capcodes.txt'
- Get GPS latitude/longitude for addresses using OpenCage service


## Screenshots

![View](/screenshots/p2000_sensor.png)

![View](/screenshots/cli_output.png)

## Installation

Preparing a Raspberry Pi:

Download and install Raspbian software on an SD card using Raspberry Imager from
https://www.raspberrypi.com/software/
Choose Raspberry Pi OS Other and then Raspberry Pi OS Lite (32-bit)

Insert the SD card, connect the display and keyboard and boot the Raspberry Pi.
Default login pi/raspberry

NOTE: Use a good quality SD card otherwise it will wear out soon (also make backups of your config)

```
sudo raspi-config
```
Select Interface options and then P2 SSH to enable SSH
Back Finish
Set your own password for user ‘pi’
```
passwd
```
Gather assigned IP address to login with SSH
```
ip addr
```
Look for `eth0` when connected wired
If you want to use Wi-Fi use raspi-config to set country and Wi-Fi credentials using System
Options, S1 Wireless LAN
Fix timezone settings if time is incorrect:
```
sudo dpkg-reconfigure tzdata
```
Login and update software:
```
sudo apt update
sudo apt upgrade
sudo reboot
```

### 0) Install required build tools and libraries (tested on Debian and Raspbian 11)

```
sudo apt-get install build-essential cmake unzip pkg-config libusb-1.0-0-dev git qt5-qmake \
libpulse-dev libx11-dev python3-pip
```

### 1) Install RTL-SDR software

Download and build the software:
```
cd
git clone git://git.osmocom.org/rtl-sdr.git
cd rtl-sdr

mkdir build;cd build

cmake ../ -DINSTALL_UDEV_RULES=ON -DDETACH_KERNEL_DRIVER=ON
make
sudo make install
sudo ldconfig
```

To be able to communicate with the dongle as a non-root user install and activate the udev rules
```
sudo cp ../rtl-sdr.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
```
Then remove and insert the RTL-SDR dongle.

Test the rtl-sdr functionality like so:
```
$ rtl_test
Found 1 device(s):
0: Realtek, RTL2838UHIDIR, SN: 00000001
Using device 0: Generic RTL2832U OEM
Detached kernel driver
Found Rafael Micro R820T tuner
Supported gain values (29): 0.0 0.9 1.4 2.7 3.7 7.7 8.7 12.5 14.4 15.7 16.6 19.7 20.7 22.9
25.4 28.0 29.7 32.8 33.8 36.4 37.2 38.6 40.2 42.1 43.4 43.9 44.5 48.0 49.6
[R82XX] PLL not locked!
Sampling at 2048000 S/s.
Info: This tool will continuously read from the device, and report if
samples get lost. If you observe no further output, everything is fine.
Reading samples in async mode...
...
[Ctrl-C]
```


### 2) Install multimon-ng software

Download and build the software:
```
cd
git clone https://github.com/Zanoroy/multimon-ng.git
cd multimon-ng

mkdir build;cd build

qmake -qt=qt5 ../multimon-ng.pro
make
sudo make install
```
The multimon-ng command should work after this install.
```
$ multimon-ng -h
multimon-ng 1.1.8
  (C) 1996/1997 by Tom Sailer HB9JNX/AE4WA
  (C) 2012-2019 by Elias Oenal
Available demodulators: POCSAG512 POCSAG1200 POCSAG2400 FLEX EAS UFSK1200 CLIPFSK FMSFSK AFSK1200 AFSK2400 AFSK2400_2 AFSK2400_3 HAPN4800 FSK9600 DTMF ZVEI1 ZVEI2 ZVEI3 DZVEI PZVEI EEA EIA CCIR MORSE_CW DUMPCSV X10 SCOPE

Usage: multimon-ng [file] [file] [file] ...
  If no [file] is given, input will be read from your default sound
  hardware. A filename of "-" denotes standard input.
  -t <type>  : Input file type (any other type than raw requires sox)
  -a <demod> : Add demodulator
  -s <demod> : Subtract demodulator
  -c         : Remove all demodulators (must be added with -a <demod>)
  -q         : Quiet
  -v <level> : Level of verbosity (e.g. '-v 3')
               For POCSAG and MORSE_CW '-v1' prints decoding statistics.
  -h         : This help
  -A         : APRS mode (TNC2 text output)
  -m         : Mute SoX warnings
  -r         : Call SoX in repeatable mode (e.g. fixed random seed for dithering)
  -n         : Don't flush stdout, increases performance.
  -j         : FMS: Just output hex data and CRC, no parsing.
  -e         : POCSAG: Hide empty messages.
  -u         : POCSAG: Heuristically prune unlikely decodes.
  -i         : POCSAG: Inverts the input samples. Try this if decoding fails.
  -p         : POCSAG: Show partially received messages.
  -f <mode>  : POCSAG: Overrides standards and forces decoding of data as <mode>
                       (<mode> can be 'numeric', 'alpha', 'skyper' or 'auto')
  -b <level> : POCSAG: BCH bit error correction level. Set 0 to disable, default is 2.
                       Lower levels increase performance and lower false positives.
  -C <cs>    : POCSAG: Set Charset.
  -o         : CW: Set threshold for dit detection (default: 500)
  -d         : CW: Dit length in ms (default: 50)
  -g         : CW: Gap length in ms (default: 50)
  -x         : CW: Disable auto threshold detection
  -y         : CW: Disable auto timing detection
  --timestamp: Add a time stamp in front of every printed line
  --label    : Add a label to the front of every printed line
   Raw input requires one channel, 16 bit, signed integer (platform-native)
   samples at the demodulator's input sampling rate, which is
   usually 22050 Hz. Raw input is assumed and required if piped input is used.
```


### 3) Install Python3 package dependencies

Most of the needed packages are installed by default on Debian 11. If you get errors about
missing packages when starting the software, you may need to install them for your distro.
Install these packages to support MQTT and opencage:
```
sudo pip3 install paho.mqtt
sudo pip3 install opencage
sudo pip3 install geopy
```

### 4) Install RTL-SDR-P2000Receiver-HA software

```
cd
git clone https://github.com/cyberjunky/RTL-SDR-P2000Receiver-HA.git

cd RTL-SDR-P2000Receiver-HA
./p2000.py
RTL-SDR P2000 Receiver for Home Assistant Version 0.0.6
Checking if required software is installed
rtl_fm is found
multimon-ng is found
Created config file 'config.ini', edit it and restart the program.
```

See the Configuration section for more information


After successful configuraton and testing by running it manually you have two options to start it automatically:

#### a) Add it to the debian rc.local startup script 
```
sudo nano /etc/rc.local

# Insert this just above the exit 0 line
su - pi -c /home/pi/RTL-SDR-P2000Receiver-HA/p2000.py > /dev/null 2>&1 &

```

#### b) Edit and use supplied systemd config
```
sudo nano rtlsdrp2000.service

# If needed change these lines to match the location of the software on your system:

StandardOutput=file:/home/pi/RTL-SDR-P2000Receiver-HA/rtlsdrp2000.log
StandardError=file:/home/pi/RTL-SDR-P2000Receiver-HA/rtlsdrp2000.log
ExecStart=/usr/bin/python3 /home/pi/RTL-SDR-P2000Receiver-HA/p2000.py

sudo cp rtlsdrp2000.service /etc/systemd/system
sudo systemctl enable rtlsdrp2000
sudo systemctl start rtlsdrp2000
```


### 5) Cleanup build environments (optional)

```
cd
sudo rm -r rtl-sdr multimon-ng
```

### 6) Quick setup RTL-SDR-P2000Receiver-HA

Fill in the generated `config.ini ` (after the first run of p2000.py)
Set `debug = True` to see what's happening to check your configuration, disable if all is
working to save writes to SD card.
home-assistant section:
enabled = True
baseurl = the IP address or url of your Home-Assistant instance including port.
token = A long lived token generated inside Home-Assistant
If you want to use geocoding set opencage
opencage section:
enabled = True
token = Your opencage tokenUpdate all database files:
```
update_db.py
```
Run p2000.py
Check Home Assistant sensor after first message trigger
Filtering
I use match_text.txt to match all my plaatsnamen:
```
# Only pass messages when filter matches, format: one string per line, * and ? masks are
allowed.
# When empty or all entries are commented with # all messages pass
*Dordrecht*
*DORDRT*
*Zwijndrecht*
*ZWIJND*
*Sliedrecht*
*SLIEDR*
```
And ignore_text.txt to ignore unwanted stuff:
```
# Ignore messages when filter matches, format: one string per line, * and ? masks are
allowed.
# When empty or all commented with # all messages pass
*Test*
*test*
*TEST*
```
NOTE: All tools makes backups of current files inside the 'convert' directory with timestamps appended to filename.
This is also the location the temp data is downloaded to.


## RTL-SDR dongle

![View](/screenshots/dongle.jpg)

I tested the software with:
*RTL-SDR / FM+DAB / DVB-T USB 2.0 Mini Digital TV Stick DVBT Dongle SDR*

The software searches for device 0 by default, see Configuration section for more details.

Sample output:
```
$ rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -
Found 1 device(s):
  0:  Realtek, RTL2838UHIDIR, SN: 00000001

multimon-ng 1.1.8
  (C) 1996/1997 by Tom Sailer HB9JNX/AE4WA
  (C) 2012-2019 by Elias Oenal
Available demodulators: POCSAG512 POCSAG1200 POCSAG2400 FLEX EAS UFSK1200 CLIPFSK FMSFSK AFSK1200 AFSK2400 AFSK2400_2 AFSK2400_3 HAPN4800 FSK9600 DTMF ZVEI1 ZVEI2 ZVEI3 DZVEI PZVEI EEA EIA CCIR MORSE_CW DUMPCSV X10 SCOPE
Enabled demodulators: FLEX
Using device 0: Generic RTL2832U OEM
Found Rafael Micro R820T tuner
Tuner gain set to automatic.
Tuned to 169903575 Hz.
Oversampling input by: 46x.
Oversampling output by: 1x.
Buffer size: 8.08ms
Exact sample rate is: 1014300.020041 Hz
Allocating 15 zero-copy buffers
Sampling at 1014300 S/s.
Output at 22050 Hz.
FLEX|2021-06-28 16:50:07|1600/2/K/A|12.077|001180000|ALN|TESTOPROEP HOOFDSYSTEEM MKOB DEN BOSCH
FLEX|2021-06-28 16:50:35|1600/2/K/A|12.092|002029568 000126999 000126164|ALN|A2 (dia: ja) 12164 Rit 79824 Hotel Herbergh Amsterdam Airport Sloterweg Badhoevedorp
...

```

## Configuration

Start the program for the first time to create a default config.ini file.

```
$ ./p2000.sh
RTL-SDR P2000 Receiver for Home Assistant Version 0.0.1

Checking if required software is installed
rtl_fm is found
multimon-ng is found
Created config file 'config.ini', edit it and restart the program.
```

Then edit the file config.ini:
```
[main]
debug = False
logtofile = True

[rtl-sdr]
cmd = rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -

[home-assistant]
enabled = True
baseurl = http://homeassistant.local:8123
token = Place your Long-Lived Access Token here
sensorname = P2000

[mqtt]
enabled = False
mqtt_server = 192.168.1.100
mqtt_port = 1883
mqtt_user = mqttuser
mqtt_password = somepassword
mqtt_topic = p2000

[opencage]
enabled = False
token = Place your OpenCage API Token here

[sensor_p2000_radius]
friendlyname = P2000 1km from GPS
zone_latitude = 52.37602835336776
zone_longitude = 4.902929475786443
zone_radius = 1

[sensor_p2000_keyword]
friendlyname = P2000 keyword
searchkeyword = *GRIP*,*Grip*,*grip*

[sensor_p2000_capcode]
friendlyname = P2000 capcodes Lifeliners
searchcapcode = *000120901*,*000726001*,*000923993*

[sensor_p2000_region]
friendlyname = P2000 Region Amsterdam-Amstelland and Utrecht
searchregion = Amsterdam-Amstelland,Flevoland

[sensor_p2000_discipline_]
friendlyname = P2000 Brandweer
searchdiscipline = Brandweer

```
*main - debug*

Set to True to get debugging output.

*main - logtofile*

Set to True to create daily logfiles from all send and ignored messages

*rtl-sdr - cmd*

My dongle works with these default settings (without -g and -p), with them I get no output.

You may need to add these gain or correction parameters:
-g = 'gain' - a number between 0-50
-p = 'correction' - specific ppm deviation
-d = 'device id' - if you have more than one dongle

For example:
```
cmd = rtl_fm -f 169.65M -M fm -s 22050 -g 20 -p 0 | multimon-ng -a FLEX -t raw -
```
U can test this by running the command line from the shell, see RTL-SDR dongle section above.
You should see the FLEX messages appear after some seconds.

*home-assistant - enabled*

True to post data to HA, False to disable

*home-assistant - baseurl*

Enter the url to your local Home Assistant instance including port.

*home-assistant - token*

Goto your user profile menu in Home Assistant lovelace GUI, and create a so called 'Long-Lived Access Token'.
Name it 'P2000Receiver' for example and copy and paste this token here in the config.ini file.

*mqtt - enabled*

True to post data to MQTT, False to disable

*mqtt - mqtt_server*
*mqtt - mqtt_port*
*mqtt - mqtt_user*
*mqtt - mqtt_password*
*mqtt - mqtt_topic*

MQTT server address, port, user credentials to connect with and topic to post to

*opencage - enabled*

True to fetch latitude/longitude for address

*opencage - token*

To use OpenCage support you need to create a (free max 2500 request per day, 1 per second) account at https://opencagedata.com
Then fill in your API key here

*sensor_p2000_radius*

Sensor naming in Home-Assistant, you may name the sensor as you want, but it has to start with "sensor_" 

*friendlyname*

This is the displayname from the sensor in Home-Assistant, change to whatever you find suitable

*zone_latitude*
*zone_longitude*
*zone_radius*

These three values are mandatory for a GPS based sensor, zone_radius is defined in KM

*searchkeyword*

Keywords for the sensor, comma separated and with use of wildcards

*searchregion*

Regions as criteria for a sensor, values are case-sensitive and can be comma separated 

*searchcapcode*
Capcodes for the sensor, comma separated and with use of wildcards

*searchdiscipline*
Disciplines for the sensor, comma separated and with use of wildcards

## Filtering

There is basic filtering implemented (this can be changed during development)

The following files are used:

ignore_text.txt
ignore_capcodes.txt

A specific type of filtering is ignored if the file is empty or only has commented lines in it. (lines with leading #)

The syntax for *match_text.txt* and *ignore_text.txt* is using fnmatch.

https://docs.python.org/3/library/fnmatch.html

So entries need to match whole message exactly, or use wildcards to match parts of it.



This is the order in which the filters are processed:

![View](/screenshots/filters.png)
 
## Automation
You can get message events on your mobile device(s) by using a notify event, for example like this:
```
automation:
  - alias: "Melding P2000 Bericht"
    trigger:
      platform: state
      entity_id: sensor.p2000
    action:
      service: notify.telegram
      data_template:
        message: >
          {{ states.sensor.p2000.state + "\n" + states.sensor.p2000.attributes.disciplines }}
```

If you want an OpenStreetMap link included (if GPS location was found using OpenCage):
```
automation:
  - alias: "Melding P2000 Bericht"
    trigger:
      platform: state
      entity_id: sensor.p2000
    action:
      service: notify.telegram
      data_template:
        message: >
          {{ states.sensor.p2000.state + "\n" + states.sensor.p2000.attributes.disciplines + "\n" + states.sensor.p2000.attributes.mapurl }}
```

If you want to use native Telegram location support (if GPS location was found using OpenCage):
```
automation:
  - alias: "Melding P2000 Bericht"
    trigger:
      platform: state
      entity_id: sensor.p2000
    action:
      service: notify.telegram
      data_template:
        message: >
          {{ states.sensor.p2000.state + "\n" + states.sensor.p2000.attributes.disciplines }}
      - condition: or
        conditions: "{{ states.sensor.p2000.attributes.latitude|float > 0 }}"
      - service: script.notify_telegram_location

script:
  notify_telegram_location:
    alias: Test notify.telegram location template
    sequence:
      - service: notify.telegram
        data:
          message: "Not used here but needed..."
          data:
            location:
              latitude: "{{ states.sensor.p2000.attributes.latitude|float }}"
              longitude: "{{ states.sensor.p2000.attributes.longitude|float }}"
```


## Troubleshooting

If you have issues with the dongle not being recognized try this:
```
sudo nano /etc/modprobe.d/raspi-blacklist.conf

blacklist dvb_usb_rtl28xxu
blacklist rtl2832
blacklist rtl2830
```

If you don't get any output from the script, no messages try this:

Run this command to see if you get output lines:
```
rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -
```
If not try ti place the antenna near the window/outside.

If you get output from this command, maybe the filters are too strict/wrong.
Create an empty match_text.txt file

## Credits

### RPi-P2000Receiver

My project is based on https://github.com/dmitryelj/RPi-P2000Receiver written by https://github.com/dmitryelj, thanks for the inspiration!

I rewrote it heavily though, left out all unneeded code for my specific purpose, and added some functionality:
- Removed websocket code
- Removed httpserver code
- Removed POCSAG code
- Removed all RPi specific code and functionality (e.g. LCD, Reboot. Power, CPU)
- Make it more Linux distro independent
- Removed Windows specific code
- Added config file support, see config.ini (run program ones to create it)
- Added P2000 address extract/guess code
- Added support for city database, see db_plaatsnamen.txt
- Added support for finding and translating city shortnames, see db_pltsnmn.txt
- Rewrote 3rd party post to server code to post to Home Assistant REST API
- Created class based code instead of monolith using globals
- Renamed files to see which are filters and which are databases
- Added tools to create these files, find them under 'tools'
- Pylint, flake8, black, isort checked code, some rewriting todo to get pylint 10 score.

- https://github.com/bduijnhouwer for MQTT support
- https://github.com/Dinges28 for OpenCage geolocation support

### Capcodes, Disciplines, Regions etc.

http://p2000.bommel.net

https://www.tomzulu10capcodes.nl/

### Plaatsnamen & Pltsnmn

https://www.tomzulu10capcodes.nl/

## Development state

NOTE: We only support one sensor for now.
Some filter functionalty (e.g. disciplinces, regions) is not implemented yet.

Unless you fill match_filter.txt you will receive all P2000 messages!

Could be that we re-add websocket functionality, and create a matching Home Assistant custom integration.

There is a chance we make other big breaking changes.

Focus of development is now on getting as much as data from the FLEX messages as possible.

Replace text files with a database (MongoDB/SQLite?)


## Debugging

Set debug = True in config.ini file to get all debbugging info when running.
