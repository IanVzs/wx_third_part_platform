from typing import List

from pydantic import BaseModel


class WeatherWarningBase(BaseModel):
    id: str
    dt: str
    hourType: int
    stationId: int
    areaId: str
    stationName: str
    lon: float
    lat: float
    signalType: str
    signalLevel: str
    issueTime: str
    relieveTime: str
    issueContent: str


class WeatherWarningCreate(WeatherWarningBase):
    pass


class WeatherWarning(WeatherWarningBase):
    id: str
    class Config:
        orm_mode = True

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
    weatherWarning: List[WeatherWarning
] = []

    class Config:
        orm_mode = True

