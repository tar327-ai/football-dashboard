import json
import datetime
import requests

# 네이버 차단을 방지하기 위한 헤더 세팅
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://m.sports.naver.com/wfootball/index',
    'Accept': 'application/json, text/plain, */*'
}

PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "team": "아스널", "league": "EPL", "category": "epl"},
    {"participant": "햆", "name": "주드 벨링엄", "team": "레알 마드리드", "league": "LaLiga", "category": "primera"},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "team": "릴", "league": "Ligue 1", "category": "ligue1"},
    
    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "team": "맨체스터 유나이티드", "league": "EPL", "category": "epl"},
    {"participant": "갮", "name": "라민 야말", "team": "바르셀로나", "league": "LaLiga", "category": "primera"},
    {"participant": "갮", "name": "메이슨 그린우드", "team": "마르세유", "league": "Ligue 1", "category": "ligue1"},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "team": "맨체스터 시티", "league": "EPL", "category": "epl"},
    {"participant": "돖", "name": "알렉스 바에나", "team": "아틀레티코 마드리드", "league": "LaLiga", "category": "primera"},
    {"participant": "돖", "name": "우스만 뎀벨레", "team": "PSG", "league": "Ligue 1", "category": "ligue1"}
]

def fetch_data_from_naver(category):
    team_pts = {}
    player_assists = {}

    # 1. 팀 순위/승점 (모바일 API 우선 시도 후 웹 API 백업)
    urls_team = [
        f"https://sports.news.naver.com/wfootball/record/teamRank?category={category}",
        f"https://sports.news.naver.com/wfootball/record/teamRank.nhn?category={category}"
    ]

    for url in urls_team:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # 다양한 JSON 구조 대응
                records = data.get('recordList', []) or data.get('regularTeamRecordList', [])
                for item in records:
                    t_name = item.get('teamName') or item.get('name', '')
                    # gainGoal 필드가 보통 승점(pts)으로 전달되는 네이버 구조 대응
                    pts = item.get('gainGoal') if item.get('gainGoal') is not None else item.get('pts', 0)
                    if t_name:
                        team_pts[t_name] = int(pts)
                if team_pts:
                    break
        except Exception as e:
            print(f"[{category}] 팀 승점 가져오기 실패: {e}")

    # 2. 어시스트 수집
    urls_assist = [
        f"https://sports.news.naver.com/wfootball/record/playerRank?category={category}&recordType=assist",
        f"https://sports.news.naver.com/wfootball/record/playerRank.nhn?category={category}&recordType=assist"
    ]

    for url in urls_assist:
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 200:
                data = res.json()
                records = data.get('recordList', [])
                for item in records:
                    p_name = item.get('playerName') or item.get('name', '')
                    ast = item.get('assist', 0)
                    if p_name:
                        player_assists[p_name] = int(ast)
                if player_assists:
                    break
        except Exception as e:
            print(f"[{category}] 어시스트 가져오기 실패: {e}")

    return team_pts, player_assists

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    categories = ["epl", "primera", "ligue1"]
    all_teams = {}
    all_assists = {}

    for cat in categories:
        t_data, a_data = fetch_data_from_naver(cat)
        all_teams.update(t_data)
        all_assists.update(a_data)

    print("수집된 팀 승점 데이터:", all_teams)
    print("수집된 어시스트 데이터:", all_assists)

    result_players = []
    for p in PLAYERS_CONFIG:
        pts = 0
        # 유연한 팀명 매칭 (예: '아스널' - '아스널 FC')
        for t_name, t_pts in all_teams.items():
            if p["team"] in t_name or t_name in p["team"]:
                pts = t_pts
                break

        ast = 0
        # 유연한 이름 매칭
        for a_name, a_ast in all_assists.items():
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

    print("data.json 저장 성공!")

if __name__ == "__main__":
    main()
