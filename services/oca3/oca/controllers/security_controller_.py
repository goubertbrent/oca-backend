import logging

from oca.db.server_settings import get_server_settings


def info_from_ApiKeyAuth(api_key, required_scopes):
    """
    Check and retrieve authentication information from api_key.
    Returned value will be passed in 'token_info' parameter of your operation function, if there is one.
    'sub' or 'uid' will be set in 'user' parameter of your operation function, if there is one.

    :param api_key API key provided by Authorization header
    :type api_key: str
    :param required_scopes Always None. Used for other authentication method
    :type required_scopes: None
    :return: Information attached to provided api_key or None if api_key is invalid or does not allow access to called API
    :rtype: dict | None
    """
    expected_key = get_server_settings()['apikey']
    if api_key != expected_key:
        logging.debug(f'API key does not match expected value: {api_key}, expected {expected_key}')
        raise Exception('Forbidden')
    return {}
