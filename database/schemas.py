import datetime
import uuid

import pydantic


class ChildBase(pydantic.BaseModel):
    name: str
    sur_name: str
    birth_day: datetime.date


class Child(ChildBase):
    child_id: uuid.UUID
    created_at: datetime.datetime

    class Config:
        orm_mode = True
