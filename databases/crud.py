from sqlalchemy.orm import Session

from . import models, schemas


def get_city_by_city_id(db: Session, city_id: str):
    return db.query(models.City).filter(models.City.id == city_id).first()


def get_citys(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.City).offset(skip).limit(limit).all()


def create_city(db: Session, city: schemas.CityCreate):
    # fake_hashed_password = city.password + "notreallyhashed"
    db_city = models.City(id=city.id)
    db.add(db_city)
    db.commit()
    db.refresh(db_city)
    return db_city


# def get_weathers(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(models.Item).offset(skip).limit(limit).all()


def create_city_weather(db: Session, wearth: schemas.WeatherCreate, city_id: int):
    db_wearth = models.Wearth(**wearth.dict(), id=city_id)
    db.add(db_wearth)
    db.commit()
    db.refresh(db_wearth)
    return db_wearth