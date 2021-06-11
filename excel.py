from functools import reduce
import re
from consts import BTN_TEXTS, DAYS_ON_WEEK_UPPER, MONTHS
from utils import get_current_week, join_lines, get_start_week, get_date_day_month, to_n_items
import xlrd
from datetime import datetime,timedelta

row_teacher = 2

def sort_by_key(object):
  return dict(sorted(object.items(), key=lambda x: x[0]))

def get_teachers_from_cell(row,col,sheet):
  return re.findall("[А-ЯЁ][а-яё]+\s[А-ЯЁ]\.[А-ЯЁ]\.",str(get_cell_value(row=row,col=col, sheet=sheet)))

def get_lessons(lessons):
  return "\n".join(lessons) if len(lessons) > 0 else "—"

def get_excel_data(filename):
  book = xlrd.open_workbook(filename)
  sheet = book.sheet_by_index(0)
  num_cols = sheet.ncols
  num_rows = sheet.nrows
  return (sheet, num_cols, num_rows)

def get_group_col(group, cols_length, sheet):
  group_col = None
  for col in range(cols_length):
    if(str(sheet.cell(rowx=1,colx=col).value).lower() == group.lower()):
      group_col = col
      break
  return group_col

def get_cell_value(row, col, sheet):
  return sheet.cell(rowx=row,colx=col).value

def is_empty(row, col, sheet):
  return not get_cell_value(row=row, col=col, sheet=sheet)

def is_table_cell(row, sheet):
  value = str(get_cell_value(row=row, sheet=sheet, col=4))
  if(value or row < 3):
    return True
  return False

def get_last_row(sheet):
  row = 3
  while(True):
    if(not is_table_cell(row=row,sheet=sheet)):
      return row
    row += 1

def to_schedule(acc, value):
  if(not acc.get(value)):
    acc[value] = "—"
  return acc

def get_rows_for_day(day, col_length, sheet):
  last_row = get_last_row(sheet=sheet)
  rows = []
  for col in range(0, col_length ):
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      day_in_table = None
      for row in range(3, last_row + 1, 1):
        day_in_table = str(get_cell_value(row=row,col=col,sheet=sheet)) or day_in_table
        is_equal = re.compile(day, flags=re.I).findall(day_in_table)
        if(is_equal and not rows):
          rows.append(row)
          rows.append(row)
        elif(is_equal):
          rows[1] = row
      break
  return rows

def schedule_day_to_text(day, date, teacher_name=""):
  teacher_str = f"преподавателя {teacher_name} " if teacher_name else ""
  lessons = [f"Расписание {teacher_str}на {date}"]
  for lesson_num, lesson_name in day.items():
      lessons.append(f"{lesson_num}) {lesson_name}") 
  return join_lines(lessons)

def get_cells_categs(sheet,row,col):
  res = [\
    str(get_cell_value(sheet=sheet,row=row,col=col + i)).split("\n") for i in range(4)\
  ]
  max_count = reduce(lambda acc,arr: max(acc, len(arr)) ,res,0)
  return list(map(lambda x:to_n_items(array=x, n=max_count), res))

def schedule_week_to_text(week, start_week, teacher_name=""):
  days = []
  cur_day = start_week
  for day, lessons in week.items():
    month = MONTHS[cur_day.month]
    num_day = cur_day.day
    days.append(schedule_day_to_text(day=lessons, date=f"{day.lower()} {num_day} {month}", teacher_name=teacher_name))
    cur_day += timedelta(days=1)
    
  return "\n\n".join(days)

def get_schedule_week(filename, group, type):
  current_week = get_current_week()
  if type == BTN_TEXTS["NEXT_WEEK"]:
    current_week += 1
  isEvenWeek = current_week % 2 == 0
  start_week = get_start_week(type=type)
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  group_col = get_group_col(group=group, cols_length=num_cols, sheet=sheet)
  first_lesson_row = None
  last_day_row = None
  days = {}
  if not group_col:
    return "Группа введена не правильно"
  for col in range(group_col - 1, 0, -1):
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      day = None
      lesson = 0
      for row in range(3, num_rows, 1):
        day = str(sheet.cell(rowx=row,colx=col).value) or day
        oddWeek = str(sheet.cell(rowx=row,colx=col + 4).value)
        if(not oddWeek):
          break
        if(not days.get(day)):
          lesson = 0
          if(not first_lesson_row):
            first_lesson_row = row + 0 if isEvenWeek else 1
          days[day] = {}
        if(isEvenWeek and oddWeek == "I" or not isEvenWeek and oddWeek == "II"):
          continue
        lesson += 1
        cell_lessons,cell_types,cell_teachers,cell_cabinets = get_cells_categs(sheet=sheet,row=row, col=group_col)
        lessons_day = []
        for i in range(len(cell_lessons)):
          lesson_name = cell_lessons[i].split(" н.").pop()
          weeks_str = re\
            .compile("^[0-9]+(?:[,][0-9]+)*")\
            .findall(cell_lessons[i])
          weeks = list(map(int, weeks_str[0].split(","))) if len(weeks_str) > 0 else []
          if(not lesson_name.strip(" ") or  not current_week in weeks and len(weeks) > 0 ):
            continue;
          type = cell_types[i]
          teacher = cell_teachers[i]
          cabinet = cell_cabinets[i]
          lessons_day.append(", ".join(list(map(lambda x: x or "—",[lesson_name, type,teacher,cabinet]))))
        days[day][lesson] = get_lessons(lessons=lessons_day)
      break
  text = f"Расписание на {current_week} неделю:\n"
  text += schedule_week_to_text(week=days, start_week=start_week)
  return text

def get_schedule_day(filename, group, type):
  current_week = get_current_week()
  now = datetime.now()
  date = get_date_day_month()
  day_number = now.weekday()
  if(type == BTN_TEXTS["TOMORROW"]):
    day_number += 1
    if(day_number > 6):
      day_number = 0
      current_week += 1
      
  isEvenWeek = current_week % 2 == 0
  if(day_number == 6 and type == BTN_TEXTS["TODAY"]):
    return "Сегодня выходной"
  if(day_number == 6 and type == BTN_TEXTS["TOMORROW"]):
    return "Завтра выходной"
  day_name = DAYS_ON_WEEK_UPPER[day_number]
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  group_col = get_group_col(group=group, cols_length=num_cols, sheet=sheet)
  if not group_col:
    return "Группа введена не правильно"
  schedule = {}
  for col in range(group_col - 1, 0, -1):
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      day = None
      lesson = 0
      lesson_col = col + 1
      is_odd_col = col + 4
      for row in range(3, num_rows, 1):
        day = str(sheet.cell(rowx=row,colx=col).value) or day
        if(day != day_name):
          continue
        oddWeek = str(sheet.cell(rowx=row,colx=is_odd_col).value)
        lesson = int(sheet.cell(rowx=row,colx=lesson_col).value or 0) or lesson
        if(not oddWeek):
          break
        if(isEvenWeek and oddWeek == "I" or not isEvenWeek and oddWeek == "II"):
          continue
        cell_lessons,cell_types,cell_teachers,cell_cabinets = get_cells_categs(sheet=sheet,row=row, col=group_col)
      
        lessons_day = []
        for i in range(len(cell_lessons)):
          lesson_name = cell_lessons[i].split(" н.").pop()
          weeks_str = re\
            .compile("^[0-9]+(?:[,][0-9]+)*")\
            .findall(cell_lessons[i])
          weeks = list(map(int, weeks_str[0].split(","))) if len(weeks_str) > 0 else []
          if(not lesson_name.strip(" ") or not current_week in weeks and len(weeks) > 0 ):
            continue
          type = cell_types[i]
          teacher = cell_teachers[i]
          cabinet = cell_cabinets[i]
          lessons_day.append(", ".join(list(map(lambda x: x or "—",[lesson_name, type,teacher,cabinet]))))
        schedule[lesson] = get_lessons(lessons=lessons_day)
      break
  
  text = schedule_day_to_text(day=schedule, date=date )
  return text

def get_schedule_full_day(filename ,group, day):
  day = day.upper()
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  group_col = get_group_col(group=group, cols_length=num_cols, sheet=sheet)
  if not group_col:
    return "Группа введена не правильно"
  schedule = {"even": {}, "odd": {}}
  for col in range(group_col - 1, 0, -1):
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      day_on_week = None
      lesson = 0
      lesson_col = col + 1
      is_odd_col = col + 4
      for row in range(3, num_rows, 1):
        day_on_week = str(sheet.cell(rowx=row,colx=col).value) or day_on_week
        if day_on_week != day:
          continue
        lesson = int(sheet.cell(rowx=row,colx=lesson_col).value or 0) or lesson
        oddWeek = str(sheet.cell(rowx=row,colx=is_odd_col).value)
        acc = schedule["odd"] if oddWeek == "I" else schedule["even"] 
        cell_lessons,cell_types,cell_teachers,cell_cabinets = get_cells_categs(sheet=sheet,row=row, col=group_col)

        lessons_day = []
        for i in range(len(cell_lessons)):
          lesson_name = cell_lessons[i].split(" н.").pop()
          weeks_str = re\
            .compile("^[0-9]+(?:[,][0-9]+)*")\
            .findall(cell_lessons[i])
          weeks = weeks_str[0] + " н. " if len(weeks_str) else ""
          if(not lesson_name.strip(" ")):
            continue;
          type = cell_types[i]
          teacher = cell_teachers[i]
          cabinet = cell_cabinets[i]
          lessons_day.append(weeks + ", ".join(list(map(lambda x: x or "—",[lesson_name, type,teacher,cabinet]))))
        acc[lesson] = get_lessons(lessons=lessons_day)
      break
  day_lower = day.lower()
  text = ""
  text += schedule_day_to_text(day=schedule["odd"], date = f"нечётный {day_lower}" )
  text += "\n\n"
  text += schedule_day_to_text(day=schedule["even"], date = f"чётный {day_lower}" )
  return text

def find_teachers_in_one_file(filename, surname):
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  last_row = get_last_row(sheet=sheet)
  teachers = []
  for col in range(num_cols):
    value = get_cell_value(row=row_teacher, col=col, sheet=sheet)
    if(not(re.compile("ФИО преподавателя").findall(str(value)))):
      continue
    for row in range(3, last_row):
      # teacher_names = re.split("[/,\r\n][\s]*",str(get_cell_value(row=row,col=col, sheet=sheet)))
      teacher_names = get_teachers_from_cell(row=row,col=col, sheet=sheet)
      for value in teacher_names:
        if not value:
          continue;
        teacher_name = value.split(" ")[0]
        if(not re.compile(f"^{teacher_name}$", flags=re.I).findall(surname)):
          continue
        teachers.append(value)
  return teachers

def get_teacher_day_in_file(filename, name, schedule, day_name, isEvenWeek):
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  start, end = get_rows_for_day(day=day_name, col_length=num_cols, sheet=sheet)
  group_name = None
  lesson = 0
  lesson_col = None
  is_odd_col = None
  for col in range(num_cols):
    value = get_cell_value(row=row_teacher, col=col, sheet=sheet)
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      lesson_col = col + 1
      is_odd_col = col + 4
    if(not(re.compile("ФИО преподавателя").findall(str(value)))):
      continue
    group_name = str(get_cell_value(sheet=sheet,col=col-2, row=row_teacher-1))
    for row in range(start, end):
      lesson = int(get_cell_value(row=row,col=lesson_col, sheet=sheet) or 0) or lesson
      oddWeek = get_cell_value(row=row,col=is_odd_col, sheet=sheet)
      if(isEvenWeek and oddWeek == "I" or not isEvenWeek and oddWeek == "II"):
        continue
      teachers = get_teachers_from_cell(row=row,col=col, sheet=sheet )
      if(name not in teachers):
        continue
      idx = teachers.index(name)
    
      cell_lessons,cell_types,_,cell_cabinets = get_cells_categs(sheet=sheet,row=row, col=col - 2)
    
      result = ", ".join([cell_lessons[idx].split(" н.").pop(),cell_types[idx],group_name,cell_cabinets[idx]])
      schedule[lesson] = result
  lessons = [i for i in range(1, lesson + 1)]
  schedule = reduce(to_schedule,lessons,schedule)
  return schedule

def get_teacher_week_in_file(filename,name,schedule, isEvenWeek):
  sheet, num_cols, num_rows = get_excel_data(filename=filename)
  group_name = None
  day = None
  lesson = 0
  day_col = None
  lesson_col = None
  is_odd_col = None
  for col in range(num_cols):
    value = get_cell_value(row=row_teacher, col=col, sheet=sheet)
    if(str(sheet.cell(rowx=1,colx=col).value) == "День недели"):
      day_col = col
      lesson_col = col + 1
      is_odd_col = col + 4
    if(not(re.compile("ФИО преподавателя").findall(str(value)))):
      continue
    group_name = str(get_cell_value(sheet=sheet,col=col-2, row=row_teacher-1))
    for row in range(3, get_last_row(sheet=sheet)):
      day = str(get_cell_value(row=row,col=day_col, sheet=sheet)) or day
      lesson = int(get_cell_value(row=row,col=lesson_col, sheet=sheet) or 0) or lesson
      oddWeek = get_cell_value(row=row,col=is_odd_col, sheet=sheet)
      if(isEvenWeek and oddWeek == "I" or not isEvenWeek and oddWeek == "II"):
        continue
      teachers = get_teachers_from_cell(row=row,col=col, sheet=sheet )
      if(name not in teachers):
        continue
      idx = teachers.index(name)
    
      cell_lessons,cell_types,_,cell_cabinets = get_cells_categs(sheet=sheet,row=row, col=col - 2)
      result = ", ".join([cell_lessons[idx].split(" н.").pop(),cell_types[idx],group_name,cell_cabinets[idx]])
      schedule[day][lesson] = result
  lessons = [i for i in range(1, lesson + 1)]
  for day in schedule.keys():
    schedule[day] = reduce(to_schedule,lessons,schedule[day])
  return schedule


def find_teachers(filenames, surname):
  teachers = []
  for filename in filenames:
    teachers.extend(find_teachers_in_one_file(filename=filename, surname=surname))
  return list(set(teachers))

def get_teacher_day(filenames, name, type):
  current_week = get_current_week()
  day_number = datetime.now().weekday()
  if(type == BTN_TEXTS["TOMORROW"]):
    day_number += 1
    if(day_number > 6):
      day_number = 0
      current_week += 1
  isEvenWeek = current_week % 2 == 0
  if(day_number == 6 and type == BTN_TEXTS["TODAY"]):
    return "Сегодня выходной"
  if(day_number == 6 and type == BTN_TEXTS["TOMORROW"]):
    return "Завтра выходной"
  day_name = DAYS_ON_WEEK_UPPER[day_number]
  schedule = {}
  for filename in filenames:
    schedule = get_teacher_day_in_file(filename=filename, name=name, schedule=schedule, day_name=day_name, isEvenWeek=isEvenWeek)
  full_schedule = sort_by_key(schedule)
  text = schedule_day_to_text(day=full_schedule, date=get_date_day_month(), teacher_name=name)
  return text
  
def get_teacher_week(filenames, name, type):
  current_week = get_current_week()
  if(type == BTN_TEXTS["NEXT_WEEK"]):
    current_week += 1
  schedule = dict(list(map(lambda x: (x, {}), list(DAYS_ON_WEEK_UPPER.values()))))
  isEvenWeek = current_week % 2 == 0
  for filename in filenames:
    schedule = get_teacher_week_in_file(filename=filename,name=name,schedule=schedule, isEvenWeek=isEvenWeek)
  for day in schedule.keys():
    schedule[day] = sort_by_key(schedule[day])
  text = schedule_week_to_text(start_week=get_start_week(type=type), week=schedule, teacher_name=name)
  return text
  
