from selenium import webdriver
from selenium.webdriver.support.select import Select
import time
from bs4 import BeautifulSoup
import chromedriver_binary
import pymysql.cursors

def get_syllabus(year: str) -> str:
  options = webdriver.ChromeOptions()
  options.add_argument('--headless')
  options.add_argument('--no-sandbox')
  options.add_argument('--disable-dev-shm-usage')
  driver = webdriver.Chrome('chromedriver', options=options)
  driver.get('https://campus.icu.ac.jp/icumap/ehb/SearchCO.aspx')
  driver.find_element('id','username_input').send_keys('USERNAME')
  driver.find_element('id','password_input').send_keys('PASSWORD')
  driver.find_element('id','login_button').click()
  time.sleep(3)
  Select(driver.find_element('id','ctl00_ContentPlaceHolder1_ddl_year')).select_by_value(year)

  Select(driver.find_element('id','ctl00_ContentPlaceHolder1_ddlPageSize')).select_by_value('ALL')
  driver.find_element('id','ctl00_ContentPlaceHolder1_btn_search').click()
  time.sleep(7)
  elem_table = driver.find_element('id','ctl00_ContentPlaceHolder1_grv_course')
  html = elem_table.get_attribute('outerHTML')
  return html

def get_id_param(id: str) -> str:
  reversed = id[::-1]
  param = ''
  for _ in reversed:
    if _ == '_':
      break
    param += _
    
  return param[::-1]

def syllabus_to_db(html: str, year: str):
  soup = BeautifulSoup(html, 'html.parser')
  spans = soup.find_all('span')

  for span in spans:
    param = get_id_param(span['id'])
    if param == 'rgno':
      courseinfo_list = []
    if param != "Label1":
      courseinfo_list.append(span.string)
    if param == 'unit':
      if len(span.parent['class']) > 0 :
      #if span.parent['class'][0] == 'word_line_through':
        courseinfo_list.append('true')
      else:
        courseinfo_list.append('false')
      syllabus2db(year, courseinfo_list)

def syllabus2db(year, infolist):
  connection = pymysql.connect(host='localhost',
                             user='USERNAME',
                             password='PASSWORD',
                             database='syllabus_icu',
                             cursorclass=pymysql.cursors.DictCursor)
  
  infotuple = tuple(infolist)
  rgno = infotuple[0]

  with connection:
    with connection.cursor() as cursor:
      if int(year) > 2022 or int(year) < 2016:
        return []
      sql = f"SELECT * FROM `icu_{year}` WHERE `rgno`={rgno}"
      cursor.execute(sql)
      result = cursor.fetchall()

  infolist_before = list(result[0].values())
  connection.ping()
  if len(result) == 0:
    with connection:
        with connection.cursor() as cursor:
            sql = """INSERT INTO `icu_{}` (`rgno`, `season`, `ay`, `no`, `cno`, `lang`, `section`, `e`, `j`, `schedule`, `room`, `comment`, `maxnum`, `instructor`, `unit`, `deleted`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""".format(year)
            cursor.execute(sql, infotuple)
        connection.commit()
  elif infolist_before != infolist:
    with connection:
        with connection.cursor() as cursor:
            sql = """UPDATE `icu_{}` 
            SET `season`=%s,`ay`=%s,`no`=%s,`cno`=%s,`lang`=%s,`section`=%s,`e`=%s,`j`=%s,`schedule`=%s,`room`=%s,`comment`=%s,`maxnum`=%s,`instructor`=%s,`unit`=%s,`deleted`=%s
            WHERE `rgno` = {}
            """.format(year, rgno)
            cursor.execute(sql, infotuple[1:])
        connection.commit()

def make_db(year: str) -> None:
  html = get_syllabus(year)
  syllabus_to_db(html, year)

for year in ["2022", "2021", "2020", "2019", "2018", "2017"]:
  make_db(year)
  print(year)
