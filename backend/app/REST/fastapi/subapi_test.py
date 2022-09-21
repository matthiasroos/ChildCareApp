import fastapi
import fastapi.security
import sqlalchemy.orm
import uvicorn

import backend.database.queries_v2
import backend.database.usermanagement

PATH = '/test'

app = fastapi.FastAPI()

security = fastapi.security.HTTPBasic()


def get_db(request: fastapi.Request):
    """

    :return:
    """
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    try:
        yield db
    finally:
        db.close()


def check_credentials(credentials: fastapi.security.HTTPBasicCredentials = fastapi.Depends(security),
                      db: sqlalchemy.orm.Session = fastapi.Depends(get_db)):
    """

    """

    authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                            user_name=credentials.username,
                                                                            password=credentials.password)
    if not authenticated or role != 'admin':
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return


subapi_children = fastapi.FastAPI(dependencies=[fastapi.Depends(check_credentials)])


@subapi_children.get('/')
async def fetch_children(request: fastapi.Request, db=fastapi.Depends(get_db)):
    result = backend.database.queries_v2.fetch_children(db=db)
    return result


subapi_parents = fastapi.FastAPI()


@subapi_parents.get('/')
async def fetch_parents(limit: int = 10):
    return {'message': 'list of parents '}


@subapi_parents.get('/parents/is_alive')
async def is_alive():
    return {'message': 'parents Server is alive'}


@app.get(f'/is_alive')
@app.get(f'{PATH}/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


app.mount(f'{PATH}/children', subapi_children)
app.mount(f'{PATH}/parents/', subapi_parents)


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8084)
