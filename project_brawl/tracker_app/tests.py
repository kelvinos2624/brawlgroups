from django.test import TestCase

# Create your tests here.
from django.db import models

class PlayerGroup(models.Model):
    name = models.CharField(max_length=100)
    player_ids = models.TextField()
