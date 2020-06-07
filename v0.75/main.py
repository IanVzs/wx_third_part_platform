import aiohttp

from app_setting import app

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
