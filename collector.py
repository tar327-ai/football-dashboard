import json
import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
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

def parse_naver_m_sports(category):
    team_pts = {}
    player_assists = {}

    # 네이버 모바일 웹 페이지 접속
    url = f"https://m.sports.naver.com/wfootball/record/index?category={category}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # HTML 내 포함된 JSON 데이터 추출 시도
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and '__NEXT_DATA__' in script.string:
                    json_data = json.loads(script.string)
                    props = json_data.get('props', {}).get('pageProps', {})
                    
                    # 팀 순위 데이터 파싱
                    standing_list = props.get('initialState', {}).get('record', {}).get('teamRank', [])
                    for t in standing_list:
                        t_name = t.get('teamName', '')
                        pts = t.get('pts', 0)
                        if t_name:
                            team_pts[t_name] = int(pts)
                            
                    # 어시스트 데이터 파싱
                    assist_list = props.get('initialState', {}).get('record', {}).get('playerRank', {}).get('assist', [])
                    for p in assist_list:
                        p_name = p.get('playerName', '')
                        ast = p.get('assist', 0)
                        if p_name:
                            player_assists[p_name] = int(ast)
                    break
    except Exception as e:
        print(f"[{category}] 파싱 오류:", e)

    return team_pts, player_assists

def main():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    categories = ["epl", "primera", "ligue1"]
    all_teams = {}
    all_assists = {}

    for cat in categories:
        t_data, a_data = parse_naver_m_sports(cat)
        all_teams.update(t_data)
        all_assists.update(a_data)

    print("수집된 팀 개수:", len(all_teams))
    print("수집된 어시스트 선수 개수:", len(all_assists))

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

    print("data.json 정상 저장 완료!")

if __name__ == "__main__":
    main()
