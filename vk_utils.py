import requests
import os

VK_GROUP_ID = os.getenv("VK_GROUP_ID")
VK_TOKEN = os.getenv("VK_ACCESS_TOKEN")

def check_vk_subscription(username):
    url = "https://api.vk.com/method/groups.isMember"
    params = {
        "group_id": VK_GROUP_ID,
        "user_id": username,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        return data.get("response", 0) == 1
    except:
        return False