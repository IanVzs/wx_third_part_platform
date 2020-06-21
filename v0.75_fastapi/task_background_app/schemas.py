from typing import List

from pydantic import BaseModel


class WeatherBase(BaseModel):
    id: int
    utime: int
    wea: str 
    tem: float
    win: str
    win_speed: int
    win_meter: str
    air: int


class WeatherCreate(WeatherBase):
    pass


class Weather(WeatherBase):
    id: int

    class Config:
        orm_mode = True


class CityBase(BaseModel):
    id: str
    cityEn: str
    cityZh: str
    provinceEn: str
    provinceZh: str
    countryEn: str
    countryZh: str
    leaderEn: str
    leaderZh: str
    lat: str
    lon: str


class CityCreate(CityBase):
    pass


class City(CityBase):
    id: str
    weathers: List[Weather] = []

    class Config:
        orm_mode = True
