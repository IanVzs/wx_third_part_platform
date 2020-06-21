import json
from typing import List

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from route_class import TimedRoute, APIRouter
from . import crud, models, schemas, task_worker
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

router = APIRouter(route_class=TimedRoute)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/citys/", response_model=schemas.City)
def create_city(city: schemas.CityCreate, db: Session = Depends(get_db)):
    db_city = crud.get_city_by_id(db, _id=city.id)
    if db_city:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_city(db=db, city=city)


@router.get("/citys/", response_model=List[schemas.City])
def read_citys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    citys = crud.get_citys(db, skip=skip, limit=limit)
    return citys


@router.get("/task/weather/")
async def creat_task(task_id: str = 'wearth_forecast', db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    task_status = {"status": 1}
    if task_worker.in_todo_list(task_id):
        citys = crud.get_citys(db, skip=0, limit=4000)
        background_tasks.add_task(task_worker.do_work, task_id, citys)
        num = len(citys)
        task_status = {"status": 0, "msg": f"task: {task_id}, num: {num}, set success."}
    else:
        task_status["msg"] = f"task: {task_id or None}, set failed."
    return task_status
