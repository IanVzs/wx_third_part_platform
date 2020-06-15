"""
定时任务相关实现
"""
import json
from fastapi import Depends
from sqlalchemy.orm import Session

from databases import crud, models, schemas, database

models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_save_weather(task_id):
    cityid_dict = {}
    if task_id:
        import pdb; pdb.set_trace()
        db = Depends(get_db)
        citys = crud.get_citys(db, skip=0, limit=100)
    else:
        with open("task_background/city.json") as city_file:
            cityid_dict = json.load(city_file)
        for city_info in cityid_dict:
            cityid = city
    return 1
