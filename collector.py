import os
import json
import datetime
import requests

API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

HEADERS = {
    "X-Auth-Token": API_KEY
}

# 팀 ID/선수 영문명 매칭 설정
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

def fetch_league_standings(league_code):
    """리그별 팀 승점 수집"""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
    team_pts = {}
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            standings = data.get("standings", [])[0].get("table", [])
            for row in standings:
                team_id = row["team"]["id"]
                pts = row["points"]
                team_pts[team_id] = pts
    except Exception as e:
        print(f"[{league_code}] 승점 조회 오류:", e)
        
    return team_pts

def fetch_top_scorers_and_assists(league_code):
    """리그별 개인 기록(어시스트) 수집"""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/scorers?limit=100"
    assists_map = {}
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            scorers = data.get("scorers", [])
            for item in scorers:
                p_name = item.get("player", {}).get("name", "")
                ast = item.get("assists") or 0
                if p_name:
                    assists_map[p_name] = ast
    except Exception as e:
        print(f"[{league_code}] 어시스트 조회 오류:", e)

    return assists_map

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    league_codes = ["PL", "PD", "FL1"]
    all_standings = {}
    all_assists = {}

    for code in league_codes:
        all_standings.update(fetch_league_standings(code))
        all_assists.update(fetch_top_scorers_and_assists(code))

    result_players = []
    for p in PLAYERS_CONFIG:
        # 1. 승점 매칭
        pts = all_standings.get(p["team_id"], 0)

        # 2. 어시스트 매칭 (영문/유사 이름 체크)
        ast = 0
        for api_pname, a_val in all_assists.items():
            for search_name in p["search_names"]:
                if search_name.lower() in api_pname.lower() or api_pname.lower() in search_name.lower():
                    ast = a_val
                    break
            if ast > 0:
                break

        result_players.append({
            "participant": p["participant"],
            "name": p["name"],
            "team": p["team_name"],  # ID 번호 대신 한글 팀 이름으로 수정
            "league": p["league_name"],
            "pts": pts,
            "assists": ast
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

    print("data.json 정제 업데이트 완료!")

if __name__ == "__main__":
    main()
