from django.db import models

# Create your models here.

class Brawl_Group(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'tracker_app'

    def __str__(self):
        return self.name

class Player(models.Model):
    group = models.ForeignKey(Brawl_Group, related_name='players', on_delete=models.CASCADE)
    player_id = models.CharField(max_length=20)

    def __str__(self):
        return self.player_id
    
