# django-xmpp-http-account

This is a [Django](https://www.djangoproject.com) app providing functionality for [HTTP File
Upload](http://xmpp.org/extensions/inbox/http-upload.html), a draft XEP. The idea is
that an XMPP server gets the relevant upload/download URLs from this app and the app handles
all HTTP parts. This Django app can be used together with ejabberds
[mod_http_upload](https://github.com/processone/ejabberd-contrib/tree/master/mod_http_upload).

**Warning:** This app is in its early stages of development. Certainly not ready for any use.

## Settings

The following settings are supported, simply add them to your `settings.py` file (some projects use
e.g. a file called `localsettings.py`).

* `XMPP_HTTP_ACLS`:

  A list of tuples of regular expressions and a dictionary of settings. The key `http_upload` is
  used by this app (and other apps might use different keys). Various subkeys are supported:

  ```
  XMPP_HTTP_ACLS = (
      '^admin@jabber\.at$': {
          'http_upload': {},  # empty dict -> no restrictions
      },
      '^blocked@jabber.at$': False,  # this user isn't allowed to do anything
      '@jabber\.zone$': {
          'http_upload': False,  # jabber.zone users cannot upload
      }, 
      '@jabber\.at$': {
          'http_upload': {
              'max_file_size': 10 * 1024 * 1024,  # 10 MB
              'bytes_per_timedelta': {  # 1 MB per hour
                  'delta': timedelta(hours=1),
                  'bytes': 1024 * 1024,
              },
              'bytes_per_timedelta': {  # 3 Uploads per hour
                  'delta': timedelta(hours=1),
                  'uploads': 3,
              },
          },
      },
      '.*': False,  # All other users can't do anything
  )
  ```
* `XMPP_HTTP_UPLOAD_URL_BASE`:
  The domain used to create upload/download URLs when a new slot is requested by the XMPP server.
  By default, the domain used to access the slot API is used.
* `XMPP_HTTP_UPLOAD_ROOT`:
  The base directory uploaded files will be put into. This will be a subdirectory of the directory
  configured in the `MEDIA_ROOT` setting. The default is `http_upload`.
* `XMPP_HTTP_UPLOAD_PUT_TIMEOUT`:
  The default PUT timeout for slots. Clients must start uploading a file within the configured
  time. The default is 360 seconds (five minutes).
* `XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD`:
  Set to `False` if your webserver does not serve media files (see Djangos `MEDIA_URL` setting)
  and want the app itself to serve downloaded files.

## Development

If you want to use this app to develop e.g. a plugin for an XMPP server, you can simply do the
following to get a running app:

```
git clone https://github.com/mathiasertl/django-xmpp-http-upload.git
cd django-xmpp-http-upload
virtualenv .
source bin/activate
pip install -r requirements.txt
python demo/manage.py migrate
python demo/manage.py runserver
```

The last command will start a development HTTP server at `127.0.0.1:8000`. The demo project
includes the app under the `/http_upload/` path, so you can request a new slot at

http://127.0.0.1:8000/http_upload/slot/?jid=user@example.com&size=10240&name=example.jpg

### The slot API

The slot API is the API an XMPP uses to request an upload slot that can be forwarded to the user
initiating the upload. It accepts the following GET parameters:

* `jid` (mandatory)

  The JID of the user initiating the request. Note that the JID has to be URL-encoded.
* `name` (mandatory)

  The name of the file.
* `size` (mandatory)

  The file size.
* `content_type`

  The content type of the file that will be uploaded. According to the XEP, this is optional.
* `output`

  The format of the output. Currently `text/plain` (the default) and `application/json` is
  supported.

### ToDo

* Write documentation on how to use and configure this app.
* Allow `application/xml` as output format for a slot request.
