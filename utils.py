import requests
from PIL import Image
import PIL
import re
from bs4 import BeautifulSoup
import uuid
from datetime import datetime, timedelta
from consts import MONTHS, BTN_TEXTS

def get_current_week():
  
  url = "https://www.mirea.ru"
  page = requests.get(url)
  soup = BeautifulSoup(page.text, "html.parser")
  result = soup\
    .find("div", class_="mainpage")\
    .find("div")\
    .find("div")\
    .find("div", class_="bonus_cart-title")
  text = result.getText().split(",").pop()
  week = re.findall(pattern="[0-9]+", string=text)[0]
  return int(week)


def object_to_search_params(object):
  def to_str(key):
    return f"{key}={object[key]}"
  res = object.keys()
  return "?" + "&".join(list(map(to_str, res)))

def get_random_id():
  return str(uuid.uuid4())

def with_spaces(num):
  return '{0:,}'.format(num).replace(',', ' ')

def no_fractions(str):
  return str.split(".")[0]

def join_lines(array):
  return "\n".join([str(x) for x in array])

def get_start_week(type):
  day_on_week = datetime.now().weekday()
  today = datetime.today()
  if(type == BTN_TEXTS["NEXT_WEEK"]):
    today += timedelta(weeks=1)
  start_week = today - timedelta(days=day_on_week)
  return start_week

def get_date_day_month():
  today = datetime.today()
  day = today.day
  month = MONTHS[today.month]
  return f"{day} {month}"

def is_group(text):
  return re.compile("^[а-яА-ЯёЁ]{4}-[\d]{2}-[\d]{2}$").findall(text)

def format_weather_day(list, day_name=""):
  return "".join([f"/{x}°C/" for x in list ]) + (" " + day_name) if day_name else ""

def to_photo_attachment(photo):
  return f"photo{photo['owner_id']}_{photo['id']}"

def join_photos(photos):
  count = len(photos)
  img = Image.new("RGB", (50 * count, 50))
  for i in range(count):
    arg = requests.get(photos[i], stream=True).raw if photos[i].startswith("http") else photos[i] 
    open_img = Image.open(arg)
    img.paste(open_img, (50 * i, 0))
  path = "{id}.png".format(id=get_random_id())
  img.save(path)
  return path

def to_n_items(array, n):
  length = len(array)
  if(length == n):
    return array
  if(length == 1):
    return [array[0] for x in range(n)]
  if(length < n):
    times = n // len(array)
    ost = n % len(array)
    temp = []
    for i in range(times):
      temp.extend(array)
    temp.extend(array[0:ost])
    return temp
  if(length > 2):
    return array[0:2]
  else:
    return [None,None]