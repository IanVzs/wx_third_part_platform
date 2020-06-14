from typing import List
from pydantic import BaseModel


class WeatherBase(BaseModel):
    title: str
    description: str = None
    update_time = int
    wea = str
    tem = float
    tem_day = float
    tem_night = float
    win = str
    win_speed = int
    win_meter = str
    air = int


class WeatherCreate(WeatherBase):
    pass


class Weather(WeatherBase):
    id: str

    class Config:
        orm_mode = True


class CityBase(BaseModel):
    cityEn = str
    cityEn = str
    cityZh = str
    provinceEn = str
    provinceZh = str
    countryEn = str
    countryZh = str
    leaderEn = str
    leaderZh = str
    lat = str
    lon = str


class CityCreate(CityBase):
    pass


class City(CityBase):
    id: str
    is_active: bool
    Weathers: List[Weather] = []

    class Config:
        orm_mode = True
