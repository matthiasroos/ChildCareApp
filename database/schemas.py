import datetime
import uuid

import pydantic


class Child(pydantic.BaseModel):
    child_id: uuid.UUID
    name: str
    sur_name: str
    birth_day: datetime.date
    created_at: datetime.datetime

    class Config:
        orm_mode = True
