import fastapi
import fastapi.security
import uvicorn


import backend.database.usermanagement

PATH = '/test'

app = fastapi.FastAPI()

security = fastapi.security.HTTPBasic()


def check_credentials(credentials: fastapi.security.HTTPBasicCredentials = fastapi.Depends(security)):
    """

    """
    authenticated, role = backend.database.usermanagement.authenticate_user(credentials.username,
                                                                            credentials.password)
    if not authenticated or role != 'admin':
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return


subapi_children = fastapi.FastAPI(dependencies=[fastapi.Depends(check_credentials)])


@subapi_children.get('/')
async def fetch_children():
    return {'message': 'list of children '}


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
