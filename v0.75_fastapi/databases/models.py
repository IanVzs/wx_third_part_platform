from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
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

    weathers = relationship("Weather", back_populates="owner")

class Weather(Base):
    __tablename__ = "weather"

    id = Column(String, primary_key=True, index=True, ForeignKey("city.id"))
    update_time = Column(Integer)
    wea = Column(String)
    tem = Column(Float)
    tem_day = Column(Float)
    tem_night = Column(Float)
    win = Column(String)
    win_speed = Column(Integer)
    win_meter = Column(String)
    air = Column(Integer)
    
    owner = relationship("City", back_populates="weathers")
