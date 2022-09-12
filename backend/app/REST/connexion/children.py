import typing
import uuid

import connexion

import backend.app.REST.utils
import backend.database.queries
import backend.database.schemas


def fetch_children(recent: bool, limit: int):
    """

    :return:
    """
    result = backend.database.queries.fetch_children(recent=recent, limit=limit)
    result_ = backend.app.REST.utils.serialize_result(result=result)
    return result_, 200


def create_child(child: typing.Dict):
    """

    :return:
    """

    child_id = uuid.uuid4()
    child_dict = child
    child_dict['child_id'] = child_id
    _ = backend.database.queries.create_child(child=child_dict)

    return child_id, 201


def fetch_child(child_id: uuid.UUID):
    """

    :return:
    """
    result = backend.database.queries.fetch_child(child_id=child_id)
    result_ = backend.app.REST.utils.serialize_result(result=result)
    return result_ or ('Not found', 404)


def update_child(child_id: uuid.UUID, updates_for_child: typing.Dict):
    """

    :return:
    """
    updates_dict = {key: values for key, values in updates_for_child.items() if values is not None}
    _ = backend.database.queries.update_child(child_id=child_id, updates_for_child=updates_dict)
    return connexion.NoContent, 200


def delete_child(child_id: uuid.UUID):
    """

    :return:
    """
    backend.database.queries.delete_child(child_id=child_id)
    return connexion.NoContent, 200
