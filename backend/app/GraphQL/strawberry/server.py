import typing

import fastapi
import strawberry.fastapi
import uvicorn

import backend.app.GraphQL.strawberry.schema
import backend.app.REST.fastapi.server


schema = strawberry.Schema(query=backend.app.GraphQL.strawberry.schema.Query,
                           mutation=backend.app.GraphQL.strawberry.schema.Mutation)
graphql_app = strawberry.fastapi.GraphQLRouter(schema)


app = fastapi.FastAPI(root_path='/graphql/strawberry/v1')
app.include_router(graphql_app, prefix='/graphql')


@app.get('/is_alive')
def is_alive():
    return {'message': 'Server is alive'}


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port=8090)
