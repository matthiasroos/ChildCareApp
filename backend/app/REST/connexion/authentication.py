import backend.database.usermanagement


def basic_auth(username: str, password: str, required_scopes=None):
    """


    :return:
    """
    # TODO: required_scopes is always None,
    #   despite following https://github.com/spec-first/connexion/issues/863
    authenticated, role = backend.database.usermanagement.authenticate_user(user_name=username,
                                                                            password=password)
    if not authenticated:
        return None
    return {'sub': username}
