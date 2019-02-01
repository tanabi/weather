#!/usr/bin/env python3
#
# Python script to pull weather from an airport and publish it to a MUCK.
# This gives realistic weather conditions to a MUCK based on real world
# stuff.

from configparser import ConfigParser
from pyfuzzball.mcp import MCP

import os
import requests
import sys
import xml.etree.ElementTree as ET


# Load configuration
if not os.path.exists('config.ini'):
    print("You need a config.ini for this to work.")
    sys.exit(1)

config = ConfigParser()
config.read('config.ini')

if 'weather' not in config:
    print("Config must have a weather section")

# What are the required config paramters?
for param in ('muck_host', 'muck_port', 'mcp_key', 'airport'):
    if param not in config['weather']:
        print("Could not find config parameter %s." % param)
        sys.exit(1)

# What is our METAR URL?
url = "https://www.aviationweather.gov/adds/dataserver_current/httpparam?" \
      "dataSource=metars&requestType=retrieve&format=xml&" \
      "stationString=%s&mostRecent=true&hoursBeforeNow=3" \
      % config['weather']['airport']

response = requests.get(url)

# Load the XML document
root = ET.fromstring(response.content.decode('utf-8'))

# What we want to parse out:
#
# - temp_c
# - dewpoint_c
# - wind_dir_degrees
# - wind_speed_kt
# - wind_gust_kt
# - visibility_statute_mi
# - altim_in_hg
# - sky_condition
# - precip_in
# - snow_in
#
# Fields are described here:
#
# https://www.aviationweather.gov/dataserver/fields?datatype=metar

# Get our elements
metar = {}

for ele in root.find('data').find('METAR').iter():
    # Copy these over to our structure with no additional processing.
    if ele.tag in ('temp_c', 'dewpoint_c', 'wind_dir_degrees',
                   'wind_speed_kt', 'wind_gust_kt', 'visibility_statute_mi',
                   'altim_in_hg', 'precip_in', 'snow_in'):
        metar[ele.tag] = ele.text
    elif ele.tag == 'sky_condition':
        metar["sky_condition_cover"] = ele.attrib.get('sky_cover')
        metar["sky_condition_base"] = ele.attrib.get('cloud_base_ft_agl')

# Compile our weather message based on the conditions.
message = []

temp = float(metar['temp_c'])

if temp < 0:
    message.append("It is below-0 freezing.")
elif temp < 10:
    message.append("It is freezing out.")
elif temp < 20:
    message.append("It is chilly out.")
elif temp < 30:
    message.append("The tempurature is nice.")
elif temp < 40:
    message.append("It is really hot out.")
else:
    message.append("It is sweltering out.")

dew_point = float(metar['dewpoint_c'])

if dew_point > temp:
    message.append("Right now, it is very foggy.")
elif dew_point > 15:
    if dew_point < 21:
        message.append("Right now, it is somewhat humid.")
    elif dew_point < 26:
        message.append("Right now, it is really humid.")
    else:
        message.append("Right now, the humidity is pretty brutal.")

wind_direction = int(metar['wind_dir_degrees'])
wind_speed = int(metar['wind_speed_kt'])
wind_gust_kt = 0

if 'wind_gust_kt' in metar:
    wind_gust_kt = int(metar['wind_gust_kt'])

# Double 0 is calm winds
if not (wind_direction == 0 and wind_speed == 0):
    wind = "Winds are "

    if wind_direction == 0:
        wind += "variable"
    elif wind_direction < 20:
        wind += "from the north"
    elif wind_direction < 70:
        wind += "from the north east"
    elif wind_direction < 110:
        wind += "from the east"
    elif wind_direction < 160:
        wind += "from the south east"
    elif wind_direction < 200:
        wind += "from the south"
    elif wind_direction < 250:
        wind += "from the south west"
    elif wind_direction < 290:
        wind += "from the west"
    elif wind_direction < 340:
        wind += "from the north west"
    else:
        wind += "from the north"

    wind += " and "

    if wind_speed < 2:
        wind += "calm"
    elif wind_speed < 5:
        wind += "breezy"
    elif wind_speed < 10:
        wind += "kind of windy"
    elif wind_speed < 15:
        wind += "strong"
    else:
        wind += "very strong"

    if wind_gust_kt > 20:
        wind += " and gusty"

    wind += "."
    message.append(wind)

if metar["sky_condition_cover"] == "CLR" or \
   metar["sky_condition_cover"] == "SKC":
    message.append("There isn't a cloud in the sky.")
elif metar["sky_condition_cover"] == "FEW":
    message.append("There are a few clouds but it is mostly clear.")
elif metar["sky_condition_cover"] == "SCT":
    message.append("It is a little cloudy.")
elif metar["sky_condition_cover"] == "BKN":
    message.append("There is a lot of cloud cover.")
elif metar["sky_condition_cover"] == "OVC":
    message.append("It is overcast.")

# Easter Island doesn't seem to report precipitation
"""
precip = 0

if 'precip_in' in metar:
    float(metar['precip_in'])

if precip > 0:
    message.append("And it is raining.")
"""

# Do rain based on dew point
if temp - dew_point < 2:
    message.append("And it is raining.")
elif temp - dew_point < 5 and  \
     float(metar['visibility_statute_mi']) < 2:
    message.append("And it is pretty foggy right now.")

m = MCP(config['weather']['muck_host'], config['weather']['muck_port'],
        config['weather'].get('use_ssl', 0), True)
m.negotiate(['net-hopeisland-weather'])
m.call('net-hopeisland-weather', 'set', {
    "auth": config['weather']['mcp_key'],
    "weather": "  ".join(message)
})

m.quit()
