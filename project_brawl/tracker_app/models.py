from django.db import models
import string
import secrets
import random

# Create your models here.

class Brawl_Group(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'tracker_app'

    def __str__(self):
        return self.name

class Group(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        app_label = 'tracker_app'
    
    def __str__(self):
        return self.name

class Player(models.Model):
    group = models.ForeignKey(Group, related_name='players', on_delete=models.CASCADE)
    player_id = models.CharField(max_length=20)
    brawl_name = models.CharField(max_length=100, default='Unknown')

    def __str__(self):
        return self.brawl_name