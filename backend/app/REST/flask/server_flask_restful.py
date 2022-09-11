import json

import flask
import flask_restful

import backend.database.queries
import backend.database.schemas
from backend.app.REST.flask.authentication import auth_required


app = flask.Flask(__name__)
api = flask_restful.Api(app)

PREFIX = '/rest/flask/v1'


class Children(flask_restful.Resource):
    method_decorators = [auth_required(role='admin')]

    def get(self, recent: bool = False, limit: int = 10):
        result = backend.database.queries.fetch_children(recent=recent, limit=limit)
        # Pydantic has currently no functionality to directly create a jsonable dict,
        # workaround according to the following discussion:
        # https://stackoverflow.com/questions/65622045/pydantic-convert-to-jsonable-dict-not-full-json-string
        result_ = [json.loads(backend.database.schemas.Child.from_orm(r).json()) for r in result]
        return result_


api.add_resource(Children, f'{PREFIX}/children', '/children')


if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=8084)
