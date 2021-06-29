# RTL-SDR-P2000Receiver-HA
Receiving P2000 messages using RTL-SDR stick and post them to Home Assistant.

Read the Credits section below.

## Features

- Standalone P2000 messages receiver using a local RTL-SDR compatible receiver
- Linux based only
- Post P2000 message information to a Home Assistant sensor using the REST API (no need to install something on HA side)
- Capcodes database (text based for now), see 'db_capcodes.txt'
- Optional text match filter (white-list), see 'match_text.txt'
- Capcode ignore filter (black-list), see 'ignore_capcodes.txt'


## Screenshots

![View](/screenshots/p2000_sensor.png)

![View](/screenshots/cli_output.png)

## Installation

### 0) Install required build tools and libraries (tested on Debian 10)

```
sudo apt-get install build-essential cmake unzip pkg-config libusb-1.0-0-dev git qt4-qmake libpulse-dev libx11-dev qt4-default
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

Insert your dongle and test the rtl-sdr functionality like so:
```
$ rtl_test 
Found 1 device(s):
  0:  Realtek, RTL2838UHIDIR, SN: 00000001

Using device 0: Generic RTL2832U OEM
Detached kernel driver
Found Rafael Micro R820T tuner
Supported gain values (29): 0.0 0.9 1.4 2.7 3.7 7.7 8.7 12.5 14.4 15.7 16.6 19.7 20.7 22.9 25.4 28.0 29.7 32.8 33.8 36.4 37.2 38.6 40.2 42.1 43.4 43.9 44.5 48.0 49.6 
[R82XX] PLL not locked!
Sampling at 2048000 S/s.

Info: This tool will continuously read from the device, and report if
samples get lost. If you observe no further output, everything is fine.

Reading samples in async mode...
lost at least 1460 bytes
lost at least 1600 bytes
lost at least 1336 bytes
lost at least 908 bytes
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

qmake ../multimon-ng.pro
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


### 3) Install this RTL-SDR-P2000Receiver-HA software

```
cd
git clone https://github.com/cyberjunky/RTL-SDR-P2000Receiver-HA.git

cd RTL-SDR-P2000Receiver-HA
./p2000.py
```

See the Configuration section for more information


After successful configuraton and testing by running it manually you may add it to the startup script
```
sudo nano /etc/rc.local
python3 /home/<YOUR USER>/RTL-SDR-P2000Receiver-HA/p2000.py &
```

Python packages, the needed packages are installed by default on Debian 10.
If you get errors about missing packages when starting the software, you may need to install them for your distro.


### 4) Cleanup build environments (optional)

```
cd
sudo rm -r rtl-sdr multimon-ng
```

### 5) Tools (optional)

I have created some tools to download and/or convert or extract data from.
You can find them in the tools directory, you must run them from there.

*gen_db_capcodes.py*

Downloads capcodes file from http://p2000.bommel.net/cap2csv.php
And created the db_capcodes.txt file from it.
Different delimiter, lowercase header names, fill capcodes with zero's to 9 char lenght.
Format: capcode,discipline,region,location,description,remark

*gen_db_plaatsnamen.py*

Downloads Afkortingen_Plaatsnamen sheet from Google Docs file https://www.tomzulu10capcodes.nl/
And extracts the plaatsnamen from it to create db_plaatsnamen.txt.
It's used to check for valid plaatsnamen.
Format: plaatsnaam

*gen_db_pltsnmn.py*

Downloads Afkortingen_Plaatsnamen sheet from google Docs file https://www.tomzulu10capcodes.nl/
And creates the db_pltsnmn.txt file from it.
And extracts the pltsnmn and plaatsnamen from it to create db_pltsnmn.txt.
It's used to look up plaatsnamen by there short name and convert them.
Format: pltsnmn,plaatsnaam

*gen_match_regions.py*

Extract all regions from db_capcodes.txt and create match_regions.txt.
Format: regio

This file is not used yet, but will be a filter later.

*gen_match_disciplines.py*

Extract all disciplines from db_capcodes.txt and create match_disciplines.txt
Format: disciplines

This file is not used yet, but will be a filter later.


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

[rtl-sdr]
cmd = rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -

[home-assistant]
baseurl = http://192.168.2.123:8123
token = Place Your Long-Lived Access Token Here
sensorname = P2000
```

Enter the local url to your Home Assistant instance including port http://IP-ADDRESS:8123
Goto your user profile menu in Home Assistant lovelace GUI, and create a Long-Lived Access Token.
Name it P2000Receiver and copy and paste this token to the config.ini file.
Change default sensor name 'P2000' if you want too.

Mine works with default settings (with -g and -p), with them I get no output.

You maybe need to add the gain or correction parameters, depending on the dongle you have.
-g = 'gain' - a number between 0-50
-p = 'correction' - specific ppm deviation
-d = 'device id' - if you have more than one dongle

For example:
```
cmd = rtl_fm -f 169.65M -M fm -s 22050 -g 20 -p 0 | multimon-ng -a FLEX -t raw -
```

U can test this by running the command line from the shell, see RTL-SDR dongle section above.
You should see the FLEX messages appear after some seconds.


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

### Capcodes, Disciplines, Regions etc.

http://p2000.bommel.net


### Plaatsnamen & Pltsnmn

https://www.tomzulu10capcodes.nl/


## Development state

NOTE: We only support one sensor for now.
Some filter functionalty (e.g. disciplinces, regions) is not implemented yet.

Unless you fill match_filter.txtr you will receive all P2000 messages!

Could be that we re-add websocket functionality, and create a matching Home Assistant custom integration.

There is a chance we make other big breaking changes.

Focus of development is now on getting as much as data from the FLEX messages as possible.

Adding GPS location lat/long, from Cloud service or database

Replace text files with a database (MongoDB/sSQLite?)


## Debugging

Set debug = True in config.ini file to get all debbugging info when running.
