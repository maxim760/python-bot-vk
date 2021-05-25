import os, sys; 
from os.path import dirname, join, abspath
sys.path.append("../excel.py")
sys.path.append("../consts.py")
sys.path.append("../utils.py")
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
from utils import get_random_id
from consts import BTN_TEXTS
import requests
import re
from bs4 import BeautifulSoup
from datetime import date, datetime



def get_schedule(group_name):
  group, year = group_name.split("-")[1::]
  now = datetime.now()
  month = now.month
  course = (now.year % 100) - int(year) + 1 - 1 if month < 9 else 0
  url = "https://www.mirea.ru/schedule/"
  page = requests.get(url)
  soup = BeautifulSoup(page.text, "html.parser")
  refs = soup\
    .find("div", {"id": "tabs"})\
    .find(text=re.compile("Институт информационных технологий", flags=re.I))\
    .findParent("div")\
    .findNextSibling("div")\
    .find_all("a")
  for a in refs:
    if a.find(text=re.compile(f"{course} курс", flags=re.I)):
      href = a["href"]
      filename = get_random_id() + ".xlsx"
      with open(filename, "wb") as f:
        resp = requests.get(href)
        f.write(resp.content)
  
      return (course, filename)
  return None
  
  

def get_courses_files(courses):
  courses_len = len(courses)
  if(courses_len == 0):
    return {}
  url = "https://www.mirea.ru/schedule/"
  page = requests.get(url)
  soup = BeautifulSoup(page.text, "html.parser")
  refs = soup\
    .find("div", {"id": "tabs"})\
    .find(text=re.compile("Институт информационных технологий", flags=re.I))\
    .findParent("div")\
    .findNextSibling("div")\
    .find_all("a")
  files = {}
  finded = 0
  for a in refs:
    if a.find(text=re.compile(f'[{"".join([str(x) for x in courses])}] курс', flags=re.I)):
      finded += 1
      course = int(a.getText().strip().split(" ")[0])
      href = a["href"]
      filename = get_random_id() + ".xlsx"
      with open(filename, "wb") as f:
        resp = requests.get(href)
        f.write(resp.content)
      files[course] = filename
      if(finded == courses_len):
        break
  return files
