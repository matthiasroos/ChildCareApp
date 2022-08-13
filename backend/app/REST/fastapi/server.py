import typing

import fastapi
import uvicorn

import database.queries
import database.schemas


app = fastapi.FastAPI()

subapi = fastapi.FastAPI()

PATH = '/rest/fastapi/v1'


@subapi.get('/children', response_model=typing.List[database.schemas.Child])
async def fetch_children(recent: bool = False, limit: int = 10):
    """

    :return:
    """
    result = database.queries.get_children(recent=recent, limit=limit)
    return result


@subapi.get('/children/{child_id}')
async def fetch_child(child_id: int = fastapi.Path(..., title='ID of the child to get')):
    """

    :return:
    """
    return None


@subapi.post('/children', status_code=fastapi.status.HTTP_201_CREATED)
async def create_child(child: dict):
    """

    :param child:
    :return:
    """
    return None


@subapi.delete('/children')
async def delete_child(child_id: int):
    """

    :param child_id:
    :return:
    """
    return None


@subapi.post('/children/{child_id}/caretimes')
async def add_caretime(child_id: int, ):
    """

    :param child_id:
    :return:
    """
    return None


subapi_parents = fastapi.FastAPI()


@subapi.get('/parents')
async def fetch_parents(limit: int = 10):
    """

    :return:
    """
    return []


@app.get(f'/is_alive')
@app.get(f'{PATH}/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


app.mount(PATH, subapi)


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)