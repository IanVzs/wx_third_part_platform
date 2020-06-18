"""后台任务"""
import json


global TASK_DATA
def get_task_json():
    global TASK_DATA
    with open("./task_background_app/task_config.json") as api_file:
        TASK_DATA = json.load(api_file)

get_task_json()
print(TASK_DATA)

def get_city_weather(citys: iter):
    """实况天气"""
    for i in citys:
        print("######", i)
        print("######", i.id, i.cityZh)
        break
    return True

def in_todo_list(task_id):
    global TASK_DATA
    if task_id in TASK_DATA:
        return True
    else:
        return False

def to_nothing(*args, **kwargs):
    pass

def do_work(task_id: str, citys: iter):
    task_config = globals()["TASK_DATA"][task_id]
    worker_name = task_config.get("woker") or ''
    worker = globals().get(worker_name) or to_nothing
    worker(citys)
    return True
