"""
test task_background_app 的逻辑

使用: unittest
    mock.patch.object: Mock 一个类, 后接方法
    mock.patch: Mock 一个方法, 按路径

    @mock.patch("databases.wx_service.get_user_base_info")
    @mock.patch.object(wx_service.WeChat_OAP, "send_template_msg")
    def test_create_weawarning(self, mock_send_template_msg, mock_get_user_base_info):
        # 装饰器生效从内到外, 传入参数顺序, 从左到右
        pass
        mock_send_template_msg.return_value = ''/{}/[]/() 皆可  设定mock返回值
        mock_get_user_base_info.side_effect = [''/{}/[]/(), ''/{}/[]/()] 设定每次调用mock函数依次返回返回值
"""

import sys
sys.path.append("/home/ubuntu/wx_third_part_platform/v0.75_fastapi")
# 地址测试的话需更换为实际目录地址
import unittest
from unittest import mock

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from fastapi import Depends, FastAPI, HTTPException

from task_background_app import crud, models, schemas, task_worker, database


engine = create_engine(database.SQLALCHEMY_DATABASE_URL+"_test")

def get_test_db():
    db = Session(bind=engine)
    # db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_weawarning(weawarning: schemas.WeatherWarningCreate):
    db = get_test_db()

    db_weawarning = crud.get_weawarning_by_id(db, _id=weawarning.id)
    if db_weawarning:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_weawarning(db=db, warning=weawarning)


class TestProducer(unittest.TestCase):
    def setUp(self):
        self.aaa = type
        pass

    def test_create_weawarning(self):
        """测试创建天气预警"""
        db = None
        warning = {}
        result = {"sign": 1, "msg": ''}

        weawarning = schemas.WeatherWarningCreate(id = '', dt= '', hourType= 24, stationId= 221, areaId= '123', stationName= "站点", lon= 12.1, lat= 21.2, signalType= '暴雨', signalLevel= '黄色', issueTime= '2020-01-02 12=12=12', relieveTime= '2020-01-02 12=12=12', issueContent= '你好你好\(@^0^@)/你好')
        self.assertEqual(create_weawarning(weawarning), result)


if __name__ == '__main__':
    unittest.main()
