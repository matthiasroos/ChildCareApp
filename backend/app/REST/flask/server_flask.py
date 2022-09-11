import json

import flask

import backend.database.queries
import backend.database.schemas
from backend.app.REST.flask.authentication import auth_required


app = flask.Flask(__name__)

PREFIX = '/rest/flask/v2'


@app.route(f'{PREFIX}/children', methods=['GET'])
@auth_required(role='admin')
def get(recent: bool = False, limit: int = 10):
    result = backend.database.queries.fetch_children(recent=recent, limit=limit)
    # Pydantic has currently no functionality to directly create a jsonable dict,
    # workaround according to the following discussion:
    # https://stackoverflow.com/questions/65622045/pydantic-convert-to-jsonable-dict-not-full-json-string
    result_ = [json.loads(backend.database.schemas.Child.from_orm(r).json()) for r in result]
    response = app.response_class(
        response=json.dumps(result_),
        status=200,
        content_type='application/json',
    )
    return response


if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=8084)
