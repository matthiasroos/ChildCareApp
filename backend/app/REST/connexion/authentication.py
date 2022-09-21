import backend.database.usermanagement


def basic_auth(username: str, password: str, required_scopes=None):
    """


    :return:
    """
    # TODO: required_scopes is always None,
    #   despite following https://github.com/spec-first/connexion/issues/863
    db_config = backend.database.queries_v2.get_database_config()
    db = backend.database.queries_v2.create_session(db_config=db_config)
    authenticated, role = backend.database.usermanagement.authenticate_user(db=db,
                                                                            user_name=username,
                                                                            password=password)
    if not authenticated:
        return None
    return {'sub': username}
