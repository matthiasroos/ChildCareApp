import json

import flask

import backend.app.REST.utils.json_handling
import backend.database.queries
import backend.database.schemas
from backend.app.REST.flask.authentication import auth_required


app = flask.Flask(__name__)

PREFIX = '/rest/flask/v2'


@app.route(f'{PREFIX}/children', methods=['GET'])
@auth_required(required_role='admin')
def get(recent: bool = False, limit: int = 10):
    result = backend.database.queries.fetch_children(recent=recent, limit=limit)
    result_ = backend.app.REST.utils.json_handling.serialize_result(result=result)
    response = app.response_class(
        response=json.dumps(result_),
        status=200,
        content_type='application/json',
    )
    return response


@app.route(f'{PREFIX}/children', methods=['POST'])
@auth_required(required_role='admin')
def post():
    result = backend.database.queries.fetch_child(child_id=flask.request.form['child_id'])
    result_ = backend.app.REST.utils.json_handling.serialize_result(result=result)
    response = app.response_class(
        response=json.dumps(result_),
        status=200,
        content_type='application/json',
    )
    return response


if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=8084)
