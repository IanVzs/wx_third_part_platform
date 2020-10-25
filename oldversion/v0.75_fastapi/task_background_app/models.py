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
    
    weawarnings = relationship("WeatherWarning", back_populates="city_info")
    weathers = relationship("Weather", back_populates="owner")


class Weather(Base):
    __tablename__ = "weathers"

    id = Column(Integer, ForeignKey("citys.id"), primary_key=True, index=True)
    utime = Column(Integer) # 更新时间
    wea = Column(String(12)) # 天气描述
    nwea = Column(String(12)) # 天气描述
    tem_max = Column(Float(4))
    tem_min = Column(Float(4))
    tem = Column(Float(4)) # 温度
    win = Column(String(12)) # 风向
    win_speed = Column(Integer) # 公里/小时
    win_angle = Column(Integer) # 角度
    hum = Column(Integer) # 湿度
    cloud = Column(Integer) # 云量
    vis = Column(Integer) # 可见度  公里
    water = Column(Integer) # 降水量
    pwater = Column(Integer) # 降水概率
    uv_index = Column(Integer) # 紫外线指数
    

    owner = relationship("City", back_populates="weathers")


class WeatherWarning(Base):
    __tablename__ = "weatherWarnings"

    id = Column(Integer, primary_key=True, index=True)
    dt = Column(String(19))
    hourType = Column(Integer)
    stationId = Column(Integer)
    areaId = Column(String, ForeignKey("citys.id"))
    stationName = Column(String(36))
    lon = Column(Float(4))
    lat = Column(Float(4))
    signalType = Column(String(24))
    signalLevel = Column(String(6))
    issueTime = Column(String(19))
    relieveTime = Column(String(19))
    issueContent = Column(String(512))

    city_info = relationship("City", back_populates="weawarnings")
