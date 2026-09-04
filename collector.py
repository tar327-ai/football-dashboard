import os
import json
import datetime
import requests

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

HEADERS = {
    "X-Auth-Token": API_KEY
}

# 참가자별 선수 및 팀 정보 설정
PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "search_names": ["Bukayo Saka", "Saka"], "team_name": "아스널", "team_id": 57, "league_code": "PL", "league_name": "EPL"},
    {"participant": "햆", "name": "주드 벨링엄", "search_names": ["Jude Bellingham", "Bellingham"], "team_name": "레알 마드리드", "team_id": 86, "league_code": "PD", "league_name": "LaLiga"},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "search_names": ["Håkon Arnar Haraldsson", "Haraldsson"], "team_name": "릴", "team_id": 521, "league_code": "FL1", "league_name": "Ligue 1"},

    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "search_names": ["Bruno Fernandes", "Fernandes"], "team_name": "맨체스터 유나이티드", "team_id": 66, "league_code": "PL", "league_name": "EPL"},
    {"participant": "갮", "name": "라민 야말", "search_names": ["Lamine Yamal", "Yamal"], "team_name": "바르셀로나", "team_id": 81, "league_code": "PD", "league_name": "LaLiga"},
    {"participant": "갮", "name": "메이슨 그린우드", "search_names": ["Mason Greenwood", "Greenwood"], "team_name": "마르세유", "team_id": 516, "league_code": "FL1", "league_name": "Ligue 1"},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "search_names": ["Rayan Cherki", "Cherki"], "team_name": "맨체스터 시티", "team_id": 65, "league_code": "PL", "league_name": "EPL"},
    {"participant": "돖", "name": "알렉스 바에나", "search_names": ["Álex Baena", "Alex Baena", "Baena"], "team_name": "아틀레티코 마드리드", "team_id": 78, "league_code": "PD", "league_name": "LaLiga"},
    {"participant": "돖", "name": "우스만 뎀벨레", "search_names": ["Ousmane Dembélé", "Dembele"], "team_name": "PSG", "team_id": 524, "league_code": "FL1", "league_name": "Ligue 1"}
]

# 영어 공식 팀명을 깔끔한 한글 팀명으로 매핑 (주요 구단 보완)
TEAM_NAME_KOR = {
    # LaLiga
    "Real Madrid CF": "레알 마드리드",
    "Club Atlético de Madrid": "아틀레티코 마드리드",
    "FC Barcelona": "바르셀로나",
    "Rayo Vallecano de Madrid": "라요 바예카노",
    "Real Sociedad de Fútbol": "레알 소시에다드",
    "Valencia CF": "발렌시아",
    "Sevilla FC": "세비야",
    "Villarreal CF": "비야레알",
    "Real Betis Balompié": "베티스",
    "Athletic Club": "아틀레틱 빌바오",
    "Girona FC": "지로나",
    "RCD Mallorca": "마요르카",
    "RC Celta de Vigo": "셀타 비고",
    "CA Osasuna": "오사수나",
    "Getafe CF": "헤타페",
    "RCD Espanyol de Barcelona": "에스파뇰",
    "Real Valladolid CF": "바야돌리드",
    "UD Las Palmas": "라스팔마스",
    "CD Leganés": "레가네스",
    "D. Alavés": "알라베스",

    # EPL
    "Arsenal FC": "아스널",
    "Manchester City FC": "맨체스터 시티",
    "Manchester United FC": "맨체스터 유나이티드",
    "Chelsea FC": "첼시",
    "Liverpool FC": "리버풀",
    "Tottenham Hotspur FC": "토트넘",
    "Everton FC": "에버튼",
    "Aston Villa FC": "애스턴 빌라",
    "Newcastle United FC": "뉴캐슬",
    "Brighton & Hove Albion FC": "브라이튼",
    "West Ham United FC": "웨스트햄",

    # Ligue 1
    "Paris Saint-Germain FC": "PSG",
    "Olympique de Marseille": "마르세유",
    "Lille OSC": "릴",
    "AS Monaco FC": "모나코",
    "Olympique Lyonnais": "리옹",
    "OGC Nice": "니스",
    "RC Lens": "랑스"
}

def clean_team_name(raw_name):
    """팀 이름 매핑 처리 및 가독성 개선"""
    if raw_name in TEAM_NAME_KOR:
        return TEAM_NAME_KOR[raw_name]
    # 매핑되지 않은 팀 이름에서 FC, CF 등 접미사 정리
    clean = raw_name.replace(" FC", "").replace(" CF", "").replace(" de Fútbol", "").strip()
    return clean

def fetch_league_standings(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    team_pts = {}
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            standings = data.get("standings", [])[0].get("table", [])
            for row in standings:
                team_pts[row["team"]["id"]] = row["points"]
    except Exception as e:
        print(f"[{league_code}] 승점 조회 오류:", e)
    return team_pts

def fetch_top_scorers_and_assists(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/scorers?limit=100"
    assists_map = {}
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("scorers", []):
                p_name = item.get("player", {}).get("name", "")
                ast = item.get("assists") or 0
                if p_name:
                    assists_map[p_name] = ast
    except Exception as e:
        print(f"[{league_code}] 어시스트 조회 오류:", e)
    return assists_map

def fetch_upcoming_matches(league_code):
    url = f"https://api.football-data.org/v4/competitions/{league_code}/matches?status=SCHEDULED"
    matches_by_team = {}
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # 경기 날짜순 정렬
            matches = sorted(data.get("matches", []), key=lambda x: x.get("utcDate", ""))
            
            for m in matches:
                utc_date = m.get("utcDate")
                if utc_date:
                    dt = datetime.datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                    kst_dt = dt.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
                    match_time_str = kst_dt.strftime("%m/%d %H:%M KST")
                else:
                    match_time_str = "일정 미정"

                home_id = m["homeTeam"]["id"]
                away_id = m["awayTeam"]["id"]
                
                home_name = clean_team_name(m["homeTeam"]["name"])
                away_name = clean_team_name(m["awayTeam"]["name"])

                match_info = {
                    "matchDate": match_time_str,
                    "homeTeam": home_name,
                    "awayTeam": away_name,
                    "matchSummary": f"{home_name} vs {away_name}"
                }

                # 각 팀별 가장 빠르게 다가오는 1경기만 수집
                if home_id not in matches_by_team:
                    matches_by_team[home_id] = match_info
                if away_id not in matches_by_team:
                    matches_by_team[away_id] = match_info
    except Exception as e:
        print(f"[{league_code}] 일정 조회 오류:", e)
    return matches_by_team

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    league_codes = ["PL", "PD", "FL1"]
    all_standings = {}
    all_assists = {}
    all_matches = {}

    for code in league_codes:
        all_standings.update(fetch_league_standings(code))
        all_assists.update(fetch_top_scorers_and_assists(code))
        all_matches.update(fetch_upcoming_matches(code))

    result_players = []
    for p in PLAYERS_CONFIG:
        pts = all_standings.get(p["team_id"], 0)

        ast = 0
        for api_pname, a_val in all_assists.items():
            for search_name in p["search_names"]:
                if search_name.lower() in api_pname.lower() or api_pname.lower() in search_name.lower():
                    ast = a_val
                    break
            if ast > 0:
                break

        next_match = all_matches.get(p["team_id"], {
            "matchDate": "일정 없음",
            "homeTeam": "-",
            "awayTeam": "-",
            "matchSummary": "예정된 리그 경기 없음"
        })

        result_players.append({
            "participant": p["participant"],
            "name": p["name"],
            "team": p["team_name"],
            "league": p["league_name"],
            "pts": pts,
            "assists": ast,
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

    print("data.json 업데이트 완료!")

if __name__ == "__main__":
    main()
