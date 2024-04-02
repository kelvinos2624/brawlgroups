from django import forms
from .models import Brawl_Group, Player

class Group_Form(forms.ModelForm):
    class Meta:
        model = Brawl_Group
        fields = ['name']

class Player_Form(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['player_id']