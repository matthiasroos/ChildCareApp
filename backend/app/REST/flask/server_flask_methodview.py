import json

import flask.views

import backend.app.REST.utils.json_handling
import backend.database.queries
import backend.database.schemas
from backend.app.REST.flask.authentication import auth_required


app = flask.Flask(__name__)

PREFIX = '/rest/flask/v1'


class Children(flask.views.MethodView):
    method_decorators = [auth_required(required_role='admin')]

    def get(self, recent: bool = False, limit: int = 10):
        result = backend.database.queries.fetch_children(recent=recent, limit=limit)
        result_ = backend.app.REST.utils.json_handling.serialize_result(result=result)
        response = app.response_class(
            response=json.dumps(result_),
            status=200,
            content_type='application/json',
        )
        return response


app.add_url_rule(rule=f'{PREFIX}/children', view_func=Children.as_view('children'))


if __name__ == '__main__':
    app.run(debug=False, host='localhost', port=8084)
