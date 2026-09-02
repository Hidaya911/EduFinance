from django.db import models
from django_mongodb_backend.fields import ObjectIdField

class User(models.Model):
    _id = ObjectIdField(primary_key=True, auto_created=True)