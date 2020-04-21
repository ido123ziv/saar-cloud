from django.db import models

# Create your models here.
class CloudUser(models.Model):
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    displayName = models.CharField(max_length=100)
    directory = models.CharField(max_length=10000)

    def __str__(self):
        return self.username + ' - ' + self.displayName
