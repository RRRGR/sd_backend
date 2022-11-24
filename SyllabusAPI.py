from fastapi import FastAPI, HTTPException, status, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import os
import pymysql.cursors
from pydantic import BaseModel
from typing import List
import uvicorn
import shutil

class courseModel(BaseModel):
  rgno: str|None
  season: str|None
  ay: str|None
  no: str|None
  cno: str|None
  lang: str|None
  section: str|None
  e: str|None
  j: str|None
  schedule: str|None
  room: str|None
  comment: str|None
  maxnum: str|None
  instructor: str|None
  unit: str|None
  deleted: str|None

class searchModel(BaseModel):
  courses: List[courseModel]
  total: int = 1

def get_from_id(year: str, courseId: str):
  connection = pymysql.connect(host='localhost',
                              user='USERNAME',
                              password='PASSWORD',
                              database='syllabus_icu',
                              cursorclass=pymysql.cursors.DictCursor)

  with connection:
    with connection.cursor() as cursor:
      if int(year) > 2022 or int(year) < 2016:
        return []
      sql = f"SELECT * FROM `icu_{year}` WHERE `rgno`={courseId}"
      cursor.execute(sql)
      result = cursor.fetchall()
      return result

def search_courses(year:str, season:str|None, period:str|None, day:str|None):
  

  connection = pymysql.connect(host='localhost',
                              user='USERNAME',
                              password='PASSWORD',
                              database='syllabus_icu',
                              cursorclass=pymysql.cursors.DictCursor)

  with connection:
    with connection.cursor() as cursor:
      if int(year) > 2022 or int(year) < 2016:
        return []

      if season is None:
        sql_season = ""
      else:
        sql_season = f"`season`='{season}'"
      if period is None:
        sql_period = ""
      else:
        sql_period = f"`schedule` like '%{period}%'"
        if len(sql_season) > 0:
          sql_period = "AND" + sql_period
      if day is None:
        sql_day = ""
      else:
        sql_day = f"`schedule` like '%{day}%'"
        if len(sql_period) > 0:
          sql_day = "AND" + sql_day

      if len(sql_season)==0 and len(sql_period)==0 and len(sql_day)==0:
        where = ""
      else:
        where = "WHERE"

      sql = f"SELECT * FROM `icu_{year}` {where} {sql_season} {sql_period} {sql_day}"
      cursor.execute(sql)
      result = cursor.fetchall()
      return result

def insert_imgpath(courseId:str, imgpath:str):
  connection = pymysql.connect(host='localhost',
                              user='USERNAME',
                              password='PASSWORD',
                              database='images',
                              cursorclass=pymysql.cursors.DictCursor)

  with connection:
    with connection.cursor() as cursor:
      sql = """INSERT INTO `imgs` (`rgno`, `path`) 
      VALUES (%s, %s)"""
      cursor.execute(sql, (courseId, imgpath))
    connection.commit()

def get_imgpath(courseId: str):
  connection = pymysql.connect(host='localhost',
                              user='USERNAME',
                              password='PASSWORD',
                              database='images',
                              cursorclass=pymysql.cursors.DictCursor)

  with connection:
    with connection.cursor() as cursor:
      sql = f"SELECT * FROM `imgs` WHERE `rgno`={courseId}"
      cursor.execute(sql)
      result = cursor.fetchall()
      return result


app = FastAPI()

origins = [
  'http://localhost:3000'
]
app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=['GET'],
  allow_headers=['*']
)


@app.get("/syllabus/{year}/courses/{courseId}", response_model=courseModel)
def get_course(year: str, courseId: str):

  """

  Get a course by id

  - **year** 2017-2022
  - **courseID** rgno

  """
  
  info = get_from_id(year, courseId)
  if len(info) == 0:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Course with id {courseId} in {year} academic year not found"
    )
  return info[0]

@app.get("/syllabus/{year}/search", response_model=searchModel)
def get_search(year: str, season:str|None=None, period:str|None=None, day:str|None=None):

  """
  
  Search courses

  - **year** 2017-2022
  - **season** Spring, Autumn, Winter
  - **period**1-8
  - **day** M, TU, W, TH, F, SA 

  """

  courses = search_courses(year, season, period, day)
  if len(courses) == 0:
    raise HTTPException(
      status_code=status.HTTP_404_NOT_FOUND,
      detail=f"Courses not found"
    )
  response_dict = {
    "courses": courses,
    "total": len(courses)
  }
  return response_dict

@app.get("/images/{courseId}")
def get_image(courseId: str):

  imgpaths = get_imgpath(courseId)
  # if len(imgpaths) == 0:
  #   raise HTTPException(
  #     status_code=status.HTTP_404_NOT_FOUND,
  #     detail="Images not found"
  #   )
  print(imgpaths)
  response_dict = {
    "imgpaths": imgpaths,
    "total": len(imgpaths)
  }
  return response_dict


@app.post("/upload/{courseId}")
def post_uploadfile(courseId: str, upload_file: UploadFile):

  imgdir = f"SOMETHING/images/{courseId}"
  if not os.path.isdir(imgdir):
    os.makedirs(imgdir)

  imgpath = f'images/{courseId}/{upload_file.filename}'

  with open(f'SOMETHING/public/{imgpath}', 'wb+') as buffer:
      shutil.copyfileobj(upload_file.file, buffer)

  insert_imgpath(courseId, imgpath)  

  return {
      'filename': imgpath,
      'type': upload_file.content_type
  }

if __name__ == "__main__":
  uvicorn.run(app, host="0.0.0.0", port=8000)