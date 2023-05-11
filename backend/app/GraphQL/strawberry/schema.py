import datetime
import uuid

import strawberry

import backend.database.models
import backend.database.queries_v2


@strawberry.type
class Child:
    child_id: uuid.UUID
    name: str
    sur_name: str
    birth_day: datetime.date
    created_at: datetime.datetime

    @classmethod
    def marshal(cls, model: backend.database.models.Child):
        return Child(child_id=strawberry.ID(model.child_id),
                     name=model.name,
                     sur_name=model.sur_name,
                     birth_day=model.birth_day,
                     created_at=model.created_at)


@strawberry.type
class Query:
    @strawberry.field(name='children')
    def fetch_children(self) -> list[Child]:
        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)
        result = backend.database.queries_v2.fetch_children(db=db, limit=30)
        return [Child.marshal(child) for child in result]

    @strawberry.field(name='child')
    def fetch_child(self, child_id: uuid.UUID) -> Child:
        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)
        result = backend.database.queries_v2.fetch_child(db=db, child_id=child_id)
        return Child.marshal(result)


@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_child(self, name: str, sur_name: str, birth_day: datetime.date) -> uuid.UUID:
        db_config = backend.database.queries_v2.get_database_config()
        db = backend.database.queries_v2.create_session(db_config=db_config)

        child_id = uuid.uuid4()
        child_dict = dict()
        child_dict['child_id'] = child_id
        child_dict['name'] = name
        child_dict['sur_name'] = sur_name
        child_dict['birth_day'] = birth_day
        _ = backend.database.queries_v2.create_child(db=db, child=child_dict)
        db.close()
        return child_id
