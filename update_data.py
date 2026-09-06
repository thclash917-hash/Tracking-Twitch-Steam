import os
import json
import requests

TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")

def get_twitch_access_token():
    url = f"https://id.twitch.tv/oauth2/token?client_id={TWITCH_CLIENT_ID}&client_secret={TWITCH_CLIENT_SECRET}&grant_type=client_credentials"
    response = requests.post(url)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def fetch_twitch_games():
    token = get_twitch_access_token()
    if not token:
        return []
    
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    
    # Demande des 100 catégories les plus populaires sur Twitch
    url = "https://api.twitch.tv/helix/games/top?first=100"
    response = requests.get(url, headers=headers)
    
    games = []
    if response.status_code == 200:
        data = response.json().get("data", [])
        for item in data:
            box_art = item.get("box_art_url", "").replace("{width}", "100").replace("{height}", "133")
            games.append({
                "name": item.get("name"),
                "platform": "Twitch",
                "image": box_art,
                "volume": "Spectateurs en direct"
            })
    return games

def main():
    twitch_games = fetch_twitch_games()
    
    steam_games = [
        {"name": "Counter-Strike 2", "platform": "Steam", "image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/730/header.jpg", "volume": "1 084 344 joueurs"},
        {"name": "Dota 2", "platform": "Steam", "image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/570/header.jpg", "volume": "765 773 joueurs"},
        {"name": "PUBG: BATTLEGROUNDS", "platform": "Steam", "image": "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/578080/header.jpg", "volume": "212 048 joueurs"},
        {"name": "Brawl Stars", "platform": "Mobile/Cross", "image": "https://picsum.photos/100/133?random=brawl", "volume": "Prioritaire"},
        {"name": "Roblox", "platform": "PC/Mobile", "image": "https://picsum.photos/100/133?random=roblox", "volume": "Prioritaire"},
        {"name": "Clash of Clans", "platform": "Mobile", "image": "https://picsum.photos/100/133?random=coc", "volume": "Prioritaire"}
    ]

    all_games = steam_games + twitch_games

    with open("game.json", "w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=4)
    print(f"Succès : {len(all_games)} jeux/catégories enregistrés dans game.json")

if __name__ == "__main__":
    main()
