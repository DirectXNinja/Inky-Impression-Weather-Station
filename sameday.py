#!/usr/bin/python3
# -*- coding: utf-8 -*-
import copy, json,requests, pytz,time
from inky.inky_uc8159 import Inky, DESATURATED_PALETTE
import datetime
from PIL import Image, ImageFont, ImageDraw
import io, apikey, os,signal, iconmap
import RPi.GPIO as GPIO

path = os.path.dirname(os.path.realpath(__file__))

ICON_SIZE = 200
TILE_WIDTH = 200
TILE_HEIGHT = 200
FONT_SIZE = 35
SPACE = 0
ROTATE = 0 # 180 = flip display
USE_INKY = True
SHOW_CLOCK = False
SLEEP_TIME = 3600
colours = ['Black', 'White', 'Green', 'Blue', 'Red', 'Yellow', 'Orange']
percipitation_colour = colours[0]
temp_colour = colours[4]
day_colour = colours[2]
presure_colour = colours[3]
LABELS = ['A','B','C','D']
time_colour = colours[4]

class Day:
    def __init__(self, temp, speed, pop, id, description, dt, dt_txt):
        self.temp = int(temp + 0.5)
        self.speed = int(speed + 0.5)
        self.pop = pop
        self.id = id
        self.description = description
        self.dt = dt
        self.dt_txt = dt_txt
    
    def __str__(self):
        return f"{self.temp} {self.speed} {self.pop}  {self.id}  {self.description}  {self.dt} {self.dt_txt}"

def get_icon(name):
    return Image.open(name).convert("RGBA")

def day_lists_not_identical(days, other_days):
    if (len(days) != len(other_days)):
        return True
    for i in range(len(days)):
        if (days[i].min != other_days[i].min):
            return True
        if (days[i].max != other_days[i].max):
            return True
        if (days[i].pop != other_days[i].pop):
            return True
        if (days[i].id != other_days[i].id):
            return True
    return True

api_key = apikey.api_key
if (api_key == "<your API key>"):
    print("You forgot to enter your API key")
    exit()

night_map = iconmap.night_map
day_map = iconmap.day_map
general_map = iconmap.general_map

lat = apikey.lat
lon = apikey.lon
api_key = apikey.api_key
unit = apikey.unit

url = "https://api.openweathermap.org/data/2.5/forecast?lat=%s&lon=%s&appid=%s&units=%s"% (lat, lon, api_key, unit)
#print(url)

palette_colors = [(c[0] / 255.0, c[1] / 255.0, c[2] / 255.0) for c in DESATURATED_PALETTE[2:6] + [(0, 0, 0)]]
tile_positions = []
for i in range(2):
    for j in range(4):
        tile_positions.append((j * TILE_WIDTH, i * TILE_HEIGHT))
inky_display = Inky()
satuation = 0
y_top = int(inky_display.height)
y_bottom = y_top + int(inky_display.height * (4.0 / 10.0))

font = ImageFont.truetype(path+
    "/fonts/BungeeColor-Regular_colr_Windows.ttf", FONT_SIZE)
smallfont = ImageFont.truetype(path+
    "/fonts/BungeeColor-Regular_colr_Windows.ttf", 15)
old_days = []

try:
    response = requests.get(url)
    data = json.loads(response.text)
except:
    None

days = []
daily = data["list"]
for day in daily:
    temp = day["main"]["temp"]
    speed = day["wind"]["speed"]
    pop = day["pop"]
    id = day["weather"][0]["id"]
    description = day["weather"][0]["description"]
    dt = day["dt"]
    dt_txt = day["dt_txt"]
    days.append(Day(temp, speed, pop, id, description, dt, dt_txt))
print(days[0])
print(days[1])
print(days[2])

inky_list = []
inky_list.insert(0,days[0])
inky_list.insert(1,days[1])
inky_list.insert(2,days[2])
inky_list.insert(3,days[3])

if (day_lists_not_identical(days, old_days)):
    old_days = copy.deepcopy(days)
    img = Image.new("RGBA", inky_display.resolution, colours[1])
    draw = ImageDraw.Draw(img)
    for i in range(3):
       name = path+"/icons/wi-"
       name += general_map[inky_list[i].id]
       
       # Icon handling and placement
       icon = get_icon(name)
       x = tile_positions[i][0] + (TILE_WIDTH - ICON_SIZE) // 2
       y = tile_positions[i][1]
       img.paste(icon, (x, y))
       
       # Pop string placement
       text = str(int(100 * inky_list[i].pop)) + "%"
       left, top, right, bottom = font.getbbox(text)
       text_width = right - left
       text_height = bottom - top
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y = tile_positions[i][1] + ICON_SIZE + SPACE
       draw.text((x, y), text, percipitation_colour, font)
       
       # Temp string placement
       text = str(inky_list[i].temp) + "Â°"
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y += FONT_SIZE
       draw.text((x, y), text, colours[4], font)
       
       # Windspeed string placement
       text = str(inky_list[i].speed) + " m/s"
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y += FONT_SIZE
       draw.text((x, y), text, colours[3], font)
       
       # WeatherDescription string placement
       text = str(inky_list[i].description)
       left, top, right, bottom = smallfont.getbbox(text)
       text_width = right - left
       text_height = bottom - top
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y += FONT_SIZE
       draw.text((x, y), text, presure_colour, smallfont)
       
       # Takes dt parameter and converts it from unixtime to name of the day
       ts = time.gmtime(inky_list[i].dt)
       day_name = time.strftime("%a", ts)
       text = day_name
       left, top, right, bottom = font.getbbox(text)
       text_width = right - left
       text_height = bottom - top
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y += FONT_SIZE
       draw.text((x, y), text, day_colour, font)
       
    # Takes dt parameter and converts it from unixtime to time
       ts = time.gmtime(inky_list[i].dt)
       day_name = time.strftime("%H:%M", ts)
       text = day_name
       left, top, right, bottom = font.getbbox(text)
       text_width = right - left
       text_height = bottom - top
       x = tile_positions[i][0] + (TILE_WIDTH - text_width) // 2
       y += FONT_SIZE
       draw.text((x, y), text, day_colour, font)
       
       img.rotate(180)
    #img.show()
    inky_display.set_border(colours[4])
    inky_display.set_image(img.rotate(ROTATE), saturation=0)
    inky_display.show()
    exit()
