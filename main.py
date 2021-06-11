import vk_api
import json
import re
import vk_api
from vk_api import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from decouple import config
from functools import reduce
from services.schedule import get_schedule, get_courses_files
from services.weather import get_weather_current, get_weather_day, get_weather_5_days
from services.coronavirus import get_stat_last_10_days, get_stat_by_query
from excel import get_schedule_day, get_schedule_week,get_schedule_full_day, find_teachers,get_teacher_day,get_teacher_week
from utils import get_current_week, join_photos, is_group, to_photo_attachment
from consts import FORMAT_GROUP, BTN_TEXTS, UNKNOWN, DAYS_ON_WEEK_UPPER
def get_bot_instruction():
  return """С помощью бота вы можете получать:
    ⚡ Расписание учебной группы и преподавателей
    ⚡ Погоду в Москве
    ⚡ Статистику коронавируса
    
    Для начала введите название группы (XXXX-00-00), чтобы бот её запомнил
    
    Доступные команды:
      ввод группы - бот запоминает вашу группу
      бот - для расписания
      бот [день недели] - расписание для вашей группы на определенный день недели
      бот [название группы] - расписание для группы
      бот [день недели] [название группы] - расписание на день недели для введенной группы
      бот [название группы] [день недели] - то же самое, порядок не важен
      найти [фамилия преподавателя] - расписание преподавателя
      погода - для погоды в Москве
      корона - для получения статистики по коронавирусу
      корона [название региона] - статистика коронавируса по региону
    """



def get_teacher_keyboard(teacher):
  category ="TEACHER"
  kwargs = dict(payload=(category, teacher))
  keyboard = VkKeyboard()
  keyboard.add_button(label=BTN_TEXTS["TODAY"], color=VkKeyboardColor.POSITIVE , **kwargs)
  keyboard.add_button(label=BTN_TEXTS["TOMORROW"], color=VkKeyboardColor.NEGATIVE , **kwargs)
  keyboard.add_line()
  keyboard.add_button(label=BTN_TEXTS["THIS_WEEK"],color=VkKeyboardColor.PRIMARY,  **kwargs)
  keyboard.add_button(label=BTN_TEXTS["NEXT_WEEK"],color=VkKeyboardColor.PRIMARY,  **kwargs)
  return keyboard.get_keyboard()
def get_dif_teachers_keyboard(teachers):
  category ="TEACHERS_NAME"
  keyboard = VkKeyboard(one_time=True)
  for i, name in enumerate(teachers):
    keyboard.add_button(label=name, color=VkKeyboardColor.PRIMARY , payload=(category, name))
    if(i == len(teachers) - 1):
      break
    keyboard.add_line()
  return keyboard.get_keyboard()
def get_schedule_keyboard(group):
  category ="SCHEDULE"
  kwargs = dict(payload=(category, group))
  keyboard = VkKeyboard()
  keyboard.add_button(label=BTN_TEXTS["TODAY"], color=VkKeyboardColor.POSITIVE , **kwargs)
  keyboard.add_button(label=BTN_TEXTS["TOMORROW"], color=VkKeyboardColor.NEGATIVE , **kwargs)
  keyboard.add_line()
  keyboard.add_button(label=BTN_TEXTS["THIS_WEEK"],color=VkKeyboardColor.PRIMARY,  **kwargs)
  keyboard.add_button(label=BTN_TEXTS["NEXT_WEEK"],color=VkKeyboardColor.PRIMARY,  **kwargs)
  keyboard.add_line()
  keyboard.add_button(label="какая неделя?")
  keyboard.add_button(label="какая группа?")
  return keyboard.get_keyboard()
def get_weather_keyboard():
  category ="WEATHER"
  kwargs = dict(payload=(category, None))
  keyboard = VkKeyboard()
  keyboard.add_button(label=BTN_TEXTS["NOW"], color=VkKeyboardColor.PRIMARY , **kwargs)
  keyboard.add_button(label=BTN_TEXTS["TODAY"], color=VkKeyboardColor.POSITIVE , **kwargs)
  keyboard.add_button(label=BTN_TEXTS["TOMORROW"], color=VkKeyboardColor.POSITIVE , **kwargs)
  keyboard.add_line()
  keyboard.add_button(label=BTN_TEXTS["FIVE_DAYS"],color=VkKeyboardColor.POSITIVE,  **kwargs)
  return keyboard.get_keyboard()


weather_key = config("WEATHER_KEY")
vk_key = config("VK_SECRET_KEY")
def main():
  vk_session = vk_api.VkApi(token=vk_key)
  def get_attachment(picture):
    img = picture if type(picture) == str else join_photos(photos=picture)
    photo = VkUpload(vk_session).photo_messages(photos=img)[0]
    return to_photo_attachment(photo)
  users = {}
  groups = {}
  files = {
    1: None,
    2: None,
    3: None,
  }
  
  vk = vk_session.get_api()
  VkKeyboard(one_time=True).add_button("старт", color=VkKeyboardColor.SECONDARY)
  longpoll = VkLongPoll(vk_session)
  
  for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW and event.text and event.to_me:
      def send_message(message=None, keyboard=None,attachment=None):
        vk.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=message,
        keyboard=keyboard,
        attachment=attachment
        )
      text = str(event.text).strip().lower()
      user_id = event.user_id 
      user_group = users.get(user_id)
      
      is_not_user = not user_group
      # получаю информацию нажатой кнопке
      payload_from_msg = event.extra_values.get("payload")
      payload = json.loads(payload_from_msg) if payload_from_msg else None
      category, payload_dop_info = payload if (payload and type(payload) != dict) else (None, None)
      group_name = payload_dop_info or user_group
      teacher_name = payload_dop_info
      
      
      if(text in ["начать", "начало", "старт"]):
        if(user_id not in users):
          users[user_id] = None
          
        send_message(message=get_bot_instruction())
      elif(is_group(text)):
        group = text.upper()
        res = get_schedule(group_name=group)
        if(not res):
          send_message(message="Группа не найдена")
        else:  
          course, filename = res
          users[user_id] = group
          groups[group] = course
          files[course] = filename
          send_message(message=f"Я запомнил, что ты из группы {group}")      
      elif(text == "бот"):
        if(is_not_user):
          send_message(message="Введите свою группу")
        else:
          send_message(message="Показать расписание",keyboard=get_schedule_keyboard(group=group_name))
      elif(text.startswith("какая неделя")):
        week = get_current_week()
        send_message(message=f"Идёт {week} неделя")
      elif(text.startswith("какая группа")):
        group = users.get(user_id)
        msg = f"Показываю расписание группы {group}" if group else "Группы неизвестна, введите её " + FORMAT_GROUP
        send_message(message=msg)
      elif(category == "SCHEDULE"):
        schedule = None
        if(group_name not in groups):
            res = get_schedule(group_name=group_name)
            if(not res):
              send_message(message="Группа не найдена")
              continue
            course, filename = res
            groups[group_name] = course
            files[course] = filename
        kwargs = dict(group=group_name, filename=files[groups[group_name]],type=text)
        if(text in [BTN_TEXTS["TODAY"], BTN_TEXTS["TOMORROW"]]):
          schedule = get_schedule_day(**kwargs)
        else:
          schedule = get_schedule_week(**kwargs)
        send_message(message=schedule)
      elif(text.startswith("бот ")):
        words = [str(x).upper() for x in re.split(r"\s+",text)[1::]]
        if(len(words) > 2):
          send_message(message=UNKNOWN)
        elif(len(words) == 1):
          word = words[0]
          if(is_group(word)):
            send_message(message=f"показать расписание группы {word}", keyboard=get_schedule_keyboard(group=word))
          elif(word in DAYS_ON_WEEK_UPPER.values()):
            if(is_not_user):
              send_message(message="Введите свою группу")
              continue;    
            schedule = get_schedule_full_day(filename=files[groups[group_name]], group=group_name,day=word)
            send_message(message=schedule)
          else:
            send_message(message=UNKNOWN)
        else:
          # длина - 2
          w1,w2 = words
          group, day = (w1,w2) if is_group(w1) else (w2,w1)
          if(not is_group(group) or (day not in DAYS_ON_WEEK_UPPER.values())):
            send_message(message=UNKNOWN)
            continue;
          if(group not in groups):
            res = get_schedule(group_name=group)
            if(not res):
              send_message(message="Группа не найдена")
              continue
            course, filename = res
            groups[group] = course
            files[course] = filename
          schedule = get_schedule_full_day(filename=files[groups[group]], group=group,day=day)
          send_message(message=schedule)     
      elif(text.startswith("найти ")):
        text_words = re.split(r"\s+",text)[1::] 
        name_from_text = text_words[0]
        if(len(text_words) != 1):
          send_message(message="После \"найти\" должно идти только 1 слово - фамилия преподавателя")
          continue
        
        def not_exist_file(acc,item):
          if(not item[1]):
            acc.append(item[0])
          return acc
        courses_without_file = list(reduce(not_exist_file , list(files.items()), []))
        added_files = get_courses_files(courses=courses_without_file) if len(courses_without_file) > 0 else {}
        for course, file in added_files.items():
          files[course] = file
        teachers = find_teachers(filenames=list(files.values()), surname=name_from_text)
        if(not teachers):
          send_message(message="Преподаватель не найден")
        elif(len(teachers) == 1):
          name = teachers[0]
          send_message(message=f"Показать расписание преподавателя {name}", keyboard=get_teacher_keyboard(teacher=name))
        else: 
          send_message(message="Выберите преподавателя" ,keyboard=get_dif_teachers_keyboard(teachers=teachers))
      elif(category == "TEACHER"):
        kwargs = dict(filenames=list(files.values()), name=teacher_name, type=text)
        schedule = None
        if(text in [BTN_TEXTS["TODAY"], BTN_TEXTS["TOMORROW"]]):
          schedule = get_teacher_day(**kwargs)
        else:
          schedule = get_teacher_week(**kwargs)
        send_message(message=schedule)
      elif(category == "TEACHERS_NAME"):
        send_message(f"Показать расписание преподавателя {teacher_name}", keyboard=get_teacher_keyboard(teacher=teacher_name))
      elif(text == "погода"):
        send_message(message="Показать погоду в Москве", keyboard=get_weather_keyboard())  
      elif(category == "WEATHER"):
        if(text == BTN_TEXTS["NOW"]):
          weather = get_weather_current()
          send_message(message=weather["title"])
          send_message(attachment=get_attachment(picture=[weather["icon"]]))
          send_message(message=weather["text"])
          continue
        elif(text == BTN_TEXTS["FIVE_DAYS"]):
          weather = get_weather_5_days()
          send_message(message=weather["string"])
          send_message(attachment=get_attachment(picture=weather["icons"]))
          send_message(message=weather["temps"])
          continue
        else:
          weather = get_weather_day(type=text)
          send_message(message=weather["title"])
          send_message(attachment=get_attachment(picture=weather["icons"]))
          send_message(message=weather["text"])
      elif(text.startswith("корона")):
        if(text == "корона"):
          res = get_stat_last_10_days()
          print(res)
          send_message(message=res["stat"], keyboard=VkKeyboard.get_empty_keyboard())
          send_message(attachment=get_attachment(picture=res["img"]))
        else:
          query = " ".join(re.split("\s+", text)[1::])  
          stat = get_stat_by_query(query=query)
          send_message(message=stat, keyboard=VkKeyboard.get_empty_keyboard())
      else:
        send_message(message=UNKNOWN)


if __name__ == "__main__":
  main()