from django import forms
from .models import Group, Player

class Group_Form(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']

class Player_Form(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['player_id']