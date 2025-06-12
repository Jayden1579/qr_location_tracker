# qr_location_tracker/app.py (수정 후)

import os
import json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Render Disk는 '/var/data' 경로에 마운트됩니다.
# 해당 경로에 데이터를 저장해야 영속성이 보장됩니다.
DATA_DIR = '/var/data'
DATA_FILE = os.path.join(DATA_DIR, 'location.json')

# 디렉터리가 없으면 생성
os.makedirs(DATA_DIR, exist_ok=True)

# 카카오 API 키를 환경 변수에서 가져옵니다.
KAKAO_APP_KEY = os.getenv("KAKAO_APP_KEY")

# 초기 샘플 데이터
SAMPLE_DATA = {
    "제작일": "2025년 6월 11일",
    "제작 사양": "JG RWA 4B 모터 사양 개선용",
    "기본 성능": "문제 없음",
    "기타": "n/a"
}

def load_location_data():
    """JSON 파일에서 위치 정보를 불러옵니다."""
    if not os.path.exists(DATA_FILE):
        # 파일이 없으면 기본값으로 생성
        return {"lat": None, "lon": None, "address": "아직 위치가 기록되지 않았습니다."}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError):
        # 파일 읽기 오류 시 기본값 반환
        return {"lat": None, "lon": None, "address": "위치 정보를 읽는 데 실패했습니다."}

def save_location_data(data):
    """위치 정보를 JSON 파일에 저장합니다."""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        # ensure_ascii=False로 한글이 깨지지 않게 저장
        json.dump(data, f, ensure_ascii=False, indent=4)

# 메인 페이지 라우트 (QR 코드가 가리킬 URL)
@app.route('/')
def index():
    """메인 페이지를 렌더링하고, 현재 저장된 정보를 전달합니다."""
    current_location = load_location_data()
    return render_template(
        'index.html',
        data=SAMPLE_DATA,
        location=current_location,
        kakao_app_key=KAKAO_APP_KEY # 템플릿으로 키 전달
    )

# 위치 정보 업데이트 라우트
@app.route('/update_location', methods=['POST'])
def update_location():
    """클라이언트(스마트폰)로부터 받은 위치 정보로 업데이트합니다."""
    if not request.json or 'lat' not in request.json or 'lon' not in request.json:
        return jsonify({"status": "error", "message": "Invalid data"}), 400

    new_location_data = {
        "lat": request.json['lat'],
        "lon": request.json['lon'],
        "address": request.json.get('address', '주소 정보 없음') # 주소 정보가 없으면 기본값
    }

    save_location_data(new_location_data)
    print(f"[*] 위치 업데이트: {new_location_data['address']}")
    return jsonify({"status": "success", "message": "Location updated successfully"})

if __name__ == '__main__':
    # 외부에서 접속 가능하도록 0.0.0.0으로 호스트 설정
    # debug=True는 Render에서 환경변수로 제어하는 것이 좋습니다.
    app.run(host='0.0.0.0', port=5000)
