# myapp/views.py
from django.shortcuts import render
import requests
import os
from dotenv import load_dotenv, dotenv_values
load_dotenv()

def authenticate(player):
    api_key = "YOUR_API_KEY_HERE"
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
    player_id = request.GET.get('player_id')
    if player_id:
        response = authenticate(player_id)
        converted_tilt = find_tilted_brawlers(response)
        return render(request, 'menu.html', {'converted_tilt': converted_tilt, 'player_name': response.json()["name"]})
    else:
        return render(request, 'error.html', {'message': 'Player ID not provided'})

def index(request):
    return render(request, 'index.html')

def error(request):
    return render(request, 'error.html', {'message': 'An error occurred'})
