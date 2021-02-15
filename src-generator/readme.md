To fix "no module named appengine.api" and similar errors, make a symbolic link from your virtualenv to the appengine sdk.

example:

In directory `/Users/lucas/.virtualenvs/oca-backend/lib/python2.7/site-packages/google`:

```
ln -s /Users/lucas/Downloads/google-cloud-sdk/platform/google_appengine/google/appengine appengine
ln -s /Users/lucas/Downloads/google-cloud-sdk/platform/google_appengine/google/net net
```

This is due to one of the requirements also containing the 'google' package, and it overwrites the one from the appengine sdk.
