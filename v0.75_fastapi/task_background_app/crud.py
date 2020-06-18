from sqlalchemy.orm import Session

from . import models, schemas


def get_city(db: Session, city_id: int):
    return db.query(models.City).filter(models.City.id == city_id).first()


def get_city_by_id(db: Session, _id: str):
    return db.query(models.City).filter(models.City.id == _id).first()


def get_citys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.City).offset(skip).limit(limit).all()


def create_city(db: Session, city: schemas.CityCreate):
    # fake_hashed_password = city.password + "notreallyhashed"
    # db_city = models.City(id=city.id, hashed_password=fake_hashed_password)
    db_city = models.City(**city.dict())
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


def get_weathers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Weather).offset(skip).limit(limit).all()


def create_city_weather(db: Session, weather: schemas.WeatherCreate, city_id: int):
    db_weather = models.Weather(**weather.dict(), id=city_id)
    db.add(db_weather)
    db.commit()
    db.refresh(db_weather)
    return db_weather
