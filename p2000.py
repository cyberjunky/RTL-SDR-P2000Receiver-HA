#!/usr/bin/env python3
"""RTL-SDR P2000 Receiver for Home Assistant."""

# See README for installation instructions
import calendar
import configparser
import fnmatch
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from opencage.geocoder import OpenCageGeocode
import paho.mqtt.client as mqtt
import requests

VERSION = "0.0.3"

class MessageItem:
    """Contains all the Message data."""

    def __init__(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.message_raw = ""
        self.timestamp = ""
        self.timereceived = time.monotonic()
        self.groupid = ""
        self.receivers = ""
        self.capcodes = []
        self.body = ""
        self.location = ""
        self.postcode = ""
        self.city = ""
        self.address = ""
        self.street = ""
        self.region = ""
        self.priority = 0
        self.disciplines = ""
        self.remarks = ""
        self.longitude = ""
        self.latitude = ""
        self.is_posted = False


def load_config():
    """Create default or load existing config file."""
    config = configparser.ConfigParser()
    if config.read("config.ini"):
        print("Loading configuration from 'config.ini'")
        return config

    config["main"] = {"debug": False}
    config["rtl-sdr"] = {
        "cmd": "rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -"
    }
    config["home-assistant"] = {
        "enabled": True,
        "baseurl": "http://homeassistant.local:8123",
        "token": "Place your Long-Lived Access Token here",
        "sensorname": "p2000",
    }
    config["mqtt"] = {
        "enabled": False,
        "mqtt_server": "192.168.1.100",
        "mqtt_port": 1883,
        "mqtt_user": "mqttuser",
        "mqtt_password": "somepassword",
        "mqtt_topic": "p2000",
    }
    config["opencage"] = {
        "enabled": False,
        "token": "Place your OpenCage API Token here",
    }
    with open("config.ini", "w") as configfile:
        config.write(configfile)
    print("Created config file 'config.ini', edit it and restart the program.")
    sys.exit(0)


def check_requirements():
    """Check if required software is installed."""
    print("Checking if required software is installed")
    # Check if rtl_fm is installed
    process = subprocess.Popen(
        "rtl_fm", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # Wait for the process to finish
    dummy, err = process.communicate()
    error_str = err.decode("utf8")
    if "not found" in error_str or "not recognized" in error_str:
        print("rtl_fm command not found, please install RTL-SDR software")
        return False

    print("rtl_fm is found")

    # Check if multimon-ng is installed
    process = subprocess.Popen(
        "multimon-ng -h", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # Wait for the process to finish
    dummy, err = process.communicate()
    error_str = err.decode("utf8")
    if "not found" in error_str:
        print("multimon-ng not found, please install the multimon-ng package")
        return False

    print("multimon-ng is found")
    return True


def load_capcodes_dict(filename):
    """Load capcodes to dictionary."""
    capcodes = {}
    try:
        print("Loading data from '{}'".format(filename))
        with open(filename, "r") as csv_file:
            csv_list = [
                [val.strip() for val in r.split(",")] for r in csv_file.readlines()
            ]

        (_, *header), *data = csv_list
        for row in data:
            key, *values = row
            capcodes[key] = {key: value for key, value in zip(header, values)}
        print("{} records loaded".format(len(capcodes)))
    except KeyError:
        print(f"Could not parse file contents of: {filename}")
    except OSError:
        print(f"Could not open/read file: {filename}, ignore filter")

    return capcodes


def load_capcodes_filter_dict(filename):
    """Load capcodes ignore or match data to dictionary."""
    capcodes = dict()
    try:
        print("Loading data from '{}'".format(filename))
        with open(filename, "r") as text_file:
            lines = text_file.readlines()
            for item in lines:
                if item[0] == "#":
                    continue

                fields = item.split(",")
                if len(fields) == 2:
                    capcodes[fields[0].strip()] = fields[1].strip()
                elif len(fields) == 1:
                    capcodes[fields[0].strip()] = 'NO DESCR'
        print("{} records loaded".format(len(capcodes)))
        return capcodes
    except KeyError:
        print(f"Could not parse file contents of: {filename}")
    except OSError:
        print(f"Could not open/read file: {filename}, ignore filter")

    return capcodes


def load_list(filename):
    """Load data in list."""
    tmplist = []
    try:
        print("Loading data from '{}'".format(filename))
        with open(filename, "r") as text_file:
            lines = text_file.readlines()
            lines_strip = map((lambda line: line.strip()), lines)
            tmplist = list(
                filter(
                    lambda line: len(line) > 0
                    and line[0:1] != "#"
                    and line[0:1] != ";",
                    lines_strip,
                )
            )
        print("{} records loaded".format(len(tmplist)))
        return tmplist
    except KeyError:
        print(f"Could not parse file contents of: {filename}")
    except OSError:
        print(f"Could not open/read file: {filename}")

    return tmplist


def check_filter(mylist, text):
    """Check filter data."""
    # If list is not loaded or empty allow all
    if len(mylist) == 0:
        return True

    # Check if text applied matches at least one filter
    for f_str in mylist:
        if fnmatch.fnmatch(text, f_str):
            return True

    return False


def to_local_datetime(utc_dt):
    """Convert utc to local time."""
    time_tuple = time.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
    return time.ctime(calendar.timegm(time_tuple))


def p2000_get_prio(message):
    """Look for priority strings and return level."""
    priority = 0

    regex_prio1 = r"^A\s?1|\s?A\s?1|PRIO\s?1|^P\s?1"
    regex_prio2 = r"^A\s?2|\s?A\s?2|PRIO\s?2|^P\s?2"
    regex_prio3 = r"^B\s?1|^B\s?2|^B\s?3|PRIO\s?3|^P\s?3"
    regex_prio4 = r"^PRIO\s?4|^P\s?4"

    if re.search(regex_prio1, message, re.IGNORECASE):
        priority = 1
    elif re.search(regex_prio2, message, re.IGNORECASE):
        priority = 2
    elif re.search(regex_prio3, message, re.IGNORECASE):
        priority = 3
    elif re.search(regex_prio4, message, re.IGNORECASE):
        priority = 4

    return priority


class Main:
    """Main class, start of application."""

    def __init__(self):
        self.running = True
        self.messages = []

        print(f"RTL-SDR P2000 Receiver for Home Assistant Version {VERSION}\n")
        # Set current folder so we can find the config files
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Check if required software is installed
        if not check_requirements():
            print("Application stopped, required software was not found!")
            sys.exit(0)

        # Load configuration
        self.config = load_config()
        self.debug = self.config.getboolean("main", "debug")
        self.rtlfm_cmd = self.config.get("rtl-sdr", "cmd")
        self.use_hass = self.config.getboolean("home-assistant", "enabled")
        self.baseurl = self.config.get("home-assistant", "baseurl")
        self.token = self.config.get("home-assistant", "token")
        self.sensorname = self.config.get("home-assistant", "sensorname")
        self.use_mqtt = self.config.getboolean("mqtt","enabled")
        self.mqtt_server = self.config.get("mqtt","mqtt_server")
        self.mqtt_port = int(self.config.get("mqtt","mqtt_port"))
        self.mqtt_username = self.config.get("mqtt","mqtt_user")
        self.mqtt_password = self.config.get("mqtt","mqtt_password")
        self.mqtt_topic = self.config.get("mqtt","mqtt_topic")
        self.use_opencage = self.config.getboolean("opencage","enabled")
        self.opencagetoken = self.config.get("opencage", "token")

        # Load capcodes data
        self.capcodes = load_capcodes_dict("db_capcodes.txt")

        # Load plaatsnamen data
        self.plaatsnamen = load_list("db_plaatsnamen.txt")

        # Load plaatsnamen afkortingen data
        self.pltsnmn = load_capcodes_dict("db_pltsnmn.txt")

        # Load capcodes ignore data
        self.ignorecapcodes = load_capcodes_filter_dict("ignore_capcodes.txt")

        # Load text ignore data
        self.ignoretext = load_list("ignore_text.txt")

        # Load match text filter data
        self.matchtext = load_list("match_text.txt")

        # Load match capcodes filter data
        self.matchcapcodes = load_capcodes_filter_dict("match_capcodes.txt")

        # Start thread to get data from RTL-SDR stick
        data_thread = threading.Thread(target=self.data_thread_call)
        data_thread.start()

        # Start thread to post messages to Home Assistant
        post_thread = threading.Thread(target=self.post_thread_call)
        post_thread.start()

        # Run the wait loop
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

        # Application is interrupted and is stopping
        self.running = False
        print("Application stopped")

    def post_data(self, msg):
        """Post data to Home Assistant via Rest API and/or MQTT topic."""
        data = {
            "state": msg.body,
            "attributes": {
                "time received": msg.timestamp,
                "group id": msg.groupid,
                "receivers": msg.receivers,
                "capcodes": msg.capcodes,
                "priority": msg.priority,
                "disciplines": msg.disciplines,
                "raw message": msg.message_raw,
                "region": msg.region,
                "location": msg.location,
                "postcode": msg.postcode,
                "city": msg.city,
                "address": msg.address,
                "street": msg.street,
                "remarks": msg.remarks,
                "longitude": msg.longitude,
                "latitude": msg.latitude,
            },
        }

        if self.use_hass:
            try:
                headers = {
                    "Authorization": "Bearer " + self.token,
                    "content-type": "application/json",
                }

                response = requests.post(
                    self.baseurl + "/api/states/sensor." + self.sensorname,
                    headers=headers,
                    data=json.dumps(
                        data, default=lambda o: o.__dict__, sort_keys=True, indent=4
                    ),
                )
                response.raise_for_status()
                if self.debug:
                    print(f"POST data: {data}")
                    print(f"POST status: {response.status_code} {response.reason}")
                    print(f"POST text: {response.text}")
            except requests.HTTPError:
                print(
                    f"HTTP Error while trying to post data, check baseurl and token in config.ini: {response.status_code} {response.reason}"
                )
            except requests.exceptions.SSLError as err:
                print(
                    f"SSL Error occurred while trying to post data, check baseurl in config.ini:\n{err}"
                )
            except requests.exceptions.ConnectionError as err:
                print(
                    f"Connection Error occurred while trying to post data, check baseurl in config.ini:\n{err}"
                )
            finally:
                # Mark as posted to prevent race conditions
                msg.is_posted = True


        if self.use_mqtt:
            try:
                print(f"Posting to MQTT")
 
                data=json.dumps(data)
                client = mqtt.Client()
                client.username_pw_set(self.mqtt_username, self.mqtt_password)
                client.connect(self.mqtt_server,self.mqtt_port,60)
                client.publish(self.mqtt_topic, data)
                client.disconnect()

                if self.debug:
                    print(f"MQTT status: Posting to {self.mqtt_server}:{self.mqtt_port} topic:{self.mqtt_topic}")
                    print(f"MQTT json: {data}")
            finally:
                # Mark as posted to prevent race conditions
                msg.is_posted = True

    def data_thread_call(self):
        """Thread for parsing data from RTL-SDR."""
        print(f"RTL-SDR process started with: {self.rtlfm_cmd}")
        multimon_ng = subprocess.Popen(
            self.rtlfm_cmd, stdout=subprocess.PIPE, shell=True
        )
        try:
            while self.running:
                # Read line from process
                line = multimon_ng.stdout.readline()
                try:
                    line = line.decode("utf8", "backslashreplace")
                except UnicodeDecodeError:
                    if self.debug:
                        print(f"Error while decoding utf8 string: {line}")
                    line = ""
                multimon_ng.poll()
                if line.startswith("FLEX") and line.__contains__("ALN"):
                    line_data = line.split("|")
                    timestamp = line_data[1]
                    groupid = line_data[3].strip()
                    capcodes = line_data[4].strip()
                    message = line_data[6].strip()
                    priority = p2000_get_prio(message)
                    location = ""
                    postcode = ""
                    city = ""
                    address = ""
                    street = ""
                    longitude = ""
                    latitude = ""

                    if self.debug:
                        print(line.strip())

                    # Get address info if any, look for valid postcode and get the two words around them
                    # A2 (DIA: ja) AMBU 17106 Schiedamseweg 3134BA Vlaardingen VLAARD bon 8576
                    regex_address = r"(\w*.) ([1-9][0-9]{3}[a-zA-Z]{2}) (.\w*)"
                    addr = re.search(regex_address, message)
                    if addr:
                        street = addr.group(1)
                        postcode = addr.group(2)
                        city = addr.group(3)
                        address = f"{street} {postcode} {city}"

                    # Try to get city only when there is one after a prio
                    # A1 Breda
                    else:
                        regex_prio_loc = r"(^A\s?1|\s?A\s?2|B\s?1|^B\s?2|^B\s?3|PRIO\s?1|^P\s?1|PRIO\s?2|^P\s?2) (.\w*)"
                        loc = re.search(regex_prio_loc, message)
                        if loc and loc.group(2) in self.plaatsnamen:
                            city = loc.group(2)
                        else:
                            # Find all uppercase words and check if there is a valid city name amoung them
                            # A2 Ambulancepost Moordrecht Middelweg MOORDR V
                            regex_afkortingen = "[A-Z]{2,}"
                            afkortingen = re.findall(regex_afkortingen, message)
                            for afkorting in afkortingen:
                                if afkorting in self.pltsnmn:
                                    city = self.pltsnmn[afkorting]["plaatsnaam"]
                                    
                                    # If uppercase city is found, grab first word before that city name, likely to be the address
                                    regex_address = r"(\w*.) ([A-Z]{2,})(?!.*[A-Z]{2,})"
                                    addr = re.search(regex_address, message)
                                    if addr:
                                        street = addr.group(1)
                                        city = city
                                    address = f"{street} {city}"

                    if not check_filter(self.matchtext, message):
                        if self.debug:
                            print(
                                f"Message '{message}' ignored (didn't match match_text)")
                    else:
                        if check_filter(self.ignoretext, message):
                            if self.debug:
                                print(
                                    f"Message '{message}' ignored (matched ignore_text)")
                        else:
                            # There can be several capcodes in one message
                            ignore = False
                            for capcode in capcodes.split(" "):
                                # Apply filter
                                if not capcode in self.matchcapcodes and self.matchcapcodes:
                                    if self.debug:
                                        print(
                                            f"Message '{message}' ignored (didn't match match_capcodes)"
                                        )
                                    ignore = True
                                    break
                                if capcode in self.ignorecapcodes and self.ignorecapcodes:
                                    if self.debug:
                                        print(
                                            f"Message '{message}' to '{capcode}' ignored (capcode in ignore_capcodes)"
                                        )
                                    ignore = True
                                    break

                            if not ignore:
                                for capcode in capcodes.split(" "):
                                    # Get data from capcode, if exist
                                    if capcode in self.capcodes:
                                        receiver = "{} ({})".format(
                                            self.capcodes[capcode]["description"], capcode
                                        )
                                        discipline = "{} ({})".format(
                                            self.capcodes[capcode]["discipline"], capcode
                                        )
                                        region = self.capcodes[capcode]["region"]
                                        location = self.capcodes[capcode]["location"]
                                        remark = self.capcodes[capcode]["remark"]
                                    else:
                                        receiver = capcode
                                        discipline = ""
                                        region = ""
                                        remark = ""
    
                                    # If this message was already received, only add extra info
                                    if len(self.messages) > 0 and self.messages[0].body == message:
                                        if self.messages[0].receivers == "":
                                            self.messages[0].receivers = receiver
                                        elif receiver:
                                            self.messages[0].receivers += ", " + receiver
    
                                        if self.messages[0].disciplines == "":
                                            self.messages[0].disciplines = discipline
                                        elif discipline:
                                            self.messages[0].disciplines += ", " + discipline
                                        if self.messages[0].remarks == "":
                                            self.messages[0].remarks = remark
                                        elif remark:
                                            self.messages[0].remarks += ", " + remark

                                        self.messages[0].capcodes.append(capcode)
                                        self.messages[0].location = location
                                        self.messages[0].postcode = postcode
                                        self.messages[0].city = city
                                        self.messages[0].street = street
                                        self.messages[0].address = address
                                    else:
                                        # If address is filled and OpenCage is enabled check for GPS coordinates
                                        if address and self.use_opencage:
                                            geocoder = OpenCageGeocode(self.opencagetoken)
                                            gps = geocoder.geocode(address, countrycode='nl')
                                            if gps:
                                                latitude = gps[0]['geometry']['lat']
                                                longitude = gps[0]['geometry']['lng']
                                            else:
                                                latitude = ""
                                                longitude = ""                               
                                            
                                        msg = MessageItem()
                                        msg.groupid = groupid
                                        msg.receivers = receiver
                                        msg.capcodes = [capcode]
                                        msg.body = message
                                        msg.message_raw = line.strip()
                                        msg.disciplines = discipline
                                        msg.priority = priority
                                        msg.region = region
                                        msg.location = location
                                        msg.postcode = postcode
                                        msg.longitude = longitude
                                        msg.latitude = latitude
                                        msg.city = city
                                        msg.street = street
                                        msg.address = address
                                        msg.remarks = remark
                                        msg.timestamp = to_local_datetime(timestamp)
                                        msg.is_posted = False
                                        self.messages.insert(0, msg)

                                # Limit the message list size
                                if len(self.messages) > 100:
                                    self.messages = self.messages[:100]

        except KeyboardInterrupt:
            os.kill(multimon_ng.pid, 9)

        if self.debug:
            print("Data thread stopped")

    # Thread for posting data to Home Assistant
    def post_thread_call(self):
        """Thread for posting data."""
        if self.debug:
            print("Post thread started")
        while True:
            if self.running is False:
                break

            now = time.monotonic()
            for msg in self.messages:
                if msg.is_posted is False and now - msg.timereceived >= 1.0:
                    self.post_data(msg)
            time.sleep(1.0)
        if self.debug:
            print("Post thread stopped")


# Start application
Main()
