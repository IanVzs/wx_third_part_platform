from typing import List, Optional

from pydantic import BaseModel


class Text(BaseModel):
    content: str

class MsgBody(BaseModel):
    touser: str
    msgtype: str
    text: Optional[Text] = None
    tax: Optional[float] = None

class MsgRep(BaseModel):
    msg: str
    sign: int
