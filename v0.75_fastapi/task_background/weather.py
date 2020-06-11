"""
定时任务相关实现
"""
import json

def get_save_weather(task_id):
    cityid_dict = {}
    with open("task_background/city.json") as city_file:
        cityid_dict = json.load(city_file)
    for city_info in cityid_dict:
        cityid = city
    # TODO
    return 1
