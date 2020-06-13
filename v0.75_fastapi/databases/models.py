from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class City(Base):
    __tablename__ = "city"
    id = Column(String, primary_key=True, index=True)
    cityEn = Column(String)
    cityEn = Column(String)
    cityZh = Column(String)
    provinceEn = Column(String)
    provinceZh = Column(String)
    countryEn = Column(String)
    countryZh = Column(String)
    leaderEn = Column(String)
    leaderZh = Column(String)
    lat = Column(String)
    lon = Column(String)

    items = relationship("Weather", back_populates="owner")

class Weather(Base):
    __tablename__ = "weather"

    id = Column(String, primary_key=True, index=True, ForeignKey("city.id"))
    cityid = "101120101",
    update_time = "20:55",
    wea = "晴",
    wea_img = "qing",
    tem = "11",
    tem_day = "17",
    tem_night = "7",
    win = "东南风 ",
    win_speed = "1级",
    win_meter = "小于12km/h",
    air = "73"
    owner = relationship("City", back_populates="items")
