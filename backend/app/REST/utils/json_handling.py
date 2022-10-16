import json
import typing

import backend.database.schemas


def serialize_result(result: typing.Union[typing.Any, typing.List[typing.Any]]):
    """

    :param result:
    :return:
    """

    # Pydantic has currently no functionality to directly create a jsonable dict,
    # workaround according to the following discussion:
    # https://stackoverflow.com/questions/65622045/pydantic-convert-to-jsonable-dict-not-full-json-string
    if isinstance(result, list):
        result_ = [json.loads(backend.database.schemas.Child.from_orm(r).json()) for r in result]
    else:
        result_ = json.loads(backend.database.schemas.Child.from_orm(result).json())
    return result_
