import logging
import logging.config

logging.config.fileConfig('logging.ini')

# create wea logger
weatherLog = logging.getLogger('weatherLog')
debugLog = logging.getLogger('debugLog')


def deal_data(data):
    # TODO 随后改成装饰器
    try:
        from lib import template
        data = template.deal_data(data)
    except:
        pass
    return data


def record_weather_msg(data) -> bool:
    sign = False
    weatherLog.info(f"{data}")
    return sign

def record_weather_warning(data) -> bool:
    sign = False
    debugLog.debug(f"{data}")
    data = deal_data(data)
    if isinstance(data, list):
        for i in data:
            i = ','.join(i)
            weatherLog.info(i)
    return sign

def debug(data):
    debugLog.debug(f"{data}")
