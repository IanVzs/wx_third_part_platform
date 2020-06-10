"""
后台任务触发接口
相关该类统一处理方法在routers中进行定义
"""
from fastapi import BackgroundTasks

from routers import rBGTask_API
from task_background.weather import get_save_weather

@rBGTask_API.post("/task/weather/{task_id}")
async def task_weather(task_id: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(get_save_weather, task_id)
    return {"message": "success"}

