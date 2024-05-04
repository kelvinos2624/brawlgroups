# myapp/views.py
from django.shortcuts import render, redirect
from .forms import Group_Form, Player_Form
from .models import Group, Player
import requests
import os
import json
from dotenv import load_dotenv
from collections import Counter
import random
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

def group_detail(request, group_id):
    group = Group.objects.get(pk=group_id)
    players = group.players.all()
    for player in players:
        response = authenticate(player.player_id)
        response_battlelog = authenticate_battlelog(player.player_id)
        player.tilted_stats = find_tilted_brawlers(response)
        player.total_trophies = get_total_trophies(response)
        player.solo_victories = get_solo_victories(response)
        player.duo_victories = get_duo_victories(response)
        player.threes_victories = get_3v3_victories(response)
        player.brawler_trophies = get_brawler_trophies(response)
        player.recent_win_rate = get_win_rate(response_battlelog)
        player.highest_trophies = get_highest_trophies(response)
        player.favourite_gamemode = get_favourite_gamemode(response_battlelog)
        player.favourite_brawler = get_favourite_brawler(response_battlelog, player)

    players = sorted(players, key=lambda x: x.total_trophies, reverse=True)
    brawler_response = get_brawlers_info()
    brawlers = [brawler["name"] for brawler in brawler_response.json()["items"]]

    # Serialize only the brawler_trophies attribute of players to JSON format
    brawler_trophies_json = json.dumps({
        player.brawl_name: player.brawler_trophies for player in players
    })

    fun_fact = get_fun_fact()

    player_info_json = json.dumps({
        player.brawl_name: {
            'total_trophies': player.total_trophies,
            'solo_victories': player.solo_victories,
            'duo_victories': player.duo_victories,
            'threes_victories': player.threes_victories,
            'recent_win_rate': player.recent_win_rate,
            'highest_trophies': player.highest_trophies,
            'favourite_gamemode': player.favourite_gamemode,
            'favourite_brawler': player.favourite_brawler,
        } for player in players
    })

    return render(request, 'group_detail.html', {
        'group_id': group_id,
        'group': group,
        'players': players,
        'brawler_trophies': brawler_trophies_json,  # Pass the serialized brawler_trophies data
        'brawlers': brawlers,
        'player_info': player_info_json,
        'fun_fact': fun_fact
    })

def get_fun_fact():
    fun_facts = [
        "Brawl Stars was beta for 2.5 years",
        "Mortis' default skin had a hat",
        "Pam was once called Mama J.",
        "Leon's initial invisibility made him the game's most broken brawler at launch",
        "Project Laser origins in 2015 as a multiplayer action shooter, evolving from Clash of Clans and Hay Day controls, laid the foundational idea for Brawl Stars",
        "Sakura Spike used to be called Pinky Spike",
        "Sakura Spike is undeniably the best Spike skin in the game :)"
        ]
    return fun_facts[random.randint(0, len(fun_facts) - 1)]

def get_highest_trophies(response):
    return response.json()["highestTrophies"]

def get_solo_victories(response):
    return response.json()["soloVictories"]

def get_duo_victories(response):
    return response.json()["duoVictories"]

def get_3v3_victories(response):
    return response.json()["3vs3Victories"]

def get_favourite_gamemode(response):
    gamemodes = Counter()
    for gamemode in response.json()['items']:
        gamemode = gamemode["battle"]
        gamemodes[gamemode["mode"]] += 1
    return gamemodes.most_common(1)[0][0]

def get_favourite_brawler(response, player):
    brawlers = Counter()
    for brawler in response.json()['items']:
        try:
            brawler = brawler["battle"]
            brawler = brawler["teams"]
            for item in brawler:
                if item[0]['name'] == player.brawl_name:
                    brawlers[item[0]['brawler']['name']] += 1
        except:
            continue
    return brawlers.most_common(1)[0][0]

def authenticate_battlelog(player):
    url = f"https://api.brawlstars.com/v1/players/%23{player}/battlelog"
    headers = {
        "Authorization": "Bearer " + "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjA5M2I1ZDY1LThjZjEtNGI0My1hZWEyLTMzMjJjOWQxOTFmMSIsImlhdCI6MTcxNDgwNDc5MCwic3ViIjoiZGV2ZWxvcGVyLzdiZjRlYmQ5LWIxODYtOTJkMS01NTczLTNlMmU3NTc2MzQzNSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMzQuODYuMTE5LjEyNCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.T-e11oDHecIWzjImf3oO9_gGyfypVGV0IlZQkUTbbku7IQixur1mUjVh1AqERmsemJ_0WYpcd16XSfPv3NCwVQ"
    }
    response = requests.get(url, headers=headers)
    return response

def get_win_rate(response):
    victory_counter = 0
    loss_counter = 0
    valid_gamemodes = ["gemGrab", "knockout", "brawlBall", "heist", "hotZone", "bounty", "wipeout", "duels"]
    for battle in response.json()['items']:
        battle = battle["battle"]
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
        "Authorization": "Bearer " + "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjA5M2I1ZDY1LThjZjEtNGI0My1hZWEyLTMzMjJjOWQxOTFmMSIsImlhdCI6MTcxNDgwNDc5MCwic3ViIjoiZGV2ZWxvcGVyLzdiZjRlYmQ5LWIxODYtOTJkMS01NTczLTNlMmU3NTc2MzQzNSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMzQuODYuMTE5LjEyNCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.T-e11oDHecIWzjImf3oO9_gGyfypVGV0IlZQkUTbbku7IQixur1mUjVh1AqERmsemJ_0WYpcd16XSfPv3NCwVQ"
    }
    response = requests.get(url, headers=headers)
    return response

def get_brawlers_info():
    url = "https://api.brawlstars.com/v1/brawlers"
    headers = {
        "Authorization": "Bearer " + "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjA5M2I1ZDY1LThjZjEtNGI0My1hZWEyLTMzMjJjOWQxOTFmMSIsImlhdCI6MTcxNDgwNDc5MCwic3ViIjoiZGV2ZWxvcGVyLzdiZjRlYmQ5LWIxODYtOTJkMS01NTczLTNlMmU3NTc2MzQzNSIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMzQuODYuMTE5LjEyNCJdLCJ0eXBlIjoiY2xpZW50In1dfQ.T-e11oDHecIWzjImf3oO9_gGyfypVGV0IlZQkUTbbku7IQixur1mUjVh1AqERmsemJ_0WYpcd16XSfPv3NCwVQ"
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
