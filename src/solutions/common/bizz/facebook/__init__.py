import logging
import StringIO

import facebook

from mcfw.rpc import returns, arguments
from solution_server_settings import get_solution_server_settings


@returns()
@arguments(access_token=unicode, message=unicode, image=str)
def post_to_facebook(access_token, message, image=None):
    """
    Post to facebook.

    Args:
        access_token (unicode): user or page access token
        message (unicode)
        image (str): image content
    """
    fb = facebook.GraphAPI(access_token)

    try:
        if image:
            image_source = StringIO.StringIO(image)
            fb.put_photo(image=image_source, message=message)
        else:
            fb.put_wall_post(message)
    except facebook.GraphAPIError:
        logging.error('Post to facebook failed', exc_info=True, _suppress=False)


@returns(unicode)
@arguments(access_token=unicode)
def extend_access_token(access_token):
    server_settings = get_solution_server_settings()
    app_id = server_settings.facebook_app_id
    app_secret = server_settings.facebook_app_secret

    fb = facebook.GraphAPI(access_token)
    extended_token = fb.extend_access_token(app_id, app_secret)['access_token']

    return extended_token
