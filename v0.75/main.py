import aiohttp
from fastapi import FastAPI

app = FastAPI()

"""
解决跨域/非官方方案姑且一看
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

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

@app.get("/")
async def read_main():
    async with aiohttp.ClientSession() as session:
        a = await fetch(session, 'http://127.0.0.1')
    return {"msg": "wx_third_part_platform v0.75"}

@app.get("/favicon.ico")
async def favicon_ico():
    return "hi"
