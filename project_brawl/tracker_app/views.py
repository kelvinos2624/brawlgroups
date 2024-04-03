# myapp/views.py
from django.shortcuts import render, redirect
from .forms import Group_Form, Player_Form
from .models import Brawl_Group, Player
import requests
import os
from dotenv import load_dotenv
load_dotenv()

def create_group(request):
    if request.method == 'POST':
        form = Group_Form(request.POST)
        if form.is_valid():
            group = form.save()
            return redirect('group_detail', group_id=group.id)
    else:
        form = Group_Form()
    return render(request, 'create_group.html', {'form': form})

def add_player(request, group_id):
    group = Brawl_Group.objects.get(pk=group_id)
    if request.method == 'POST':
        form = Player_Form(request.POST)
        if form.is_valid():
            player_id = form.cleaned_data.get('player_id')
            # Verify if the player ID exists in the API
            response = authenticate(player_id)
            if response.status_code == 200:
                player = form.save(commit=False)
                player.brawl_name = response.json()["name"]
                player.group = group
                player.save()
                return redirect('group_detail', group_id=group_id)
            else:
                error_message = "Player ID does not exist. Please enter a valid player ID."
                return render(request, 'add_player.html', {'form': form, 'group': group, 'error_message': error_message})
    else:
        form = Player_Form()
    return render(request, 'add_player.html', {'form': form, 'group': group})

def group_detail(request, group_id):
    group = Brawl_Group.objects.get(pk=group_id)
    players = group.players.all()
    return render(request, 'group_detail.html', {'group_id': group_id, 'group': group, 'players': players})

def authenticate(player):
    url = f"https://api.brawlstars.com/v1/players/%23{player}"
    headers = {
        "Authorization": "Bearer " + os.getenv("API_KEY")
    }
    response = requests.get(url, headers=headers)
    return response

def find_tilted_brawlers(response):
    tilt = {}
    for entity in response.json()["brawlers"]:
        tilt[entity["name"]] = entity["highestTrophies"] - entity["trophies"]
    return dict(sorted(tilt.items(), key=lambda x: x[1], reverse=True))

def menu(request):
    try:
        player_id = request.GET.get('player_id')
        if player_id:
            response = authenticate(player_id)
            converted_tilt = find_tilted_brawlers(response)
            return render(request, 'menu.html', {'converted_tilt': converted_tilt, 'player_name': response.json()["name"]})
    except:
        return render(request, 'error.html', {'message': 'Player ID not provided'})

def index(request):
    return render(request, 'index.html')

def error(request):
    return render(request, 'error.html', {'message': 'An error occurred'})
