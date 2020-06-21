import asyncio
import aiohttp


async def fetch(session, url, data):
    async with session.get(url, params=data) as response:
        return await response.json()

async def request_apis(url, datas, method="GET"):
    task_list = []
    async with aiohttp.ClientSession() as session:
        for data in datas:
            req = fetch(session, url, data)
            task = asyncio.create_task(req)
            task_list.append(task)
        await asyncio.gather(*task_list)
    return task_list

def get_all_weather(url, datas):
    weather_res = asyncio.run(request_apis(url, datas))
    results = []
    for i in weather_res:
        result = i.result()
        results.append(result)
    return results

