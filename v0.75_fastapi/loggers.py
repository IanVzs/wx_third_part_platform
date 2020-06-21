import logging
import logging.config

logging.config.fileConfig('logging.ini')

# create wea logger
weatherLog = logging.getLogger('weatherLog')



def record_weather_msg(data) -> bool:
    sign = False
    weatherLog.info(f"{data}")
    return sign
