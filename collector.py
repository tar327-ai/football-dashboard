import os
import json
import datetime
import requests

# GitHub Secrets에 등록한 API KEY 로드
API_KEY = os.getenv("FOOTBALL_DATA_API_KEY")

HEADERS = {
    "X-Auth-Token": API_KEY
}

# 참가자별 선수/팀 매핑 설정
# EPL (PL), LaLiga (PD), Ligue 1 (FL1)
PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "team_id": 57, "league_code": "PL", "league_name": "EPL"},           # Arsenal
    {"participant": "햆", "name": "주드 벨링엄", "team_id": 86, "league_code": "PD", "league_name": "LaLiga"},       # Real Madrid
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "team_id": 521, "league_code": "FL1", "league_name": "Ligue 1"}, # Lille

    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "team_id": 66, "league_code": "PL", "league_name": "EPL"},      # Manchester United
    {"participant": "갮", "name": "라민 야말", "team_id": 81, "league_code": "PD", "league_name": "LaLiga"},          # FC Barcelona
    {"participant": "갮", "name": "메이슨 그린우드", "team_id": 516, "league_code": "FL1", "league_name": "Ligue 1"},   # Marseille

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "team_id": 65, "league_code": "PL", "league_name": "EPL"},          # Manchester City
    {"participant": "돖", "name": "알렉스 바에나", "team_id": 78, "league_code": "PD", "league_name": "LaLiga"},      # Atletico Madrid
    {"participant": "돖", "name": "우스만 뎀벨레", "team_id": 524, "league_code": "FL1", "league_name": "Ligue 1"}   # PSG
]

def fetch_league_standings(league_code):
    """리그별 팀 순위 및 승점 수집"""
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
        else:
            print(f"[{league_code}] API 호출 오류 (Status: {res.status_code})")
    except Exception as e:
        print(f"[{league_code}] 네트워크 에러:", e)
        
    return team_pts

def fetch_top_scorers(league_code):
    """리그별 개인 기록(어시스트/득점) 수집"""
    url = f"https://api.football-data.org/v4/competitions/{league_code}/scorers"
    assists_map = {}
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            scorers = data.get("scorers", [])
            for item in scorers:
                p_name = item["player"]["name"]
                # 무료 플랜 API 제공 필드에 따른 어시스트/득점 파싱
                assists = item.get("assists") or 0
                assists_map[p_name] = assists
    except Exception as e:
        print(f"[{league_code}] 어시스트 조회 에러:", e)

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
        all_assists.update(fetch_top_scorers(code))

    print(f"수집된 팀 승점 정보 수: {len(all_standings)}개")

    result_players = []
    for p in PLAYERS_CONFIG:
        # 1. 승점 매칭 (Team ID 기반 100% 정확 매칭)
        pts = all_standings.get(p["team_id"], 0)

        # 2. 어시스트 매칭
        ast = 0
        for name, a_val in all_assists.items():
            if p["name"] in name or name in p["name"]:
                ast = a_val
                break

        result_players.append({
            "participant": p["participant"],
            "name": p["name"],
            "team": p["team_id"], # UI 연동용
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

    print("Football-Data API 연동 성공! data.json 정상 업데이트되었습니다.")

if __name__ == "__main__":
    main()
