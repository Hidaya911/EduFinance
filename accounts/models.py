from djongo import models

class User(models.Model):
    _id = models.ObjectIdField(primary_key=True)