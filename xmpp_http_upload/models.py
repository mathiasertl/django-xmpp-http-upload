from django.db import models

class Upload(models.Model):
    # housekeeping
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    # Populated when a slot is requested
    name = models.CharField(max_length=256)
    size = models.PositiveIntegerField()
    type = models.CharField(max_length=64, null=True, blank=True)

    # Populated when the file is uploaded
    file = models.FileField(upload_to='http_upload', null=True, blank=True)
    uploaded = models.DateTimeField(null=True, blank=True)
