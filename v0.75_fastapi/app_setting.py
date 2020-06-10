from fastapi import FastAPI

from APIRouters.wx_api import rWX_API
from APIRouters.bg_task import rBGTask_API

def creat_app():
    app = FastAPI()
    app.include_router(rWX_API)
    app.include_router(rBGTask_API)
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
