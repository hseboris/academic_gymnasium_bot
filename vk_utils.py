import requests
import os

VK_GROUP_ID = os.getenv("VK_GROUP_ID")
VK_TOKEN = os.getenv("VK_ACCESS_TOKEN")

def resolve_vk_id(username):
    if username.startswith("@"):
        username = username[1:]
    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": username,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        if "response" in data:
            return data["response"][0]["id"]
    except:
        pass
    return None

def check_vk_subscription(vk_user_id):
    url = "https://api.vk.com/method/groups.isMember"
    params = {
        "group_id": VK_GROUP_ID,
        "user_id": vk_user_id,
        "access_token": VK_TOKEN,
        "v": "5.131"
    }
    try:
        r = requests.get(url, params=params)
        data = r.json()
        return data.get("response", 0) == 1
    except:
        return False