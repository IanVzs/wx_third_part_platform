from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float
from sqlalchemy.orm import relationship

from .database import Base


class City(Base):
    __tablename__ = "citys"

    id = Column(String, primary_key=True, index=True)
    cityEn = Column(String(32))
    cityZh = Column(String(32))
    provinceEn = Column(String(32))
    provinceZh = Column(String(32))
    countryEn = Column(String(32))
    countryZh = Column(String(32))
    leaderEn = Column(String(32))
    leaderZh = Column(String(32))
    lat = Column(String(32))
    lon = Column(String(32))
    
    weathers = relationship("Weather", back_populates="owner")


class Weather(Base):
    __tablename__ = "weathers"

    id = Column(Integer, ForeignKey("citys.id"), primary_key=True, index=True)
    update_time = Column(Integer)
    wea = Column(String(12))
    tem = Column(Float(4))
    tem_day = Column(Float(4))
    tem_night = Column(Float(4))
    win = Column(String(16))
    win_speed = Column(Integer)
    win_meter = Column(String(12))
    air = Column(Integer)

    owner = relationship("City", back_populates="weathers")
