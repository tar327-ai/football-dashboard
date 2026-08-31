import json
import datetime
import requests

# 네이버 해외 IP / 크롤러 차단을 완벽히 회피하는 헤더 세팅
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Referer': 'https://m.sports.naver.com/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
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

def fetch_league_data(category):
    team_pts = {}
    player_assists = {}

    # 네이버 해외 IP 차단 대비용 엔드포인트 세팅
    url_team = f"https://sports.news.naver.com/wfootball/record/teamRank?category={category}"
    url_assist = f"https://sports.news.naver.com/wfootball/record/playerRank?category={category}&recordType=assist"

    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        
        # 메인 페이지 접속으로 쿠키 획득
        session.get("https://m.sports.naver.com/", timeout=5)

        # 1. 승점 수집
        r_team = session.get(url_team, timeout=10)
        if r_team.status_code == 200 and r_team.text.strip().startswith('{'):
            data = r_team.json()
            records = data.get('recordList', []) or data.get('regularTeamRecordList', [])
            for item in records:
                t_name = item.get('teamName', '')
                pts = item.get('gainGoal') if item.get('gainGoal') is not None else item.get('pts', 0)
                if t_name:
                    team_pts[t_name] = int(pts)

        # 2. 어시스트 수집
        r_assist = session.get(url_assist, timeout=10)
        if r_assist.status_code == 200 and r_assist.text.strip().startswith('{'):
            data = r_assist.json()
            records = data.get('recordList', [])
            for item in records:
                p_name = item.get('playerName', '')
                ast = item.get('assist', 0)
                if p_name:
                    player_assists[p_name] = int(ast)

    except Exception as e:
        print(f"[{category}] 데이터 수집 실패: {e}")

    return team_pts, player_assists

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    categories = ["epl", "primera", "ligue1"]
    all_teams = {}
    all_assists = {}

    for cat in categories:
        t_data, a_data = fetch_league_data(cat)
        all_teams.update(t_data)
        all_assists.update(a_data)

    print("수집된 승점 데이터 개수:", len(all_teams))
    print("수집된 어시스트 데이터 개수:", len(all_assists))

    result_players = []
    for p in PLAYERS_CONFIG:
        pts = 0
        for t_name, t_pts in all_teams.items():
            if p["team"] in t_name or t_name in p["team"]:
                pts = t_pts
                break

        ast = 0
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

    print("data.json 정상 갱신 완료!")

if __name__ == "__main__":
    main()
