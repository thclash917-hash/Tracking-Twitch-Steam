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
    
    # 1. Récupérer les top catégories
    url_games = "https://api.twitch.tv/helix/games/top?first=100"
    res_games = requests.get(url_games, headers=headers)
    
    # 2. Récupérer les flux en direct pour sommer les spectateurs par jeu
    game_viewers = {}
    url_streams = "https://api.twitch.tv/helix/streams?first=100"
    res_streams = requests.get(url_streams, headers=headers)
    if res_streams.status_code == 200:
        for stream in res_streams.json().get("data", []):
            g_name = stream.get("game_name")
            v_count = stream.get("viewer_count", 0)
            game_viewers[g_name] = game_viewers.get(g_name, 0) + v_count

    games = []
    if res_games.status_code == 200:
        data = res_games.json().get("data", [])
        for item in data:
            name = item.get("name")
            box_art = item.get("box_art_url", "").replace("{width}", "100").replace("{height}", "133")
            viewers = game_viewers.get(name, 0)
            
            # Formatage du nombre de spectateurs
            if viewers > 0:
                volume_str = f"{viewers:,} spectateurs".replace(",", " ")
            else:
                volume_str = "Actif sur Twitch"

            games.append({
                "name": name,
                "platform": "Twitch",
                "image": box_art,
                "volume": volume_str,
                "raw_viewers": viewers
            })
            
    return games

def main():
    twitch_games = fetch_twitch_games()
    
    steam_games = [
        {"name": "Counter-Strike 2", "platform": "Steam", "image": "https://static-cdn.jtvnw.net/ttv-boxart/32399_IGDB-100x133.jpg", "volume": "1 084 344 joueurs", "raw_viewers": 1084344},
        {"name": "Dota 2", "platform": "Steam", "image": "https://static-cdn.jtvnw.net/ttv-boxart/29595_IGDB-100x133.jpg", "volume": "765 773 joueurs", "raw_viewers": 765773},
        {"name": "PUBG: BATTLEGROUNDS", "platform": "Steam", "image": "https://static-cdn.jtvnw.net/ttv-boxart/493057_IGDB-100x133.jpg", "volume": "212 048 joueurs", "raw_viewers": 212048},
        {"name": "Brawl Stars", "platform": "Mobile/Cross", "image": "https://static-cdn.jtvnw.net/ttv-boxart/512953_IGDB-100x133.jpg", "volume": "Jeu Mobile Populaire", "raw_viewers": 150000},
        {"name": "Roblox", "platform": "PC/Mobile", "image": "https://static-cdn.jtvnw.net/ttv-boxart/23020_IGDB-100x133.jpg", "volume": "Jeu Multijoueur", "raw_viewers": 300000},
        {"name": "Clash of Clans", "platform": "Mobile", "image": "https://static-cdn.jtvnw.net/ttv-boxart/15671_IGDB-100x133.jpg", "volume": "Jeu Mobile Populaire", "raw_viewers": 80000}
    ]

    all_games = steam_games + twitch_games

    with open("game.json", "w", encoding="utf-8") as f:
        json.dump(all_games, f, ensure_ascii=False, indent=4)
    print(f"Succès : {len(all_games)} jeux/catégories enregistrés dans game.json")

if __name__ == "__main__":
    main()
