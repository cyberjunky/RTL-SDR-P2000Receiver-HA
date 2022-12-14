#!/usr/bin/env python3
"""RTL-SDR P2000 Receiver for Home Assistant."""
import calendar
import configparser
import csv
import fnmatch
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler as _TimedRotatingFileHandler

import geopy.distance
import paho.mqtt.client as mqtt
import requests
from opencage.geocoder import InvalidInputError, OpenCageGeocode, RateLimitExceededError

VERSION = "0.1.1"
CFGFILE = "config.ini"


class TimedRotatingFileHandler(_TimedRotatingFileHandler):
    """Override original code to fix bug with not deleting old logfiles."""

    def __init__(self, filename="", when="midnight", interval=1, backupCount=7):
        super().__init__(
            filename=filename,
            when=when,
            interval=int(interval),
            backupCount=int(backupCount),
        )

    def getFilesToDelete(self):
        """Find all logfiles present."""
        dirname, basename = os.path.split(self.baseFilename)
        filenames = os.listdir(dirname)
        result = []
        prefix = basename + "."
        plen = len(prefix)
        for filename in filenames:
            if filename[:plen] == prefix:
                suffix = filename[plen:]
                if self.extMatch.match(suffix):
                    result.append(os.path.join(dirname, filename))
        result.sort()
        if len(result) < self.backupCount:
            result = []
        else:
            result = result[: len(result) - self.backupCount]
        return result

    def doRollover(self):
        """Delete old logfiles but keep latest backupCount amount."""
        super().doRollover()
        self.close()
        timetuple = time.localtime(time.time())
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timetuple)

        if os.path.exists(dfn):
            os.remove(dfn)

        os.rename(self.baseFilename, dfn)

        if self.backupCount > 0:
            for oldlog in self.getFilesToDelete():
                os.remove(oldlog)

        self.stream = open(self.baseFilename, "w")

        currenttime = int(time.time())
        newrolloverat = self.computeRollover(currenttime)
        while newrolloverat <= currenttime:
            newrolloverat = newrolloverat + self.interval

        self.rolloverAt = newrolloverat


class Logger:
    """Logger class."""

    my_logger = None

    def __init__(self, datadir, logstokeep, debug_enabled):
        """Logger init."""
        self.my_logger = logging.getLogger()
        if debug_enabled:
            self.my_logger.setLevel(logging.DEBUG)
            self.my_logger.propagate = False
        else:
            self.my_logger.setLevel(logging.INFO)
            self.my_logger.propagate = False

        date_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "%(asctime)s - (%(threadName)-10s) - %(filename)s - %(levelname)s - %(message)s",
            date_fmt,
        )
        console_formatter = logging.Formatter(
            "%(asctime)s - (%(threadName)-10s) - %(filename)s - %(levelname)s - %(message)s",
            date_fmt,
        )
        # Create directory if not exists
        if not os.path.exists(f"{datadir}/logs"):
            os.makedirs(f"{datadir}/logs")

        # Log to file and rotate if needed
        file_handle = TimedRotatingFileHandler(
            filename=f"{datadir}/logs/p2000.log", backupCount=logstokeep
        )
        file_handle.setFormatter(formatter)
        self.my_logger.addHandler(file_handle)

        # Log to console
        console_handle = logging.StreamHandler()
        console_handle.setFormatter(console_formatter)
        self.my_logger.addHandler(console_handle)

    def log(self, message, level="info"):
        """Call the log levels."""
        if level == "info":
            self.my_logger.info(message)
        elif level == "warning":
            self.my_logger.warning(message)
        elif level == "error":
            self.my_logger.error(message)
        elif level == "debug":
            self.my_logger.debug(message)

    def info(self, message):
        """Info level."""
        self.log(message, "info")

    def warning(self, message):
        """Warning level."""
        self.log(message, "warning")

    def error(self, message):
        """Error level."""
        self.log(message, "error")

    def debug(self, message):
        """Debug level."""
        self.log(message, "debug")


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
        self.postalcode = ""
        self.city = ""
        self.address = ""
        self.street = ""
        self.region = ""
        self.priority = 0
        self.disciplines = ""
        self.remarks = ""
        self.longitude = ""
        self.latitude = ""
        self.opencage = ""
        self.mapurl = ""
        self.distance = ""
        self.friendly_name = ""


def load_config(filename):
    """Create default or load existing config file."""
    config = configparser.ConfigParser()
    filename = f"{datadir}/{filename}"

    if config.read(filename):

        # Upgrade config if needed
        if config.has_option("home-assistant", "sensorname"):
            config.add_section("sensor_p2000")
            config.set("sensor_p2000", "zone_latitude", "52.37602835336776")
            config.set("sensor_p2000", "zone_longitude", "4.902929475786443")
            config.set("sensor_p2000", "zone_radius", "0")
            config.remove_option("home-assistant", "sensorname")

            with open(filename, "w+") as cfgfile:
                config.write(cfgfile)

        return config

    config["main"] = {"debug": False, "logtofile": False}
    config["rtl-sdr"] = {
        "cmd": "rtl_fm -f 169.65M -M fm -s 22050 | multimon-ng -a FLEX -t raw -"
    }
    config["home-assistant"] = {
        "enabled": True,
        "baseurl": "http://homeassistant.local:8123",
        "token": "Place your Long-Lived Access Token here",
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
    config["sensor_p2000"] = {
        "zone_latitude": "52.37602835336776",
        "zone_longitude": "4.902929475786443",
        "zone_radius": "0",
    }
    with open(filename, "w") as configfile:
        config.write(configfile)

    return False


def check_requirements(self):
    """Check if required software is installed."""
    self.logger.info("Checking if required software is installed")
    # Check if rtl_fm is installed
    process = subprocess.Popen(
        "rtl_fm", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # Wait for the process to finish
    dummy, err = process.communicate()
    error_str = err.decode("utf8")
    if "not found" in error_str or "not recognized" in error_str:
        self.logger.debug("rtl_fm command not found, please install RTL-SDR software")
        return False

    self.logger.debug("rtl_fm is found")

    # Check if multimon-ng is installed
    process = subprocess.Popen(
        "multimon-ng -h", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    # Wait for the process to finish
    dummy, err = process.communicate()
    error_str = err.decode("utf8")
    if "not found" in error_str:
        self.logger.error(
            "multimon-ng not found, please install the multimon-ng package"
        )
        return False

    self.logger.debug("multimon-ng is found")
    return True


def load_capcodes_dict(self, filename):
    """Load capcodes to dictionary."""
    capcodes = {}
    filename = f"{datadir}/{filename}"
    try:
        self.logger.info("Loading data from '{}'".format(filename))
        with open(filename, "r") as csv_file:
            csv_list = [
                [val.strip() for val in r.split(",")] for r in csv_file.readlines()
            ]

        (_, *header), *data = csv_list
        for row in data:
            key, *values = row
            capcodes[key] = {key: value for key, value in zip(header, values)}
        self.logger.info("{} records loaded".format(len(capcodes)))
    except KeyError:
        self.logger.error(f"Could not parse file contents of: {filename}")
    except OSError:
        self.logger.info(f"Could not open/read file: {filename}, ignoring filter")

    return capcodes


def load_capcodes_filter_dict(self, filename):
    """Load capcodes ignore or match data to dictionary."""
    capcodes = dict()
    filename = f"{datadir}/{filename}"
    try:
        self.logger.info("Loading data from '{}'".format(filename))
        with open(filename, "r") as text_file:
            lines = text_file.readlines()
            for item in lines:
                if item[0] == "#":
                    continue

                fields = item.split(",")
                if len(fields) == 2:
                    capcodes[fields[0].strip()] = fields[1].strip()
                elif len(fields) == 1:
                    capcodes[fields[0].strip()] = "NO DESCR"
        self.logger.info("{} records loaded".format(len(capcodes)))
        return capcodes
    except KeyError:
        self.logger.debug(f"Could not parse file contents of: {filename}")
    except OSError:
        self.logger.debug(f"Could not open/read file: {filename}, ignoring filter")

    return capcodes


def load_list(self, filename):
    """Load data in list."""
    tmplist = []
    filename = f"{datadir}/{filename}"
    try:
        self.logger.info("Loading data from '{}'".format(filename))
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
        self.logger.info("{} records loaded".format(len(tmplist)))
        return tmplist
    except KeyError:
        self.logger.debug(f"Could not parse file contents of: {filename}")
    except OSError:
        self.logger.debug(f"Could not open/read file: {filename}")

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


def check_filter_with_list(searchlist, list_to_be_searched):
    # If list is not loaded or empty allow all
    if len(searchlist) == 0:
        return True

    # Check every text in the searchedlist
    for searchedtext in list_to_be_searched:
        if check_filter(searchlist, searchedtext) == True:
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


# Log all messages send or ignored to a logfile in folder logfiles
def log2file(logmessage):
    print("log2file called")
    datestamp = time.strftime("%Y%m%d")
    logfilename = "logfiles/p2000-log-" + datestamp + ".log"
    open(logfilename, "a").write(logmessage)
    open(logfilename, "a").write("\n")
    return


# Set and change to program directory
datadir = os.path.dirname(os.path.realpath(__file__))
os.chdir(datadir)

# Load configuration
config = load_config(CFGFILE)

# Init logging
logger = Logger(datadir, 7, config.getboolean("main", "debug"))


class Main:
    """Main class, start of application."""

    def __init__(self):
        self.running = True
        self.messages = []

        # Init logging
        self.logger = logger
        self.config = config

        if self.config:
            self.logger.info(f"Loading configuration from '{CFGFILE}'")
        else:
            self.logger.info(
                f"Created config file '{CFGFILE}', edit it and restart the program."
            )

        self.debug = self.config.getboolean("main", "debug")
        self.logtofile = self.config.getboolean("main", "logtofile")

        # Set current folder so we can find the config files
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # If log2file is enabled, check if logfiles folder exists
        if self.logtofile:
            if not os.path.exists("logfiles"):
                os.mkdir("logfiles")

        # Check if GPS datafile is available
        if not os.path.isfile("location_gps_database.csv"):
            gps_data_fieldnames = ["address", "latitude", "lontitude", "url"]
            with open("location_gps_database.csv", "w") as outfile:
                writer = csv.DictWriter(
                    outfile,
                    fieldnames=gps_data_fieldnames,
                    delimiter=",",
                    quoting=csv.QUOTE_MINIMAL,
                    lineterminator="\n",
                )
                writer.writeheader()
            outfile.close()

        self.logger.info(f"RTL-SDR P2000 Receiver for Home Assistant Version {VERSION}")
        self.logger.info("Started at %s" % time.strftime("%A %H:%M:%S %d-%m-%Y"))

        # Check if required software is installed
        if not check_requirements(self):
            self.logger.error("Application stopped, required software was not found!")
            sys.exit(0)

        self.rtlfm_cmd = self.config.get("rtl-sdr", "cmd")
        self.use_hass = self.config.getboolean("home-assistant", "enabled")
        self.baseurl = self.config.get("home-assistant", "baseurl")
        self.token = self.config.get("home-assistant", "token")

        self.use_mqtt = self.config.getboolean("mqtt", "enabled")
        self.mqtt_server = self.config.get("mqtt", "mqtt_server")
        self.mqtt_port = int(self.config.get("mqtt", "mqtt_port"))
        self.mqtt_username = self.config.get("mqtt", "mqtt_user")
        self.mqtt_password = self.config.get("mqtt", "mqtt_password")
        self.mqtt_topic = self.config.get("mqtt", "mqtt_topic")
        self.use_opencage = self.config.getboolean("opencage", "enabled")
        self.opencagetoken = self.config.get("opencage", "token")
        self.opencage_disabled = False

        # Load capcodes data
        self.capcodes = load_capcodes_dict(self, "db_capcodes.txt")

        # Load plaatsnamen data
        self.plaatsnamen = load_list(self, "db_plaatsnamen.txt")

        # Load plaatsnamen afkortingen data
        self.pltsnmn = load_capcodes_dict(self, "db_pltsnmn.txt")

        # Load capcodes ignore data
        self.ignorecapcodes = load_capcodes_filter_dict(self, "ignore_capcodes.txt")

        # Load text ignore data
        self.ignoretext = load_list(self, "ignore_text.txt")

        # Load match text filter data
        # self.matchtext = load_list(self, "match_text.txt.example")
        self.matchtext = load_list(self, "match_text.txt")

        # Load match capcodes filter data
        self.matchcapcodes = load_capcodes_filter_dict(self, "match_capcodes.txt")

        # Load GPS database data
        self.gpsdatabase = load_capcodes_dict(self, "location_gps_database.csv")

        # Start thread to get data from RTL-SDR stick
        data_thread = threading.Thread(name="DataThread", target=self.data_thread_call)
        data_thread.start()

        # Start thread to post messages to Home Assistant
        post_thread = threading.Thread(name="PostThread", target=self.post_thread_call)
        post_thread.start()

        # Run the wait loop
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break

        # Application is interrupted and is stopping
        self.running = False
        self.logger.info("Application stopped")

    def post_data(self, msg):
        # Loop through all sensors
        for section in config.sections():
            # Each section is a sensor
            self.radius = ""
            self.sensorname = ""
            self.home_coordinates = ""
            self.friendly_name = ""
            self.searchkeyword = ""
            self.searchcapcode = ""
            self.searchregion = ""
            post = False

            if section.startswith("sensor_"):
                self.sensorname = section.replace("sensor_", "")
                if "zone_radius" in self.config.options(section):
                    self.home_coordinates = (
                        float(self.config.get(section, "zone_latitude")),
                        float(self.config.get(section, "zone_longitude")),
                    )
                    self.radius = self.config.get(section, "zone_radius", fallback="")

                msg.friendly_name = self.config.get(
                    section, "friendlyname", fallback="P2000-SDR"
                )
                self.searchkeyword = self.config.get(
                    section, "searchkeyword", fallback=""
                ).split(",")
                self.searchcapcode = self.config.get(
                    section, "searchcapcode", fallback=""
                ).split(",")
                self.searchregion = self.config.get(
                    section, "searchregion", fallback=""
                ).split(",")
                self.searchdiscipline = self.config.get(
                    section, "searchdiscipline", fallback=""
                ).split(",")

                # If location is known and radius is specified in config calculate distance and check radius
                if msg.latitude and msg.longitude and self.radius:
                    event_coordinates = (msg.latitude, msg.longitude)
                    msg.distance = round(
                        geopy.distance.geodesic(
                            self.home_coordinates, event_coordinates
                        ).km,
                        2,
                    )
                    self.logger.debug(
                        f"Distance from home {msg.distance} km, radius set to {self.radius} km"
                    )
                    if msg.distance > float(self.radius):
                        self.logger.debug(
                            f"Message '{msg.body}' ignored for sensor {self.sensorname} (distance outside radius)"
                        )
                        msg.is_posted = True
                        continue
                    post = True

                # Check for matched text/keyword
                if "searchkeyword" in self.config.options(section):
                    if not check_filter(self.searchkeyword, msg.body):
                        self.logger.debug(
                            f"Message '{msg.body}' ignored for sensor {self.sensorname} (didn't match keyword) - {self.searchkeyword}"
                        )
                        msg.is_posted = True
                        continue
                    self.logger.debug(
                        f"Message '{msg.body}' posted for sensor {self.sensorname} (sensor succesfull match keyword) - {self.searchkeyword}"
                    )
                    post = True

                # Check for matched regions
                if "searchregion" in self.config.options(section):
                    if not check_filter(self.searchregion, msg.region):
                        self.logger.debug(
                            f"Message '{msg.body}' ignored for sensor {self.sensorname} (didn't match region) - {self.searchregion}"
                        )
                        msg.is_posted = True
                        continue
                    self.logger.debug(
                        f"Message '{msg.body}' posted for sensor {self.sensorname} (sensor succesfull match region) - {self.searchregion}"
                    )
                    post = True

                # Check for matched capcodes
                if "searchcapcode" in self.config.options(section):
                    if not check_filter_with_list(self.searchcapcode, msg.capcodes):
                        self.logger.debug(
                            f"Message '{msg.body}'{msg.capcodes} ignored for sensor {self.sensorname} (didn't match capcode) - {self.searchcapcode}"
                        )
                        msg.is_posted = True
                        continue
                    self.logger.debug(
                        f"Message '{msg.body}'{msg.capcodes} posted for sensor {self.sensorname} (sensor succesfull match capcode) - {self.searchcapcode}"
                    )
                    post = True

                # Check for matched disciplines
                if "searchdiscipline" in self.config.options(section):
                    if not check_filter(self.searchdiscipline, msg.disciplines):
                        self.logger.debug(
                            f"Message '{msg.body}'{msg.disciplines} ignored for sensor {self.sensorname} (didn't match discipline) - {self.searchdiscipline}"
                        )
                        msg.is_posted = True
                        continue
                    self.logger.debug(
                        f"Message '{msg.body}'{msg.disciplines} posted for sensor {self.sensorname} (sensor succesfull match discipline) - {self.searchdiscipline}"
                    )
                    post = True

                # No other matches valid, if distance is not valid, skip
                if post is False:
                    self.logger.debug(
                        f"Message '{msg.body}' ignored for sensor {self.sensorname} (no post criteria)"
                    )
                    msg.is_posted = True
                    continue

                # If logging all messages to file is requested, log message
                if self.logtofile:
                    logmessage = (
                        "Posted"
                        + " -|- "
                        + msg.message_raw
                        + " -|- "
                        + self.sensorname
                        + " -|- "
                        + msg.region
                        + " -|- "
                        + msg.mapurl
                    )
                    log2file(logmessage)

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
                        "postal code": msg.postalcode,
                        "city": msg.city,
                        "address": msg.address,
                        "street": msg.street,
                        "remarks": msg.remarks,
                        "longitude": msg.longitude,
                        "latitude": msg.latitude,
                        "opencage": msg.opencage,
                        "mapurl": msg.mapurl,
                        "distance": msg.distance,
                        "friendly_name": msg.friendly_name,
                    },
                }
                heartbeat = {
                    "state": time.strftime("%Y%m%d"),
                }

                if self.use_hass:
                    try:
                        self.logger.debug(
                            f"Posting to Home Assistant - {self.sensorname}"
                        )
                        headers = {
                            "Authorization": "Bearer " + self.token,
                            "content-type": "application/json",
                        }

                        response = requests.post(
                            self.baseurl + "/api/states/sensor." + self.sensorname,
                            headers=headers,
                            data=json.dumps(
                                data,
                                default=lambda o: o.__dict__,
                                sort_keys=True,
                                indent=4,
                            ),
                        )
                        response.raise_for_status()
                        self.logger.debug(f"POST data: {data}")
                        self.logger.debug(
                            f"POST status: {response.status_code} {response.reason}"
                        )
                        self.logger.debug(f"POST text: {response.text}")
                        self.logger.debug(f"OpenCage status: {msg.opencage}")
                    except requests.HTTPError:
                        self.logger.error(
                            f"HTTP Error while trying to post data, check baseurl and token in config.ini: {response.status_code} {response.reason}"
                        )
                    except requests.exceptions.SSLError as err:
                        self.logger.error(
                            f"SSL Error occurred while trying to post data, check baseurl in config.ini:\n{err}"
                        )
                    except requests.exceptions.ConnectionError as err:
                        self.logger.error(
                            f"Connection Error occurred while trying to post data, check baseurl in config.ini:\n{err}"
                        )
                    finally:
                        # Mark as posted to prevent race conditions
                        msg.is_posted = True

                if self.use_mqtt:
                    try:
                        self.logger.debug("Posting to MQTT")
                        self.mqtt_topic_sensor = (
                            self.mqtt_topic + "/sensor/" + self.sensorname
                        )

                        data = json.dumps(data)
                        client = mqtt.Client()
                        client.username_pw_set(self.mqtt_username, self.mqtt_password)
                        client.connect(self.mqtt_server, self.mqtt_port, 60)
                        client.publish(self.mqtt_topic_sensor, data)
                        client.disconnect()

                        self.logger.debug(
                            f"MQTT status: Posting to {self.mqtt_server}:{self.mqtt_port} topic:{self.mqtt_topic}"
                        )
                        self.logger.debug(f"MQTT json: {data}")
                    except Exception as e:
                        self.logger.debug(f"MQTT Crashed: {e}")
                    finally:
                        # Mark as posted to prevent race conditions
                        msg.is_posted = True

    def data_thread_call(self):
        """Thread for parsing data from RTL-SDR."""
        self.logger.info(f"RTL-SDR process started with: {self.rtlfm_cmd}")
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
                    self.logger.debug(f"Error while decoding utf8 string: {line}")
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
                    postalcode = ""
                    city = ""
                    address = ""
                    street = ""
                    longitude = ""
                    latitude = ""
                    opencage = ""
                    distance = ""
                    mapurl = ""
                    gpscheck = False

                    self.logger.debug(line.strip())

                    # Check capcodes first, only if they are defined in config
                    if self.matchcapcodes or self.ignorecapcodes:
                        for capcode in capcodes.split(" "):
                            if self.matchcapcodes:
                                # Apply filter
                                if capcode in self.matchcapcodes:
                                    self.logger.debug(
                                        f"Capcode '{capcode}' found in '{self.matchcapcodes}' (capcode in match_capcodes)"
                                    )
                                else:
                                    self.logger.debug(
                                        f"Message '{message}' ignored because capcode '{capcode}' not found in '{self.matchcapcodes}'"
                                    )
                                    continue

                            if self.ignorecapcodes and len(capcodes.split(" ")) == 1:
                                if capcode in self.ignorecapcodes:
                                    self.logger.debug(
                                        f"Message '{message}' ignored because it contains only one capcode '{capcode}' which is found in '{self.ignorecapcodes}' (capcode in ignore_capcodes)"
                                    )
                                    continue

                    # Check for ignore texts
                    if check_filter(self.ignoretext, message):
                        self.logger.debug(
                            f"Message '{message}' ignored (matched ignore_text)"
                        )
                        if self.logtofile:
                            logmessage = "Ignore text" + " -|- " + line.strip()
                            log2file(logmessage)
                        continue

                    # Get address info if any, look for valid postalcode and get the two words around them
                    # A2 (DIA: ja) AMBU 17106 Schiedamseweg 3134BA Vlaardingen VLAARD bon 8576
                    regex_address = r"(\w*.) ([1-9][0-9]{3}[a-zA-Z]{2}) (.\w*)"
                    addr = re.search(regex_address, message)
                    if addr:
                        street = addr.group(1)
                        postalcode = addr.group(2)
                        city = addr.group(3)
                        address = f"{street} {postalcode} {city}"

                        # Remove Capitalized city name from message (when postalcode is found)
                        regex_afkortingen = "[A-Z]{2,}"
                        afkortingen = re.findall(regex_afkortingen, message)
                        for afkorting in afkortingen:
                            if afkorting in self.pltsnmn:
                                message = re.sub(afkorting, "", message)

                    # Get address in info if any, look for valid postalcode without letters and get the two words around them
                    # A1 13108 Surinameplein 1058 Amsterdam 12006
                    regex_address2 = r"(\w*.) ([1-9][0-9]{3}) (.\w*)"
                    addr2 = re.search(regex_address2, message)
                    if addr2:
                        # print("Regex Amsterdam")
                        street = addr2.group(1)
                        postalcode = addr2.group(2)
                        city = addr2.group(3)
                        address = f"{street} {city}"

                        # Remove Capitalized city name from message (when postalcode is found)
                        regex_afkortingen = "[A-Z]{2,}"
                        afkortingen = re.findall(regex_afkortingen, message)
                        for afkorting in afkortingen:
                            if afkorting in self.pltsnmn:
                                message = re.sub(afkorting, "", message)

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
                                    # If uppercase city is found, grab first word before that city name, since it's likely to be the streetname
                                    regex_address = rf"(\w*.) ({afkorting})"
                                    addr = re.search(regex_address, message)
                                    if addr:
                                        street = addr.group(1)
                                    address = f"{street} {city}"
                                    # Change uppercase city to normal city in message
                                    message = re.sub(afkorting, city, message)

                        # If no address is found, do a wild guess
                        if not address:
                            # Strip all status info from messag
                            regex_messagestrip = r"(^A\s?1|\s?A\s?2|B\s?1|^B\s?2|^B\s?3|PRIO\s?1|^P\s?1|PRIO\s?2|^P\s?2|^PRIO\s?3|^P\s?3|^PRIO\s?4|^P\s?4)(\W\d{2,}|.*(BR)\b|)|(rit:|rit|bon|bon:|ambu|dia|DIA)\W\d{5,8}|\b\d{5,}$|( : )|\(([^\)]+)\)( \b\d{5,}|)|directe (\w*)|(-)+/gi"
                            strip = re.sub(regex_messagestrip, "", message, flags=re.I)
                            # Strip any double spaces from message
                            regex_doublespaces = r"(^[ \t]+|[ \t]+$)"
                            strip = re.sub(regex_doublespaces, "", strip)
                            # Strip all double words from message
                            regex_doublewords = r"(\b\S+\b)(?=.*\1)"
                            strip = re.sub(regex_doublewords, "", strip)
                            # print("Strip: " + strip)
                            # Search in leftover message for a city corresponding to City list
                            for plaatsnaam in self.plaatsnamen:
                                if plaatsnaam in strip:
                                    self.logger.debug("City found: " + plaatsnaam)
                                    # Find first word left from city
                                    regex_plaatsnamen_strip = (
                                        rf"\w*.[a-z|A-Z] \b{plaatsnaam}\b"
                                    )
                                    plaatsnamen_strip = re.search(
                                        regex_plaatsnamen_strip, strip
                                    )
                                    if plaatsnamen_strip:
                                        addr = plaatsnamen_strip.group(0)
                                        # Final non address symbols strip
                                        regex_plaatsnamen_strip_strip = (
                                            r"(- )|(\w[0-9] )"
                                        )
                                        addr = re.sub(
                                            regex_plaatsnamen_strip_strip, "", addr
                                        )
                                        address = addr
                                        city = plaatsnaam
                                        self.logger.debug(
                                            "Adress found: "
                                            + plaatsnamen_strip.group(0)
                                        )

                    # Get more info about the capcodes
                    for capcode in capcodes.split(" "):
                        if capcode in self.capcodes:
                            receiver = "{} ({})".format(
                                self.capcodes[capcode]["description"], capcode
                            )
                            discipline = "{}".format(
                                self.capcodes[capcode]["discipline"]
                            )
                            region = self.capcodes[capcode]["region"]
                            location = self.capcodes[capcode]["location"]
                            remark = self.capcodes[capcode]["remark"]
                            self.logger.debug(
                                            "capcode opgehaald: "
                                            + receiver
                                        )
                        else:
                            receiver = capcode
                            discipline = ""
                            region = ""
                            remark = ""

                        # If this message was already received, only add extra info
                        if len(self.messages) > 0 and self.messages[0].body == message:
                            if self.messages[0].receivers == "":
                                self.messages[0].receivers = receiver
                            self.logger.debug(
                                        "capcode is nu: "
                                        + self.messages[0].receivers
                                        )                                
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

                            if self.messages[0].region == "":
                                self.messages[0].region = region

                            self.messages[0].capcodes.append(capcode)
                            self.messages[0].location = location
                            self.messages[0].postalcode = postalcode
                            self.messages[0].city = city
                            self.messages[0].street = street
                            self.messages[0].address = address
                        else:
                            # After midnight (UTC), reset the opencage disable
                            hour = datetime.utcnow()
                            if (
                                hour.hour >= 0
                                and hour.minute >= 1
                                and hour.hour < 1
                                and hour.minute < 15
                            ):
                                self.opencage_disabled = False

                    # If address is filled and OpenCage is enabled check for GPS coordinates
                    # First check local GPS database file
                    if address and self.use_opencage and not gpscheck is True:
                        try:
                            self.logger.debug(f"Checking databasefile - {address}")
                            if address in self.gpsdatabase:
                                self.logger.debug(
                                    f"Address is found in databasefile - {address}"
                                )
                                mapurl = self.gpsdatabase[address]["url"]
                                latitude = self.gpsdatabase[address]["latitude"]
                                longitude = self.gpsdatabase[address]["lontitude"]
                                self.logger.debug(
                                    f"GPS Database results: {latitude}, {longitude}, {mapurl}"
                                )
                                gpscheck = True
                            else:
                                self.logger.debug(
                                    f"Address {address} not found in databasefile"
                                )
                        except:
                            self.logger.info(
                                f"Error checking {address} in databasefile"
                            )

                    # If not found in GPS database file, check opencage
                    # If address is filled and OpenCage is enabled check for GPS coordinates
                    if (
                        address
                        and self.use_opencage
                        and (self.opencage_disabled is False)
                        and not gpscheck is True
                    ):
                        geocoder = OpenCageGeocode(self.opencagetoken)
                        try:
                            gps = geocoder.geocode(address, countrycode="nl")
                            gpscheck = True
                            if gps:
                                latitude = gps[0]["geometry"]["lat"]
                                longitude = gps[0]["geometry"]["lng"]
                                mapurl = gps[0]["annotations"]["OSM"]["url"]
                                self.logger.debug(
                                    f"OpenCage results: {latitude}, {longitude}, {mapurl}"
                                )
                                # Write opencage GPS data to local GPS database file
                                try:
                                    gps_data_fieldnames = [
                                        "address",
                                        "latitude",
                                        "lontitude",
                                        "url",
                                    ]
                                    gps_data = {
                                        "address": address,
                                        "latitude": latitude,
                                        "lontitude": longitude,
                                        "url": mapurl,
                                    }
                                    self.logger.debug(
                                        f"Writing to databasefile - {address}"
                                    )
                                    with open(
                                        "location_gps_database.csv", "a"
                                    ) as outfile:
                                        writer = csv.DictWriter(
                                            outfile,
                                            fieldnames=gps_data_fieldnames,
                                            delimiter=",",
                                            quoting=csv.QUOTE_MINIMAL,
                                            lineterminator="\n",
                                        )
                                        writer.writerow(gps_data)

                                    # Write also to GPS data in memory
                                    # following line does not work, need alternative to write to list in memory
                                    # self.gpsdatabase.append(gps_data)
                                    self.logger.debug(
                                        f"Writing variable - {address}"
                                    )
                                except:
                                    self.logger.debug(
                                        f"saving to local gpsfile or variable error - {address}"
                                    )

                            else:
                                latitude = ""
                                longitude = ""
                                mapurl = ""
                        # Rate-error check from opencage
                        except RateLimitExceededError as rle:
                            self.logger.error(rle)
                            # Over rate, opencage check disabled
                            if rle:
                                self.opencage_disabled = True
                        except InvalidInputError as ex:
                            self.logger.error(ex)
                    else:
                        gpscheck = False

                    opencage = f"enabled: {self.use_opencage} ratelimit: {self.opencage_disabled} gps-checked: {gpscheck}"

                    msg = MessageItem()
                    msg.groupid = groupid
                    msg.receivers = receiver
                    msg.capcodes = capcodes.split(" ")
                    msg.body = message
                    msg.message_raw = line.strip()
                    msg.disciplines = discipline
                    msg.priority = priority
                    msg.region = region
                    msg.location = location
                    msg.postalcode = postalcode
                    msg.longitude = longitude
                    msg.latitude = latitude
                    msg.city = city
                    msg.street = street
                    msg.address = address
                    msg.remarks = remark
                    msg.opencage = opencage
                    msg.mapurl = mapurl
                    msg.timestamp = to_local_datetime(timestamp)
                    msg.is_posted = False
                    msg.distance = distance
                    self.messages.insert(0, msg)

                # Limit the message list size
                if len(self.messages) > 100:
                    self.messages = self.messages[:100]

        except KeyboardInterrupt:
            os.kill(multimon_ng.pid, 9)

        self.logger.debug("Data thread stopped")

    # Thread for posting data to Home Assistant
    def post_thread_call(self):
        """Thread for posting data."""
        self.logger.debug("Post thread started")
        while True:
            if self.running is False:
                break

            now = time.monotonic()
            for msg in self.messages:
                if msg.is_posted is False and now - msg.timereceived >= 1.0:
                    self.post_data(msg)
            time.sleep(1.0)
        self.logger.debug("Post thread stopped")


# Start application
Main()
