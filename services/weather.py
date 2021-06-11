import os,sys;
import requests;
from os.path import dirname, join, abspath
sys.path.append("../utils.py")
sys.path.append("../consts.py")
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
from utils import object_to_search_params, format_weather_day, join_lines
from consts import BTN_TEXTS
from decouple import config
from math import floor, ceil

def get_url_icon(icon):
  return f"http://openweathermap.org/img/w/{icon}.png"
def get_icon(object):
  return object["weather"][0]["icon"]
default_params = {
    "lang":"ru",
    "q":"moscow",
    "appid":config("WEATHER_KEY"),
    "units":"metric"
  }

def get_result(url, params):
  response = requests.get(url + params)
  print(url + params)
  result = response.json()
  return result

def get_cloud_state(object):
  cloud = object["clouds"]["all"]
  cloud_state = "Облачно" if cloud > 0.4 else "Ясное небо" if cloud < 0.1 else "Небольшая облачность"
  return cloud_state

def get_wind_status(object):
  wind_from_data = object["wind"]["speed"]
  wind = None
  if wind_from_data < 1:
    wind = "нет"
  elif wind_from_data < 4:
    wind = "Легкий"
  elif wind_from_data < 9:
    wind = "Умеренный"
  elif wind_from_data < 16:
    wind = "Сильный"
  else:
    wind = "Буря"
  return (wind, wind_from_data)

def get_wind_dir(object):
  wind_deg = int(object["wind"]["deg"])
  dir = None
  if(60 > wind_deg >= 30):
    dir = "северо-восточный"
  elif( wind_deg < 120):
    dir = "восточный"
  elif( wind_deg < 150):
    dir = "юго-восточный"
  elif( wind_deg < 210):
    dir = "южный"
  elif( wind_deg < 240):
    dir = "юго-западный"
  elif( wind_deg < 300):
    dir = "западный"
  elif( wind_deg < 330):
    dir = "северо-западный"
  else:
    dir = "северный"
  return dir

def get_temps(object):
  temp_min = floor(object["main"]["temp_min"])
  temp_max = ceil(object["main"]["temp_max"])
  return (temp_min, temp_max)

def get_temp(object):
  return round(object["main"]["temp"])
  
def get_weather_info(object, sym = ""):
  cloud_state = get_cloud_state(object=object)
  temp_min, temp_max = get_temps(object=object)
  temp_res = temp_min if temp_min == temp_max else " - ".join([str(i) for i in [temp_min,temp_max]])
  wind, wind_speed = get_wind_status(object=object)
  dir = get_wind_dir(object=object)
  icon = get_url_icon(icon=object["weather"][0]["icon"])
  result_to_user = []
  result_to_user.append(f'{cloud_state}, температура {temp_res}°C')
  result_to_user.append(f'Давление: {object["main"]["pressure"]} мм рт.ст., влажность {object["main"]["humidity"]}%')
  result_to_user.append(f'Ветер: {wind}, {wind_speed} м/с, {dir}')
  result = join_lines([sym + x for x in result_to_user])
  return (result, icon)


def get_weather_current():
  url = "http://api.openweathermap.org/data/2.5/weather"
  params = object_to_search_params(default_params)
  result = get_result(url=url,params=params)
  result_to_user, icon = get_weather_info(object=result) 
  return {"text": result_to_user, "icon": icon, "title": "Погода в Москве"}

def get_weather_day(type):
  is_today = type == BTN_TEXTS["TODAY"]
  string = "Погода в Москве " + ("сегодня"  if is_today else "завтра") 
  url = "http://api.openweathermap.org/data/2.5/forecast"
  params = object_to_search_params(default_params)
  result = get_result(url=url,params=params)
  icons = []
  temps = []
  weather = {
    "УТРО": None,
    "ДЕНЬ": None,
    "ВЕЧЕР": None,
    "НОЧЬ": None,
  }
  weather_list = result["list"]
  for object in weather_list:
    key = None
    hour = object["dt_txt"].split(" ").pop().split(":")[0]
    if(hour == "00"):
      key = "НОЧЬ"
    if(hour == "06"):
      if(not is_today):
        is_today = True
        continue
      key = "УТРО"
    if(hour == "12"):
      key = "ДЕНЬ"
    if(hour == "18"):
      key = "ВЕЧЕР"
    if((not is_today) or (not key) or (key != "УТРО" and not weather.get("УТРО") )):
      continue
    info, icon = get_weather_info(object=object, sym="// ")
    weather[key] = info
    icons.append(icon)
    temps.append(get_temp(object=object))
    if weather.get("НОЧЬ"):
      break;
  
  temps_txt = format_weather_day(temps)
  stats = join_lines([join_lines(x) for x in list(weather.items())]) 
  
  return dict(
    icons = icons,
    title = string,
    text = "\n\n".join([temps_txt,stats])
    
  )

def get_weather_5_days():
  url = "http://api.openweathermap.org/data/2.5/forecast"
  params = object_to_search_params(default_params)
  result = get_result(url=url,params=params)
  weather_list = result["list"]
  start = None
  end = None
  night = []
  day = []
  icons = []
  for object in weather_list:
    hour = object["dt_txt"].split(" ").pop().split(":")[0]
    yyyy,mm,dd =  object["dt_txt"].split(" ")[0].split("-")
    if(hour in ["00","12"]):
      temp = get_temp(object=object)
      if(hour == "00"):
        if(not start):
          start = f"{dd}.{mm}"
        end = f"{dd}.{mm}"
        night.append(temp)
      else:
        icon = get_url_icon(icon=get_icon(object=object))
        day.append(temp)
        icons.append(icon)
  string = f"Погода в Москве с {start} по {end}"
  
  temps = [format_weather_day(day, "день"), format_weather_day(night, "ночь")]
  return {
    "string": string, 
    "icons": icons, 
    "temps": join_lines(temps),
  }