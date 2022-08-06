import fastapi
import uvicorn

import database.queries


app = fastapi.FastAPI()


@app.get('/rest/fastapi/v1/children')
async def fetch_children(recent: bool = False, limit: int = 10):
    """

    :return:
    """
    result = database.queries.get_children(recent=recent, limit=limit)
    return result


@app.get('/rest/fastapi/v1/children/{child_id}')
async def fetch_child(child_id: int = fastapi.Path(..., title='ID of the child to get')):
    """

    :return:
    """
    return None


@app.post('/rest/fastapi/v1/children', status_code=fastapi.status.HTTP_201_CREATED)
async def create_child(child: dict):
    """

    :param child:
    :return:
    """
    return None


@app.delete('/rest/fastapi/v1/children')
async def delete_child(child_id: int):
    """

    :param child_id:
    :return:
    """
    return None


@app.post('/rest/fastapi/v1/children/{child_id}/caretimes')
async def add_caretime(child_id: int, ):
    """

    :param child_id:
    :return:
    """
    return None


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)
