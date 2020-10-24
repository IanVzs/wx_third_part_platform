from typing import List

from pydantic import BaseModel


class Text:
    content: str

class MsgBody(BaseModel):
    touser: str
    msgtype: str
    text: Text = {}

class MsgRep(BaseModel):
    msg: str
    sign: int