import asyncio
import aiohttp
import xmltodict


async def fetch(session, url, data):
    async with session.get(url, params=data) as response:
        return await response.json()

async def fetch_xml(session, url, data):
    async with session.get(url, params=data) as response:
        # res = await response.content.read(100)
        res = await response.content.read()
        result = xmltodict.parse(res)
        return result

FETCH_MODE_DICT = {"xml": fetch_xml}
async def to_nothing(*args, **kwargs):
    return ''

async def request_api(url, data, method="GET", resp_type="xml"):
    async with aiohttp.ClientSession() as session:
        res = await (FETCH_MODE_DICT.get(resp_type) or to_nothing)(session, url, data)
    return res

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

def get_all_weather_warning(url, data):
    weather_res = asyncio.run(request_api(url, data))
    return weather_res
