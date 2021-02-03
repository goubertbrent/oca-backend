# oca-backend

### Servers setup
- `./install.sh`: Installs the dependencies and builds the web client
- `./start_rogerthat.sh`: Starts the appengine development server
  

#### Other servers:

There are a few other (micro) services that are deployed separately. Create a virtualenv for each of them, and install their requirements using `pip install -r requirements.txt`. Then run `main.py` in the directory using the virtualenv.

- `services/imageresizer`: Image resizer used to create thumbnails and smaller versions of uploaded files
- `services/oca3`: Simple server only currently used to push homescreen data to Firestore, since there is no python3 client for it.


- [README](src/solution_server_settings/README)
- Settings: BASE_URL/admin/settings
