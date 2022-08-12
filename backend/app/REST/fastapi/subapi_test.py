import fastapi
import uvicorn


PATH = '/test'

app = fastapi.FastAPI()


subapi_children = fastapi.FastAPI()


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
    uvicorn.run(app, host='localhost', port=8083)
