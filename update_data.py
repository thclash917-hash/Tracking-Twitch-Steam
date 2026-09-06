def fetch_twitch_games():
    token = get_twitch_access_token()
    if not token:
        return []
    
    headers = {
        "Client-ID": TWITCH_CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }
    
    # On demande 100 catégories au lieu de 50
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
