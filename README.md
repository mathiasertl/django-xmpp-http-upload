# django-xmpp-http-upload

This is a [Django](https://www.djangoproject.com) app providing functionality for [XEP-0363: HTTP
File Upload](http://www.xmpp.org/extensions/xep-0363.html), an experimental XEP. The idea is that
an XMPP server gets the relevant upload/download URLs from this app and the app handles all HTTP
parts. This Django app can be used together with ejabberds
[mod_http_upload](https://github.com/processone/ejabberd-contrib/tree/master/mod_http_upload).

## Django integration

This assumes you already have an up and running Django instance somewhere. 

* Install **django-xmpp-http-upload** via pip:

  ```
  pip install django-xmpp-http-upload
  ```

* Add `"xmpp_http_upload"` to your `INSTALLED_APPS`, in your `settings.py`:

  ```python
  INSTALLED_APPS = (
      # ...
      "xmpp_http_upload",
  )
  ```
* Add settings described below to to your `settings.py`.
* Include URLs in your root `urls.py` (e.g. project/project/urls.py):

  ```
  urlpatterns = [
      # ...
      # regex can be anything, but namespace is important
      url(r'^share/', include('xmpp_http_upload.urls', namespace='xmpp-http-upload')),
  ]
  ```
* And finally run `manage.py migrate` to create the necessary database tables:

  ```
  python manage.py migrate
  ```
* Make sure you have a working setup for [managing
  files](https://docs.djangoproject.com/en/1.8/topics/files/), in particular, the `MEDIA_ROOT` and
  `MEDIA_URL` settings have to be correctly configured. The app uses some custom settings as well,
  see below.
* Ensure that you [cleanup old files](#user-content-cleanup-of-old-files).

## Webserver security

Care should be taken to secure your webserver:

* The slot API (`/share/slot/` in the above example) should only be reachable from the XMPP server,
   otherwise anyone might request a slot.
* The directory where files are uploaded should have no directory indexes and should not allow any
  .htaccess overrides. This app uploads all files into the directory configured by
  `XMPP_HTTP_UPLOAD_ROOT`, which is a subdirectory of `MEDIA_ROOT`. By default, that's
  `http_upload`.

Here is what is recommended for Apache:

```apache
<Location /share/slot>
    # Restrict the slot api:
    Require ip 127.0.0.1
</Location>

<Directory /var/www/upload.example.com/media/http_upload>
    # Lock down the upload directory (you might want to do this for all of media...)
    Options -FollowSymLinks -Indexes -ExecCGI -MultiViews
    AllowOverride none
</Directory>
```

## Settings

The following settings are supported, simply add them to your `settings.py` file (some projects use
e.g. a file called `localsettings.py`).

* `XMPP_HTTP_UPLOAD_ACCESS`: (**mandatory!**)

  A list of two-tuples with the first element being a regular expression (or list of regular
  expressions) and the second element being quota settings. This setting configures upload
  permissions and any upload quotas. The settings for the first matching regular expression are
  applied, so in the below example, `blocked@jabber.at` will not be able to upload, all other
  `jabber.at` or `jabber.zone` users will have the configured quotas applied. Here is a (maybe just
  a little too restricted) example:

  ```python
  XMPP_HTTP_UPLOAD_ACCESS = (
      ('^admin@jabber\.at$', {}),  # empty dict -> no restrictions
      }),
      ('^blocked@jabber.at$', False),  # this user isn't allowed to upload files
      # jabber.at and jabber.zone users have some restrictions:
      (['@jabber\.at$', '@jabber\.zone$'], {
          # User may not upload a file larger then 512 KB:
          'max_file_size': 512 * 1024,

          # User may not upload more then 10 MB in total
          'max_total_size': 10 * 1024 * 1024,

          # User may not upload more then 1 MB per hour
          'bytes_per_timedelta': {
              'delta': timedelta(hours=1),
              'bytes': 1024 * 1024,
          },

          # User may not do more then three uploads per hour
          'uploads_per_timedelta': {
              'delta': timedelta(hours=1),
              'uploads': 3,
          },
      }),
      ('.*', False),  # All other users can't upload anything either
  )
  ```

  The default is `(('.*', False), )`, so users cannot upload any files. You need to configure
  something that is sensible for your environment.
* `XMPP_HTTP_UPLOAD_URL_BASE`:
  The domain used to create upload/download URLs when a new slot is requested by the XMPP server.
  By default, the domain used to access the slot API is used.
* `XMPP_HTTP_UPLOAD_URL_HTTPS`:
  Ensure returned GET and PUT urls to be https. May be needed if protocol is
  not correctly recognized automatically.
* `XMPP_HTTP_UPLOAD_ROOT`:
  The base directory uploaded files will be put into. This will be a subdirectory of the directory
  configured in the `MEDIA_ROOT` setting. The default is `http_upload`.
* `XMPP_HTTP_UPLOAD_PUT_TIMEOUT`:
  The default PUT timeout for slots. Clients must start uploading a file within the configured
  time. The default is 360 seconds (five minutes).
* `XMPP_HTTP_UPLOAD_SHARE_TIMEOUT`:
  For how long (in seconds) uploaded files are kept. Defaults to 30 days. Please see [cleanup of
  old files](#user-content-cleanup-of-old-files) for more information.
* `XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD`:
  Set to `False` if your webserver does not serve media files (see Djangos `MEDIA_URL` setting)
  and want the app itself to serve downloaded files.
* `XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH`:
  Set to `True` to add the `Content-Length` header Slot API responses. The header leads to HTTP
  responses not using [chunked transfer
  encoding](https://en.wikipedia.org/wiki/Chunked_transfer_encoding). Erlangs HTTP client seems to
  have problems with this in some situations.

## Cleanup of old files

The `cleanup_http_uploads` management command should be used to periodically clean up old files.
Note that this is not really an optional step, otherwise the app will soon eat up all available
diskspace. Also in combination with `max_total_size` setting in `XMPP_HTTP_UPLOAD_ACCESS`, users
would never again be able to upload any files once they've reached their quota. This example
crontab would cleanup old files every day at 1 a.m.:

```
# Location of your Django app
HOME=/home/django/your-app
# If you use virtualenv, the location of its bin/ dir:
#PATH=/home/django/bin/

# m h   dom mon dow     user            command
0 1     * * *           root            python manage.py cleanup_http_uploads
```

### celery task

Alternatively, if you use [Celery](http://www.celeryproject.org/), you can also use the 
``xmpp_http_upload.cleanup_http_uploads`` task to cleanup your files.

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

* `jid` (mandatory): The JID of the user initiating the request. Note that the JID has to be
  URL-encoded.
* `name` (mandatory): The name of the file.
* `size` (mandatory): The file size.
* `content_type`: The content type of the file that will be uploaded. According to the XEP, this is
  optional.
* `output`: The format of the output. Currently `text/plain` (the default) and `application/json`
  is supported.

### Testing

There are testcases for the app, run it with:

```
cd demo
python manage.py test xmpp_http_upload
```

## TODO

* Write cleanup celery task

## ChangeLog

### 0.5.1 (2017-12-26)

* Support Django 2.0, drop support for Django 1.8 and 1.9.
* Handle requests that do not provide a ContentLength header (a rare corner case).

### 0.5.0 (2017-03-10)

* Increase length of `type` column to 255 characters (we sometimes encounter up to 80 characters).
* If a user does not match any ACL from the `XMPP_HTTP_UPLOAD_ACCESS` setting, all uploads are denied.
* Set the default app name to ``xmpp_http_upload``.
* Add many more tests to the test suite.
* Use isort to sort imports, increase textwidth to 110 chars.
* Add new setup.py commands to run the test-suite or code quality tests. 
* Add new setup.py command to generate a coverage report for the test suite.
* Use [Travis CI](https://travis-ci.org/) to run the test-suite and code quality tests in all supported Python
  and Django Versions.

### 0.4.1 (2016-03-19)

* Fix uploading filenames with spaces (spaces are now replaced with an underscore).
* Update djangorestframework dependency to the current 3.3.3.
* Fix some broken test cases, test uploads more thoroughly.
* Also upload a [Python Wheel](http://pythonwheels.com/).

### 0.4 (2016-01-09)

* Add the option `XMPP_HTTP_UPLOAD_ADD_CONTENT_LENGTH` to add the `Content-Length` header in
  responses. This leads to the response not being chunked, Erlang seems to choke on chunked
  responses.
* New option `XMPP_HTTP_UPLOAD_URL_HTTPS` to force HTTPS URLs (thanks to Filip Pytloun).
* Fix constructing of media URLs (when `XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD` is `True`) with
  non-ascii characters.
* Catch UnreadablePostError on upload, usually occurs when the client opens a connection and never
  starts sending data. We now return HTTP 400 in this case.

### 0.3 (2015-09-15)

* Fix Slot-API (ups!).
* Do not allow any slots where the filename contains a slash. Django should handle this, but just
  to be sure.
* Return HTTP 413 instead of HTTP 412, as requested by mod_http_upload.

### 0.2.1 (2015-09-15)

* We can no longer use 0.2, because PyPi does not allow reuploading of versions.
* New management command `cleanup_http_uploads` to cleanup old file uploads.
* Integrate the Upload slots into the default admin interface provided by Django.
* Increase maximum filename length to 255 chars (was: 100, Djangos default).
* Return HTTP 412 if user requests a slot with a filename that's too long.
* The size of the random hash is decreased to 32 characters, decreasing likelyhood of such a 
  HTTP 412.
* Only actually serve Upload slots if `XMPP_HTTP_UPLOAD_WEBSERVER_DOWNLOAD` is actually set to
  True. Previously the URL was just not advertised, but users could theoretically still use it.
* Catch HTTP 500 if a non-existing slot is used (or user attempts to reuse a slot).
* Update dependencies, code-style now fully conforms with pep8.

### 0.1 (2015-08-23)

* Initial version.
