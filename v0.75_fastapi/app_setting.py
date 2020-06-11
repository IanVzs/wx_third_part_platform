from fastapi import FastAPI

from routers import bg_task, wx_api

def creat_app():
    app = FastAPI()
    app.include_router(wx_api.router)
    app.include_router(bg_task.router)
    return app

"""
解决跨域/官方demo姑且放在这儿
from starlette.middleware.cors import CORSMiddleware

origins = [
    "http://localhost",
    "http://localhost:8080",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
"""
