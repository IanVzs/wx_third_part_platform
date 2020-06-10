"""
定时任务相关实现
"""
import json

def get_save_weather(task_id):
    cityid_dict = {}
    with open("task_background/city.json") as city_file:
        cityid_dict = json.load(city_file)
    # TODO
    return 1
