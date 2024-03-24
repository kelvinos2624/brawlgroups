import requests
import os
from dotenv import load_dotenv, dotenv_values
from flask import Flask, redirect, url_for

load_dotenv()
app = Flask(__name__)

def authenticate(player):
    url = f"https://api.brawlstars.com/v1/players/%23{player}"
    headers = {
        "Authorization" : "Bearer " + os.getenv("API_KEY")
    }
    response = requests.get(url, headers=headers)
    return response

def find_tilted_brawlers(response):
    tilt = {}
    for entity in response.json()["brawlers"]:
        tilt[entity["name"]] = entity["highestTrophies"] - entity["trophies"]
    return dict(sorted(tilt.items(), key=lambda x:x[1], reverse=True))

def menu(response):
    print(f'Welcome {response.json()["name"]}!')
    print("Select an action: ")
    print("Tilted Stats [T]")
    print("Exit [X]")
    print("-----------------")

def main():
    response = authenticate(input("Player ID: #"))
    while True:    
        try:
            menu(response)
        except:
            print("Invalid, try again")
            response = authenticate(input("Player ID: #"))
            continue
        action = input("Action: ")
        if action.lower() == "t":
            converted_tilt = find_tilted_brawlers(response)
            for brawler in converted_tilt:
                if converted_tilt[brawler] > 0:
                    print(f'You are tilted {converted_tilt[brawler]} trophies with {brawler} lmao')
        elif action.lower() == "x":
            break
        elif action.lower() == "r":
            response = authenticate(input("Player ID: #"))

main()