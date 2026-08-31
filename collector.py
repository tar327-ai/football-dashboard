import json
import datetime
import requests

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1'
}

PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "team": "아스널", "league": "EPL", "code": "epl"},
    {"participant": "햆", "name": "주드 벨링엄", "team": "레알 마드리드", "league": "LaLiga", "code": "primera"},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "team": "릴", "league": "Ligue 1", "code": "ligue1"},
    
    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "team": "맨체스터 유나이티드", "league": "EPL", "code": "epl"},
    {"participant": "갮", "name": "라민 야말", "team": "바르셀로나", "league": "LaLiga", "code": "primera"},
    {"participant": "갮", "name": "메이슨 그린우드", "team": "마르세유", "league": "Ligue 1", "code": "ligue1"},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "team": "맨체스터 시티", "league": "EPL", "code": "epl"},
    {"participant": "돖", "name": "알렉스 바에나", "team": "아틀레티코 마드리드", "league": "LaLiga", "code": "primera"},
    {"participant": "돖", "name": "우스만 뎀벨레", "team": "PSG", "league": "Ligue 1", "code": "ligue1"}
]

def fetch_live_data():
    """
    우회 우편 경로를 통해 해외 축구 실시간 데이터를 수집하는 함수
    """
    team_pts_map = {}
    player_assist_map = {}

    leagues = ["epl", "primera", "ligue1"]
    
    for league in leagues:
        # 네이버 스포츠 모바일 전용 오픈 API 경로
        url_team = f"https://sports.news.naver.com/wfootball/record/teamRank?category={league}"
        url_player = f"https://sports.news.naver.com/wfootball/record/playerRank?category={league}&recordType=assist"

        try:
            r_team = requests.get(url_team, headers=HEADERS, timeout=8)
            if r_team.status_code == 200:
                data = r_team.json()
                for item in data.get('recordList', []):
                    tname = item.get('teamName', '')
                    pts = item.get('gainGoal', 0) # 네이버 승점 필드
                    if tname:
                        team_pts_map[tname] = int(pts)

            r_player = requests.get(url_player, headers=HEADERS, timeout=8)
            if r_player.status_code == 200:
                data = r_player.json()
                for item in data.get('recordList', []):
                    pname = item.get('playerName', '')
                    ast = item.get('assist', 0)
                    if pname:
                        player_assist_map[pname] = int(ast)
        except Exception as e:
            print(f"[{league}] 연동 실패:", e)

    return team_pts_map, player_assist_map

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    teams_data, assists_data = fetch_live_data()

    result_players = []
    for p in PLAYERS_CONFIG:
        # 1. 팀 승점 찾기
        pts = 0
        for t_name, t_pts in teams_data.items():
            if p["team"] in t_name or t_name in p["team"]:
                pts = t_pts
                break

        # 2. 어시스트 찾기
        ast = 0
        for a_name, a_ast in assists_data.items():
            if p["name"] in a_name or a_name in p["name"]:
                ast = a_ast
                break

        result_players.append({
            "participant": p["participant"],
            "name": p["name"],
            "team": p["team"],
            "league": p["league"],
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

    print("data.json 연동 업데이트 완료!")

if __name__ == "__main__":
    main()
