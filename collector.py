import json
import datetime
import requests
from bs4 import BeautifulSoup

# Headers to bypass naive bot detection
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# 9명 선수 및 소속팀 정보
PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "team": "아스널", "league": "EPL", "league_code": "epl"},
    {"participant": "햆", "name": "주드 벨링엄", "team": "레알 마드리드", "league": "LaLiga", "league_code": "primera"},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "team": "릴", "league": "Ligue 1", "league_code": "ligue1"},
    
    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "team": "맨체스터 유나이티드", "league": "EPL", "league_code": "epl"},
    {"participant": "갮", "name": "라민 야말", "team": "바르셀로나", "league": "LaLiga", "league_code": "primera"},
    {"participant": "갮", "name": "메이슨 그린우드", "team": "마르세유", "league": "Ligue 1", "league_code": "ligue1"},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "team": "맨체스터 시티", "league": "EPL", "league_code": "epl"},
    {"participant": "돖", "name": "알렉스 바에나", "team": "아틀레티코 마드리드", "league": "LaLiga", "league_code": "primera"},
    {"participant": "돖", "name": "우스만 뎀벨레", "team": "PSG", "league": "Ligue 1", "league_code": "ligue1"}
]

def fetch_league_standings(league_code):
    """
    네이버 스포츠 리그별 팀 승점 수집
    """
    url = f"https://sports.news.naver.com/wfootball/record/index?category={league_code}"
    standings = {}
    try:
        # 네이버 스포츠 내부 API/데이터 요청
        api_url = f"https://sports.news.naver.com/wfootball/record/teamRank?category={league_code}"
        res = requests.get(api_url, headers=HEADERS, timeout=10)
        data = res.json()
        
        # 팀명 및 승점(pts) 매핑
        for team in data.get('recordList', []):
            team_name = team.get('teamName')
            gain_pts = int(team.get('gainGoal', 0)) # 승점 필드
            standings[team_name] = gain_pts
    except Exception as e:
        print(f"[{league_code}] 팀 승점 수집 실패: {e}")
    return standings

def fetch_player_assists(league_code):
    """
    네이버 스포츠 리그별 선수 어시스트 수집
    """
    assists_map = {}
    try:
        api_url = f"https://sports.news.naver.com/wfootball/record/playerRank?category={league_code}&recordType=assist"
        res = requests.get(api_url, headers=HEADERS, timeout=10)
        data = res.json()
        
        for player in data.get('recordList', []):
            player_name = player.get('playerName')
            assist_cnt = int(player.get('assist', 0))
            assists_map[player_name] = assist_cnt
    except Exception as e:
        print(f"[{league_code}] 어시스트 수집 실패: {e}")
    return assists_map

def update_sports_data():
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M (KST)")

    # 1. 리그별 승점 & 어시스트 데이터 수집
    leagues = ["epl", "primera", "ligue1"]
    standings_data = {}
    assists_data = {}

    for lcode in leagues:
        standings_data[lcode] = fetch_league_standings(lcode)
        assists_data[lcode] = fetch_player_assists(lcode)

    # 2. 지정된 9명 선수 정보에 실제 데이터 조합
    result_players = []
    for item in PLAYERS_CONFIG:
        lcode = item["league_code"]
        
        # 네이버 데이터에서 팀 승점 찾기 (유연한 이름 매칭)
        team_pts = 0
        for t_name, pts in standings_data.get(lcode, {}).items():
            if item["team"] in t_name or t_name in item["team"]:
                team_pts = pts
                break

        # 네이버 데이터에서 어시스트 찾기
        player_assist = 0
        for p_name, ast in assists_data.get(lcode, {}).items():
            if item["name"] in p_name or p_name in item["name"]:
                player_assist = ast
                break

        result_players.append({
            "participant": item["participant"],
            "name": item["name"],
            "team": item["team"],
            "league": item["league"],
            "pts": team_pts,
            "assists": player_assist
        })

    output_data = {
        "metadata": {
            "dataDate": data_date,
            "lastUpdated": last_updated
        },
        "players": result_players
    }

    # 3. data.json 저장
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"[{last_updated}] 네이버 스포츠 실시간 데이터 수집 완료.")

if __name__ == "__main__":
    update_sports_data()
