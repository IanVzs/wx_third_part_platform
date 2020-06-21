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
