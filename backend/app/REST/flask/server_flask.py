import json

import flask

import backend.app.REST.utils.gunicorn_app
import backend.app.REST.utils.json_handling
import backend.database.queries
import backend.database.schemas
from backend.app.REST.flask.authentication import auth_required


app = flask.Flask(__name__)

PREFIX = '/rest/flask/v2'


@app.route(f'{PREFIX}/children', methods=['GET'])
@auth_required(required_role='admin')
def handle_get(recent: bool = False, limit: int = 10):
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
def handle_post():
    result = backend.database.queries.fetch_child(child_id=flask.request.json['child_id'])
    result_ = backend.app.REST.utils.json_handling.serialize_result(result=result)
    response = app.response_class(
        response=json.dumps(result_),
        status=200,
        content_type='application/json',
    )
    return response


if __name__ == '__main__':
    options = {
        'bind': '%s:%s' % ('localhost', '8084'),
        'workers': 2,
    }
    backend.app.REST.utils.gunicorn_app.GunicornApp(app, options).run()
