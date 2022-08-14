import json

import flask

import database.queries
import database.schemas


app = flask.Flask(__name__)

PREFIX = '/rest/flask/v2'


@app.route(f'{PREFIX}/children', methods=['GET'])
def get(recent: bool = False, limit: int = 10):
    result = database.queries.get_children(recent=recent, limit=limit)
    # Pydantic has currently no functionality to directly create a jsonable dict,
    # workaround according to the following discussion:
    # https://stackoverflow.com/questions/65622045/pydantic-convert-to-jsonable-dict-not-full-json-string
    result_ = [json.loads(database.schemas.Child.from_orm(r).json()) for r in result]
    result_json = flask.jsonify(result_)
    return result_json


if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=8084)
