import secrets
import typing
import uuid

import fastapi
import fastapi.security
import uvicorn

import database.queries
import database.schemas
import database.usermanagement


app = fastapi.FastAPI(root_path='/rest/fastapi/v1')

security = fastapi.security.HTTPBasic()


def check_credentials(credentials: fastapi.security.HTTPBasicCredentials = fastapi.Depends(security)):
    """

    """
    authenticated = database.usermanagement.authenticate_user(credentials.username, credentials.password)
    if not authenticated:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return authenticated


@app.get('/children', response_model=typing.List[database.schemas.Child])
async def fetch_children(recent: bool = False, limit: int = 10,
                         authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    result = database.queries.fetch_children(recent=recent, limit=limit)
    return result


@app.get('/children/{child_id}', response_model=database.schemas.Child)
async def fetch_child(child_id: uuid.UUID = fastapi.Path(..., title='ID of the child to get'),
                      authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    result = database.queries.fetch_child(child_id=child_id)
    return result


@app.post('/children', status_code=fastapi.status.HTTP_201_CREATED)
async def create_child(child: database.schemas.ChildBase,
                       authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    child_id = uuid.uuid4()
    child_dict = child.dict()
    child_dict['child_id'] = child_id
    _ = database.queries.create_child(child=child_dict)
    return child_id


@app.put('/children/{child_id}/update')
async def update_child(child_id: uuid.UUID, updates_for_child: database.schemas.ChildUpdate,
                       authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    updates_dict = {key: values for key, values in updates_for_child.dict().items() if values is not None}
    _ = database.queries.update_child(child_id=child_id, updates_for_child=updates_dict)
    return


@app.delete('/children/{child_id}/delete')
async def delete_child(child_id: uuid.UUID,
                       authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    _ = database.queries.delete_child(child_id=child_id)
    return


@app.post('/children/{child_id}/caretimes')
async def add_caretime(child_id: uuid.UUID,
                       authenticated: bool = fastapi.Depends(check_credentials)):
    """

    :return:
    """
    return None


@app.get('/parents')
async def fetch_parents(limit: int = 10):
    """

    :return:
    """
    return []


@app.get('/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8083)
