import os
import requests
from dotenv import load_dotenv
load_dotenv()

url = f"https://api.brawlstars.com/v1/events/rotation"
headers = {
        "Authorization": "Bearer " + os.getenv("API_KEY")
    }
response = requests.get(url, headers=headers)
print(response.json())