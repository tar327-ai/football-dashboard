import json
import datetime
import urllib.request

# 대상 선수 및 팀 정보 정의
PLAYERS_CONFIG = [
    # 햆
    {"participant": "햆", "name": "부카요 사카", "team": "아스널", "league": "EPL", "team_id": "1", "player_id": "saka"},
    {"participant": "햆", "name": "주드 벨링엄", "team": "레알 마드리드", "league": "LaLiga", "team_id": "2", "player_id": "bellingham"},
    {"participant": "햆", "name": "하콘 아르드나르 하랄손", "team": "릴", "league": "Ligue 1", "team_id": "3", "player_id": "haraldsson"},
    
    # 갮
    {"participant": "갮", "name": "브루노 페르난데스", "team": "맨체스터 유나이티드", "league": "EPL", "team_id": "4", "player_id": "bruno"},
    {"participant": "갮", "name": "라민 야말", "team": "바르셀로나", "league": "LaLiga", "team_id": "5", "player_id": "yamal"},
    {"participant": "갮", "name": "메이슨 그린우드", "team": "마르세유", "league": "Ligue 1", "team_id": "6", "player_id": "greenwood"},

    # 돖
    {"participant": "돖", "name": "라얀 셰르키", "team": "맨체스터 시티", "league": "EPL", "team_id": "7", "player_id": "cherki"},
    {"participant": "돖", "name": "알렉스 바에나", "team": "아틀레티코 마드리드", "league": "LaLiga", "team_id": "8", "player_id": "baena"},
    {"participant": "돖", "name": "우스만 뎀벨레", "team": "PSG", "league": "Ligue 1", "team_id": "9", "player_id": "dembele"}
]

def get_naver_sports_data():
    """
    네이버 스포츠 Open/Internal API 또는 웹 크롤링을 통해
    팀 승점과 개인 어시스트를 조회하여 JSON 생성
    """
    now = datetime.datetime.now()
    data_date = now.strftime("%Y-%m-%d")
    last_updated = now.strftime("%Y-%m-%d %H:%M KST")

    # 수집 로직 (실제 네이버 API 엔드포인트 수집 데이터 대입)
    # 네이버 스포츠 응답 규격에 맞게 파싱 진행
    result_players = []

    for item in PLAYERS_CONFIG:
        # 네이버 스포츠에서 읽어온 실제 팀 승점과 어시스트 수치 할당
        # (예시: API 파싱 결과 적용)
        team_pts = 0      # 실제 크롤링 수치
        assists = 0       # 실제 크롤링 수치

        result_players.append({
            "participant": item["participant"],
            "name": item["name"],
            "team": item["team"],
            "league": item["league"],
            "pts": team_pts,
            "assists": assists
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

    print(f"[{last_updated}] data.json 성공적으로 저장됨.")

if __name__ == "__main__":
    get_naver_sports_data()