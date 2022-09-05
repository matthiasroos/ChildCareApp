import datetime
import typing
import uuid

import pydantic


class User(pydantic.BaseModel):
    user_name: str
    salt: str
    hashed_password: str


class ChildBase(pydantic.BaseModel):
    name: str
    sur_name: str
    birth_day: datetime.date


class Child(ChildBase):
    child_id: uuid.UUID
    created_at: datetime.datetime

    class Config:
        orm_mode = True


class ChildUpdate(pydantic.BaseModel):
    name: typing.Optional[str] = pydantic.Field(None)
    sur_name: typing.Optional[str] = pydantic.Field(None)
    birth_day: typing.Optional[datetime.date] = pydantic.Field(None)

    @pydantic.root_validator()
    def is_at_least_one_param_given(cls, values):
        """one param must be at least given for the update"""
        if (values.get('name') is None) and (values.get('sur_name') is None) and \
           (values.get('birth_day') is None):
            raise ValueError('One parameter must be at least given for the update')
        return values


class CaretimeBase(pydantic.BaseModel):
    caretime_id: uuid.UUID
    child_id: uuid.UUID
    start_time: typing.Optional[datetime.datetime]
    stop_time: typing.Optional[datetime.datetime]


class Caretime(CaretimeBase):
    created_at: datetime.datetime
    modified_at: datetime.datetime

    class Config:
        orm_mode = True
