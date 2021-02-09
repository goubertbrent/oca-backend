import logging

from flask import Flask, request, jsonify, Response
from google.cloud import storage
from resizer import ImageResizer, CantFetchImageException
from os import environ

from typing import Optional

logging.basicConfig(format='%(levelname)s %(asctime)s - %(filename)s:%(lineno)s - %(message)s')
DEBUG = False

storage_client = storage.Client()

if __name__ == '__main__':
    environ.update({
        'GAE_APPLICATION': 'e~debug',
        'GAE_ENV': 'debug',
        'GAE_SERVICE': 'oca-imageresizer',
        'GOOGLE_CLOUD_PROJECT': 'debug',
        'PORT': '8334',
        'GOOGLE_APPLICATION_CREDENTIALS': 'google-app-credentials.json',
        'API_KEY': 'debug'
    })
    DEBUG = True

app = Flask(__name__)


def _validate_api_key(headers):
    key = headers.get('X-API-Key')
    expected_key = environ.get('API_KEY')
    if key != expected_key:
        logging.warning('Incorrect api key: %s', key)
        return False
    return True


@app.route('/')
def index():
    version = environ.get('GAE_VERSION')
    return f'Image resizer service version {version}'


@app.route('/_ah/warmup')
def warmup():
    return Response(status=204)


def handle_resize_request(i: ImageResizer, resize_request: dict) -> Optional[dict]:
    """Resizes image based on the requested dimensions.
     Returns None in case the resized image would be larger than the original image.
    """
    if i.image.width > i.image.height:
        if i.image.width > resize_request['max_size']:
            img_resizer = i.resize(width=resize_request['max_size'])
        else:
            return None
    elif i.image.height > resize_request['max_size']:
        img_resizer = i.resize(height=resize_request['max_size'])
    else:
        return None

    gcs_path = resize_request['filename']
    if DEBUG:
        # Prefix with developer name in debug mode
        gcs_path = environ.get('USER') + '/' + gcs_path

    # entire bucket is public so no need to set it public explicitly
    public_url, content_type, file_size = img_resizer.store_and_return_url(in_bucket=resize_request['bucket'],
                                                                           key_name=gcs_path,
                                                                           quality=resize_request['quality'],
                                                                           encoding=resize_request['encoding'],
                                                                           public=False)
    return {
        'url': public_url,
        'path': gcs_path,
        'width': img_resizer.image.width,
        'height': img_resizer.image.height,
        'size': file_size,
        'content_type': content_type
    }

@app.route('/resize', methods=['POST'])
def api_resize():
    if not _validate_api_key(request.headers):
        return Response(status=403)
    content = request.json

    i = ImageResizer(storage_client)
    url = content['url']
    try:
        i.fetch_image_from_url(url)
    except CantFetchImageException:
        return f'Cannot fetch image {url}: not found', 404
    results = [handle_resize_request(i, resize_request) for resize_request in content['requests']]
    return jsonify({'results': results})


if __name__ == '__main__':
    if not environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        raise Exception('You must set the GOOGLE_APPLICATION_CREDENTIALS environment variable')
    app.run(host='127.0.0.1', port=int(environ.get('PORT')), debug=True)
