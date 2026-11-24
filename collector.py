import os
import json
import datetime
import time
import unicodedata
import requests

API_KEY = os.getenv("APIFOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

BASE_URL = "https://v3.football.api-sports.io"

# 리그 ID: EPL=39, LaLiga=140, Ligue 1=61
LEAGUE_IDS = [39, 140, 61]

PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "search_names": ["Bukayo Saka", "Saka"], "team_name": "아스널", "league_id": 39, "league_name": "EPL", "player_id": 1460, "team_id": 42},
    {"participant": "햆", "name": "주드 벨링엄", "search_names": ["Jude Bellingham", "Bellingham"], "team_name": "레알 마드리드", "league_id": 140, "league_name": "LaLiga", "player_id": 138810, "team_id": 541},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "search_names": ["Hakon Arnar Haraldsson", "Haraldsson", "Hakon"], "team_name": "릴", "league_id": 61, "league_name": "Ligue 1", "player_id": 129712, "team_id": 79},

    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "search_names": ["Bruno Fernandes", "Fernandes"], "team_name": "맨체스터 유나이티드", "league_id": 39, "league_name": "EPL", "player_id": 1485, "team_id": 33},
    {"participant": "갮", "name": "라민 야말", "search_names": ["Lamine Yamal", "Yamal"], "team_name": "바르셀로나", "league_id": 140, "league_name": "LaLiga", "player_id": 382848, "team_id": 529},
    {"participant": "갮", "name": "메이슨 그린우드", "search_names": ["Mason Greenwood", "Greenwood"], "team_name": "마르세유", "league_id": 61, "league_name": "Ligue 1", "player_id": 152982, "team_id": 81},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "search_names": ["Rayan Cherki", "Cherki"], "team_name": "맨체스터 시티", "league_id": 39, "league_name": "EPL", "player_id": 158079, "team_id": 50},
    {"participant": "돖", "name": "알렉스 바에나", "search_names": ["Alex Baena", "Baena"], "team_name": "아틀레티코 마드리드", "league_id": 140, "league_name": "LaLiga", "player_id": 128911, "team_id": 530},
    {"participant": "돖", "name": "우스만 뎀벨레", "search_names": ["Ousmane Dembele", "Dembele"], "team_name": "PSG", "league_id": 61, "league_name": "Ligue 1", "player_id": 2164, "team_id": 85}
]

TEAM_NAME_KOR = {
    "Real Madrid": "레알 마드리드",
    "Atletico Madrid": "아틀레티코 마드리드",
    "Barcelona": "바르셀로나",
    "Rayo Vallecano": "라요 바예카노",
    "Real Sociedad": "레알 소시에다드",
    "Valencia": "발렌시아",
    "Sevilla": "세비야",
    "Villarreal": "비야레알",
    "Real Betis": "베티스",
    "Athletic Club": "아틀레틱 빌바오",
    "Girona": "지로나",
    "Mallorca": "마요르카",
    "Celta Vigo": "셀타 비고",
    "Osasuna": "오사수나",
    "Getafe": "헤타페",
    "Espanyol": "에스파뇰",
    "Valladolid": "바야돌리드",
    "Las Palmas": "라스팔마스",
    "Leganes": "레가네스",
    "Alaves": "알라베스",
    "Arsenal": "아스널",
    "Manchester City": "맨체스터 시티",
    "Manchester United": "맨체스터 유나이티드",
    "Chelsea": "첼시",
    "Liverpool": "리버풀",
    "Tottenham": "토트넘",
    "Everton": "에버튼",
    "Aston Villa": "애스턴 빌라",
    "Newcastle": "뉴캐슬",
    "Brighton": "브라이튼",
    "West Ham": "웨스트햄",
    "Paris Saint Germain": "PSG",
    "Marseille": "마르세유",
    "Lille": "릴",
    "Monaco": "모나코",
    "Lyon": "리옹",
    "Nice": "니스",
    "Lens": "랑스"
}


def normalize_text(text):
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return stripped.lower().strip()


def get_current_season():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9)))
    return now.year if now.month >= 7 else now.year - 1


def load_existing_players():
    if os.path.exists("data.json"):
        try:
            with open("data.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return {p["name"]: p for p in data.get("players", [])}
        except Exception:
            return {}
    return {}


def fetch_team_standings(league_id, season):
    url = f"{BASE_URL}/standings"
    params = {"league": league_id, "season": season}
    team_pts = {}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            resp = data.get("response", [])
            if resp:
                standings = resp[0]["league"]["standings"][0]
                for row in standings:
                    team_pts[row["team"]["id"]] = row["points"]
    except Exception as e:
        print(f"[Standings {league_id}] 오류:", e)
    return team_pts


def extract_league_assists_from_entry(entry, league_id):
    stats_list = entry.get("statistics", [])
    total = 0
    found = False
    for st in stats_list:
        if st.get("league", {}).get("id") == league_id:
            ast = st.get("goals", {}).get("assists")
            total += (ast if ast is not None else 0)
            found = True
    return found, total


def fetch_assists_by_player_id(player_id, league_id, season):
    url = f"{BASE_URL}/players"
    params = {"id": player_id, "league": league_id, "season": season}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            resp = data.get("response", [])
            if resp:
                return extract_league_assists_from_entry(resp[0], league_id)
    except Exception as e:
        print(f"[Player ID {player_id}] 오류:", e)
    return False, 0


def fetch_assists_by_team_name(team_id, league_id, season, search_names):
    """ID 조회가 비어 있을 때 팀·리그·시즌 스쿼드에서 이름으로 어시스트 검색"""
    norm_targets = [normalize_text(n) for n in search_names if n]
    page = 1
    while page <= 3:
        url = f"{BASE_URL}/players"
        params = {"team": team_id, "league": league_id, "season": season, "page": page}
        try:
            res = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if res.status_code != 200:
                break
            data = res.json()
            resp = data.get("response", [])
            if not resp:
                break

            for entry in resp:
                p_info = entry.get("player", {})
                candidates = [
                    normalize_text(p_info.get("name", "")),
                    normalize_text(p_info.get("firstname", "")),
                    normalize_text(p_info.get("lastname", "")),
                    normalize_text(f"{p_info.get('firstname', '')} {p_info.get('lastname', '')}")
                ]
                matched = any(
                    t and any(t == c or t in c for c in candidates if c)
                    for t in norm_targets
                )
                if matched:
                    found, total = extract_league_assists_from_entry(entry, league_id)
                    if found:
                        return True, total

            paging = data.get("paging", {})
            cur_page = paging.get("current", page)
            total_pages = paging.get("total", page)
            if cur_page >= total_pages:
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            print(f"[Team Squad {team_id} p.{page}] 오류:", e)
            break
    return False, 0


def fetch_next_match(team_id, league_id):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "league": league_id, "next": 1}
    kst = datetime.timezone(datetime.timedelta(hours=9))
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        if res.status_code == 200:
            data = res.json()
            resp = data.get("response", [])
            if resp:
                m = resp[0]
                utc_date = m["fixture"]["date"]
                dt = datetime.datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                match_time_str = dt.astimezone(kst).strftime("%m/%d %H:%M KST")

                home_raw = m["teams"]["home"]["name"]
                away_raw = m["teams"]["away"]["name"]
                home_name = TEAM_NAME_KOR.get(home_raw, home_raw)
                away_name = TEAM_NAME_KOR.get(away_raw, away_raw)

                return {
                    "matchDate": match_time_str,
                    "homeTeam": home_name,
                    "awayTeam": away_name,
                    "matchSummary": f"{home_name} vs {away_name}"
                }
    except Exception as e:
        print(f"[Fixture Team {team_id}] 오류:", e)
    return None


def main():
    if not API_KEY:
        raise RuntimeError("APIFOOTBALL_KEY 환경변수가 설정되지 않았습니다.")

    kst = datetime.timezone(datetime.timedelta(hours=9))
    now = datetime.datetime.now(kst)
    season = get_current_season()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    existing_map = load_existing_players()

    standings_map = {}
    for l_id in LEAGUE_IDS:
        standings_map.update(fetch_team_standings(l_id, season))
        time.sleep(0.4)

    result_players = []
    for p in PLAYERS_CONFIG:
        prev_player = existing_map.get(p["name"], {})

        if p["team_id"] in standings_map:
            pts = standings_map[p["team_id"]]
        else:
            pts = prev_player.get("pts", 0)

        ok, ast_val = fetch_assists_by_player_id(p["player_id"], p["league_id"], season)
        if not ok:
            time.sleep(0.3)
            ok, ast_val = fetch_assists_by_team_name(
                p["team_id"], p["league_id"], season, p.get("search_names", [])
            )

        prev_ast = prev_player.get("assists", 0)
        final_ast = max(ast_val, prev_ast) if ok else prev_ast
        time.sleep(0.4)

        next_match = fetch_next_match(p["team_id"], p["league_id"])
        if not next_match:
            next_match = prev_player.get("nextMatch") or {
                "matchDate": "일정 없음",
                "homeTeam": "-",
                "awayTeam": "-",
                "matchSummary": "예정된 리그 경기 없음"
            }
        time.sleep(0.4)

        result_players.append({
            "participant": p["participant"],
            "name": p["name"],
            "team": p["team_name"],
            "league": p["league_name"],
            "pts": pts,
            "assists": final_ast,
            "nextMatch": next_match
        })

    output_data = {
        "metadata": {
            "dataDate": data_date,
            "lastUpdated": last_updated
        },
        "players": result_players
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"data.json 업데이트 완료 ({season} 시즌 기준)")


if __name__ == "__main__":
    main()
