import os, sys; 
from os.path import dirname, join, abspath
sys.path.append("../excel.py")
sys.path.append("../consts.py")
sys.path.append("../graph.py")
sys.path.append("../utils.py")
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import requests
import re
from bs4 import BeautifulSoup
from utils import join_lines
from graph import get_image_graph
from datetime import date, datetime
import locale
locale.setlocale(locale.LC_TIME, "ru")

def get_soup():
  url = "https://coronavirusstat.ru/country/russia/"
  page = requests.get(url)
  soup = BeautifulSoup(page.text, "html5lib")
  return soup

def get_time_text(soup):
  elem = soup\
    .find("h1", class_="font-weight-bold")\
    .findNextSibling()
  time = re\
    .compile(".+[\d]{1,2}\s[а-яА-ЯёЁ]+\s[\d]+:[\d]+")\
    .findall(elem.getText())[0]
  return time

def get_types(soup):
  types_html = soup\
    .find("table", class_="table")\
    .find("thead")\
    .find_all("th")[1::]
  types = [type.getText() for type in types_html]
  return types

def get_stat_rows(soup):
  stats = soup\
    .find("table", class_="table")\
    .find("tbody")\
    .find_all("tr")
  return stats

def get_city_rows(soup):
  cities = soup\
    .find_all("div", class_="c_search_row" )
  return cities

def get_day_info(row, soup, item):
  time_text = get_time_text(soup)
  types = get_types(soup)
  result = []
  items = row.find_all(item["tag"], class_=item["class"]) if "class" in item else row.find_all(item["tag"]) 
  for i in range(len(items)):
    string = f"{types[i]}: {items[i].contents[0]} ("
    diff = items[i].contents[1]
    string += (str(diff.getText()) if str(diff).strip() else "+0") + " за сегодня)"
    if(i != len(items) -1):
      result.append(string)
    else:
      result.insert(0, string)
  result.insert(0, time_text)
  return join_lines(result)

def get_city_info(row):
  result = []
  items = row.find_all("div", recursive=False) 
  for i in range(len(items)):
    category = items[i].find("div").getText()
    cat_regex = re.compile(category, flags=re.I)
    if(cat_regex.findall("летальность")):
      continue
    stat_block = items[i].find("div").findNextSibling()
    html_count = stat_block.find("span", recursive=False)
    all_count = (html_count.getText() if html_count else str(stat_block.contents[0])).strip()
    diff_html = stat_block.find("small").find("span", class_="badge")
    diff_txt = diff_html.getText() if diff_html else None
    diff = diff_txt if (diff_txt and '%' not in diff_txt) else "+0"
    stat_info = f"{category}: {all_count} ({diff} за сегодня)"
    if(cat_regex.findall("cлучаев")):
      result.insert(0, stat_info)
    else:
      result.append(stat_info)
  return result

def get_stat_last_10_days():
  soup = get_soup()
  time = get_time_text(soup=soup)
  types = get_types(soup=soup)
  day_number = re.compile("\d+").findall(time)[0]
  types =get_types(soup=soup)
  stats = get_stat_rows(soup=soup)
  result = { 
    "current_day_stat": None,
    "died": [],
    "save": [],
    "active": [],
    "dates": [],
    "img": None
  }
  is_added = False
  for tries, stat in enumerate(stats):
    if(tries == 10):
      break
    result["dates"].insert(0, stat.find("th").getText())
    if(not is_added and stat.find("th").getText().split(".")[0] == day_number):
      is_added = True
      result["current_day_stat"] = get_day_info(soup=soup, row=stat, item={"tag": "td"}) 
    for i, td in enumerate(stat.find_all("td")):
      count = int(td.contents[0])
      list_to_add = None
      type = types[i].lower() 
      if type == "активных":
        list_to_add = result["active"] 
      elif type == "вылечено":
        list_to_add = result["save"]
      elif type == "умерло":
        list_to_add = result["died"]
      if(list_to_add != None):
        list_to_add.insert(0, count)
  result["img"] = get_image_graph(
    dates=result["dates"],
    active=result["active"],
    died=result["died"],
    save=result["save"],
  )
  return {"img": result["img"], "stat": result["current_day_stat"]}

def get_stat_by_query(query):
  regex = re.compile(query, flags=re.I)
  soup = get_soup()
  time = get_time_text(soup=soup)
  city_rows = get_city_rows(soup=soup)
  current_day_stat = []
  for city_row in city_rows:
    a = city_row.find("a").getText()
    if(not regex.findall(a)):
      continue
    stat = city_row.find("div").findNextSibling()
    current_day_stat = get_city_info(row=stat)
    current_day_stat.insert(0, time)
    current_day_stat.insert(1, f"Регион: {a}")
    break;
  if(not current_day_stat):
    return "Регион не найден"
  return join_lines(current_day_stat)