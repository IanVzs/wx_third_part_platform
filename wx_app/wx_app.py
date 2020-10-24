import json
from typing import List

from fastapi import Depends, FastAPI, HTTPException, BackgroundTasks

from route_class import TimedRoute, APIRouter
from . import schemas

router = APIRouter(route_class=TimedRoute)

@router.post("/send_msg/", response_model=schemas.MsgRep)
def create_city(type: str, data: schemas.MsgBody):
    if type:
        raise HTTPException(status_code=400, detail="Email already registered")
    rlt = schemas.MsgRep(sign=1, msg='')
    return rlt


@router.get("/wx_api/bgt_demo/")
async def creat_task(task_id: str = 'wearth_forecast', background_tasks: BackgroundTasks = None):
    task_status = {"status": 1}
    if task_worker.in_todo_list(task_id):
        citys = crud.get_citys(db, skip=0, limit=4000)
        background_tasks.add_task(task_worker.do_work, task_id, citys)
        num = len(citys)
        task_status = {"status": 0, "msg": f"task: {task_id}, num: {num}, set success."}
    else:
        task_status["msg"] = f"task: {task_id or None}, set failed."
    return task_status
