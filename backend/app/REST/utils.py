import json
import typing

import backend.database.schemas


def serialize_result(result: typing.List[typing.Any]):
    """

    :param result:
    :return:
    """

    # Pydantic has currently no functionality to directly create a jsonable dict,
    # workaround according to the following discussion:
    # https://stackoverflow.com/questions/65622045/pydantic-convert-to-jsonable-dict-not-full-json-string
    result_ = [json.loads(backend.database.schemas.Child.from_orm(r).json()) for r in result]
    return result_
