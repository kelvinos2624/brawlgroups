# myapp/views.py
from django.shortcuts import render, redirect
from .forms import Group_Form, Player_Form
from .models import Group, Player
import requests
import os
import json
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
    group = Group.objects.get(pk=group_id)
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

def delete_player(request, group_id, player_id):
    group = Group.objects.get(pk=group_id)
    player = Player.objects.get(pk=player_id)
    player.delete()
    return redirect('group_detail', group_id=group_id)

def edit_group_name(request, group_id):
    group = Group.objects.get(pk=group_id)
    if request.method == 'POST':
        # If the form is submitted, update the group name
        new_group_name = request.POST.get('new_group_name')
        group.name = new_group_name
        group.save()
        return redirect('group_detail', group_id=group_id)
    return render(request, 'edit_group_name.html', {'group': group})

import json

def group_detail(request, group_id):
    group = Group.objects.get(pk=group_id)
    players = group.players.all()
    for player in players:
        response = authenticate(player.player_id)
        player.tilted_stats = find_tilted_brawlers(response)
        player.total_trophies = get_total_trophies(response)
        player.solo_victories = get_solo_victories(response)
        player.duo_victories = get_duo_victories(response)
        player.threes_victories = get_3v3_victories(response)
        player.brawler_trophies = get_brawler_trophies(response)
        player.recent_win_rate = get_win_rate(player.player_id)
        player.highest_trophies = get_highest_trophies(response)

    players = sorted(players, key=lambda x: x.total_trophies, reverse=True)
    brawler_response = get_brawlers_info()
    brawlers = [brawler["name"] for brawler in brawler_response.json()["items"]]

    # Serialize only the brawler_trophies attribute of players to JSON format
    brawler_trophies_json = json.dumps({
        player.brawl_name: player.brawler_trophies for player in players
    })

    player_info_json = json.dumps({
        player.brawl_name: {
            'total_trophies': player.total_trophies,
            'solo_victories': player.solo_victories,
            'duo_victories': player.duo_victories,
            'threes_victories': player.threes_victories,
            'recent_win_rate': player.recent_win_rate,
            'highest_trophies': player.highest_trophies
        } for player in players
    })

    return render(request, 'group_detail.html', {
        'group_id': group_id,
        'group': group,
        'players': players,
        'brawler_trophies': brawler_trophies_json,  # Pass the serialized brawler_trophies data
        'brawlers': brawlers,
        'player_info': player_info_json,
    })

def get_highest_trophies(response):
    return response.json()["highestTrophies"]

def get_solo_victories(response):
    return response.json()["soloVictories"]

def get_duo_victories(response):
    return response.json()["duoVictories"]

def get_3v3_victories(response):
    return response.json()["3vs3Victories"]

def get_win_rate(player):
    url = f"https://api.brawlstars.com/v1/players/%23{player}/battlelog"
    headers = {
        "Authorization": "Bearer " + os.getenv("API_KEY")
    }
    response = requests.get(url, headers=headers)
    victory_counter = 0
    loss_counter = 0
    valid_gamemodes = ["gemGrab", "knockout", "brawlBall", "heist", "hotZone", "bounty", "wipeout"]
    for battle in response.json()['items']:
        battle = battle["battle"]
        print(battle)
        if battle["mode"] in valid_gamemodes:
            if battle["result"] == "victory":
                victory_counter += 1
            else:
                loss_counter += 1
            
    win_rate = (victory_counter / (victory_counter + loss_counter)) * 100
    return f"{win_rate:.2f}%"

def authenticate(player):
    url = f"https://api.brawlstars.com/v1/players/%23{player}"
    headers = {
        "Authorization": "Bearer " + os.getenv("API_KEY")
    }
    response = requests.get(url, headers=headers)
    return response

def get_brawlers_info():
    url = "https://api.brawlstars.com/v1/brawlers"
    headers = {
        "Authorization": "Bearer " + os.getenv("API_KEY")
    }
    return requests.get(url, headers=headers)

def find_tilted_brawlers(response):
    tilt = {}
    for entity in response.json()["brawlers"]:
        tilt[entity["name"]] = entity["highestTrophies"] - entity["trophies"]
    return dict(sorted(tilt.items(), key=lambda x: x[1], reverse=True))

def get_total_trophies(response):
    return response.json()["trophies"]

def get_brawler_trophies(response):
    brawler_trophies = {}
    for entity in response.json()["brawlers"]:
        brawler_trophies[entity["name"]] = entity["trophies"]
    return brawler_trophies

def menu(request):
    try:
        player_id = request.GET.get('player_id')
        if player_id:
            response = authenticate(player_id)
            converted_tilt = find_tilted_brawlers(response)
            total_trophies = get_total_trophies(response)
            return render(request, 'menu.html', {'converted_tilt': converted_tilt, 'total_trophies': total_trophies, 'player_name': response.json()["name"]})
    except:
        return render(request, 'error.html', {'message': 'Player ID not provided'})

def index(request):
    return render(request, 'index.html')

def error(request):
    return render(request, 'error.html', {'message': 'An error occurred'})
