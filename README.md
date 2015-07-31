# django-xmpp-http-account

This is a [Django](https://www.djangoproject.com) app providing functionality for [HTTP File
Upload](http://xmpp.org/extensions/inbox/http-upload.html), a draft XEP. The idea is
that an XMPP server gets the relevant upload/download URLs from this app and the app handles
all HTTP parts. 

### Development

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
