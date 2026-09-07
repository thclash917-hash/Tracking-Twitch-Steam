import os
import time
import random
import requests
import json
import urllib.parse

CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")


# ---------------------------------------------------------------------------
# Utilitaires communs
# ---------------------------------------------------------------------------

def load_old_data():
    """Charge le game.json existant, indexé par (plateforme, nom) pour éviter
    les collisions entre un jeu qui existe à la fois côté Twitch et côté Mobile/Steam."""
    old_data = {}
    if os.path.exists("game.json"):
        try:
            with open("game.json", "r", encoding="utf-8") as f:
                old_list = json.load(f)
                for item in old_list:
                    key = (item.get("platform"), item.get("name"))
                    old_data[key] = item
        except Exception:
            pass
    return old_data


def compute_variation(old_data, platform, name, raw_metric):
    key = (platform, name)
    old_item = old_data.get(key, {})
    old_metric = old_item.get("raw_viewers", raw_metric)
    if old_metric == 0:
        old_metric = raw_metric
    variation_val = round(((raw_metric - old_metric) / old_metric) * 100, 1) if old_metric > 0 else 0.0
    variation_str = f"+{variation_val}%" if variation_val >= 0 else f"{variation_val}%"
    return variation_val, variation_str


def get_app_info(name):
    """Récupère l'icône ET le lien App Store officiel via l'API publique iTunes Search."""
    try:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": name, "country": "fr", "entity": "software", "limit": 1},
            timeout=10
        )
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                icon = results[0].get("artworkUrl512") or results[0].get("artworkUrl100")
                store_url = results[0].get("trackViewUrl")
                return icon, store_url
    except Exception:
        pass
    return None, None


# ---------------------------------------------------------------------------
# TWITCH — logique originale INCHANGÉE (seul ajout : le champ "url" pour le
# bouton "lien direct" dans la fiche détail, aucune valeur/catégorisation modifiée)
# ---------------------------------------------------------------------------

def get_twitch_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    url = "https://id.twitch.tv/oauth2/token"
    params = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    response = requests.post(url, params=params)
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def fetch_twitch_games():
    token = get_twitch_token()
    if not token:
        print("Erreur : Impossible d'obtenir le token Twitch.")
        return []

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": f"Bearer {token}"
    }

    results = []
    old_data = {}
    if os.path.exists("game.json"):
        try:
            with open("game.json", "r", encoding="utf-8") as f:
                old_list = json.load(f)
                old_data = {item["name"]: item for item in old_list}
        except:
            pass

    # Récupérer les top jeux de Twitch (pagination pour obtenir un grand nombre de catégories, ex: 100)
    top_games_url = "https://api.twitch.tv/helix/games/top?first=100"
    response = requests.get(top_games_url, headers=headers)

    if response.status_code != 200:
        print("Erreur lors de la récupération du top Twitch.")
        return []

    twitch_games = response.json().get("data", [])

    for game in twitch_games:
        game_name = game["name"]
        game_id = game["id"]

        # Formater l'image Twitch correctement (remplacement des dimensions)
        image_url = game.get("box_art_url", "").replace("{width}", "300").replace("{height}", "400")

        # Récupérer les streams en direct pour compter les spectateurs réels
        streams_url = f"https://api.twitch.tv/helix/streams?game_id={game_id}&first=100"
        streams_resp = requests.get(streams_url, headers=headers)

        viewers = 0
        if streams_resp.status_code == 200:
            streams = streams_resp.json().get("data", [])
            viewers = sum(stream["viewer_count"] for stream in streams)

        # Déterminer la plateforme selon le jeu (personnalisable)
        platform = "Twitch"
        if game_name in ["Counter-Strike 2", "Elden Ring"]:
            platform = "Steam"
        elif game_name in ["Brawl Stars", "Clash of Clans"]:
            platform = "Mobile"
        elif game_name in ["Roblox", "VALORANT"]:
            platform = "PC/Mobile" if game_name == "Roblox" else "PC"

        # Gestion spécifique des stats globales si l'API Twitch ne suffit pas (ex: Roblox ou CS2)
        if game_name == "Roblox":
            # Si tu veux un volume de joueurs global simulé/estimé combiné
            viewers_or_players = max(viewers, 2500000) # Estimation réaliste ou vraie source si disponible
            formatted_volume = f"{viewers_or_players:,} joueurs".replace(",", " ")
            raw_metric = viewers_or_players
        elif game_name == "Counter-Strike 2":
            viewers_or_players = max(viewers, 850000)
            formatted_volume = f"{viewers_or_players:,} joueurs".replace(",", " ")
            raw_metric = viewers_or_players
        else:
            raw_metric = viewers
            formatted_volume = f"{viewers:,} spectateurs".replace(",", " ")

        # Calcul de la variation
        old_item = old_data.get(game_name, {})
        old_metric = old_item.get("raw_viewers", raw_metric)
        if old_metric == 0:
            old_metric = raw_metric

        variation_val = round(((raw_metric - old_metric) / old_metric) * 100, 1) if old_metric > 0 else 0.0
        variation_str = f"+{variation_val}%" if variation_val >= 0 else f"{variation_val}%"

        game_url = f"https://www.twitch.tv/directory/game/{urllib.parse.quote(game_name)}"

        results.append({
            "name": game_name,
            "platform": platform,
            "raw_viewers": raw_metric,
            "volume": formatted_volume,
            "variationValue": variation_val,
            "variation": variation_str,
            "image": image_url,
            "url": game_url
        })

    return results


# ---------------------------------------------------------------------------
# STEAM — via l'API publique SteamSpy (gratuite, sans clé)
# ---------------------------------------------------------------------------

def fetch_steam_games():
    old_data = load_old_data()
    results = []

    try:
        url = "https://steamspy.com/api.php?request=top100in2weeks"
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if response.status_code != 200:
            print("Erreur SteamSpy:", response.status_code)
            return []
        data = response.json()
    except Exception as e:
        print("Erreur lors de la récupération SteamSpy:", e)
        return []

    games_list = list(data.values())
    games_list.sort(key=lambda g: g.get("ccu", 0), reverse=True)

    for game in games_list[:20]:
        appid = game.get("appid")
        name = game.get("name", "Inconnu")
        ccu = game.get("ccu", 0)

        image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{appid}/header.jpg"
        store_url = f"https://store.steampowered.com/app/{appid}"

        variation_val, variation_str = compute_variation(old_data, "Steam", name, ccu)

        results.append({
            "name": name,
            "platform": "Steam",
            "raw_viewers": ccu,
            "volume": f"{ccu:,} joueurs en jeu".replace(",", " "),
            "variationValue": variation_val,
            "variation": variation_str,
            "image": image_url,
            "url": store_url
        })

    return results


# ---------------------------------------------------------------------------
# MOBILE — liste organisée + vraies icônes/liens via iTunes Search API
# Pas d'API gratuite de classement mobile en temps réel : on applique une
# petite fluctuation simulée (±3%) à chaque run pour donner un effet vivant.
# ---------------------------------------------------------------------------

MOBILE_GAMES_POOL = [
    ("Brawl Stars", 12500000),
    ("Clash of Clans", 9800000),
    ("Clash Royale", 8600000),
    ("PUBG MOBILE", 15200000),
    ("Free Fire", 21000000),
    ("Mobile Legends: Bang Bang", 13400000),
    ("Candy Crush Saga", 11200000),
    ("Genshin Impact", 7300000),
    ("Roblox", 25000000),
    ("Call of Duty: Mobile", 9700000),
    ("Subway Surfers", 8100000),
    ("Honkai: Star Rail", 4200000),
    ("Pokémon GO", 6100000),
    ("Among Us", 3900000),
    ("Coin Master", 5200000),
    ("Toon Blast", 3600000),
    ("Royal Match", 4800000),
    ("EA Sports FC Mobile", 5300000),
    ("Stumble Guys", 4400000),
    ("8 Ball Pool", 3800000),
    ("Fortnite", 6700000),
    ("Minecraft", 7900000),
    ("Wild Rift", 5100000),
    ("Garena Free Fire MAX", 6800000),
    ("Homescapes", 3300000),
]


def fetch_mobile_games():
    old_data = load_old_data()
    results = []

    for name, base_volume in MOBILE_GAMES_POOL:
        old_item = old_data.get(("Mobile", name), {})
        previous_volume = old_item.get("raw_viewers", base_volume)

        # Fluctuation simulée (pas de vraie API gratuite de temps réel pour le mobile)
        fluctuation_pct = round(random.uniform(-3, 3), 1)
        new_volume = max(int(previous_volume * (1 + fluctuation_pct / 100)), 1)

        variation_val, variation_str = compute_variation(old_data, "Mobile", name, new_volume)

        icon_url, store_url = get_app_info(name)
        if not icon_url:
            icon_url = f"https://api.dicebear.com/7.x/shapes/svg?seed={name.replace(' ', '')}"
        if not store_url:
            store_url = f"https://www.google.com/search?q={urllib.parse.quote(name + ' jeu mobile')}"

        results.append({
            "name": name,
            "platform": "Mobile",
            "raw_viewers": new_volume,
            "volume": f"{new_volume:,} joueurs actifs (estimation)".replace(",", " "),
            "variationValue": variation_val,
            "variation": variation_str,
            "image": icon_url,
            "url": store_url
        })

        time.sleep(0.5)  # éviter de spammer l'API iTunes

    return results


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    twitch_games = fetch_twitch_games()
    steam_games = fetch_steam_games()
    mobile_games = fetch_mobile_games()

    updated_games = twitch_games + steam_games + mobile_games

    if updated_games:
        with open("game.json", "w", encoding="utf-8") as f:
            json.dump(updated_games, f, ensure_ascii=False, indent=4)
        print(f"Fichier game.json mis à jour avec succès ({len(updated_games)} jeux/catégories) !")
        print(f" - Twitch : {len(twitch_games)}")
        print(f" - Steam  : {len(steam_games)}")
        print(f" - Mobile : {len(mobile_games)}")
    else:
        print("Erreur lors de la mise à jour.")
