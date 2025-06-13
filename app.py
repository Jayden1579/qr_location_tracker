import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timezone, timedelta

# --- Flask 앱 초기화 ---
app = Flask(__name__)

# --- 환경 변수 로드 ---
# Render.com의 Environment Variables에서 설정해야 합니다.
SHEET_ID = os.getenv('GOOGLE_SHEETS_ID')
SHEET_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'Sheet1')
KAKAO_APP_KEY = os.getenv('KAKAO_APP_KEY') # 카카오 앱 키 추가
CREDS_FILE = 'credentials.json' # Render.com Secret File의 경로

# --- Google Sheets 설정 ---
worksheet = None
HEADER = []
try:
    if not SHEET_ID or not KAKAO_APP_KEY:
        raise ValueError("필수 환경 변수(GOOGLE_SHEETS_ID, KAKAO_APP_KEY)가 설정되지 않았습니다.")

    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    HEADER = worksheet.row_values(1)
    if not HEADER: # 시트가 비어있으면 기본 헤더 설정
        HEADER = ['timestamp', 'lat', 'lon', 'address']

except FileNotFoundError:
    print(f"오류: '{CREDS_FILE}' 파일을 찾을 수 없습니다. Render.com Secret File로 등록했는지 확인하세요.")
except Exception as e:
    print(f"Google Sheets 초기화 중 오류 발생: {e}")

# 샘플 메타데이터 (HTML 템플릿이 요구하는 모든 키 포함)
SAMPLE_DATA = {
    "제작일": "2025-06-01",
    "제작 사양": "Standard Spec. V2", # 키 추가
    "기본 성능": "High-performance tracking enabled", # 내용 수정
    "기타": "N/A" # 키 추가
}

@app.route("/")
def index():
    last_location = {}
    if worksheet:
        try:
            all_values = worksheet.get_all_values()
            if len(all_values) > 1:
                last_row_values = all_values[-1]
                last_location = dict(zip(HEADER, last_row_values))
        except Exception as e:
            print(f"데이터 로딩 오류: {e}")
            last_location = {"error": "최신 위치를 불러오는 데 실패했습니다."}
            
    # [수정됨] 1. 변수명을 'data'로 변경, 2. 'kakao_app_key' 추가
    return render_template(
        "index.html", 
        data=SAMPLE_DATA, 
        location=last_location,
        kakao_app_key=KAKAO_APP_KEY 
    )

@app.route("/update_location", methods=["POST"])
def update_location():
    if not worksheet:
        return jsonify(status="error", message="서버의 Google Sheets 연결이 설정되지 않았습니다."), 500

    try:
        data = request.get_json()
        if not all(k in data for k in ["lat", "lon", "address"]):
            return jsonify(status="error", message="필수 데이터가 누락되었습니다."), 400

        lat, lon, address = data["lat"], data["lon"], data["address"]
        
        kst = timezone(timedelta(hours=9))
        timestamp = datetime.now(kst).isoformat()

        new_row = [timestamp, str(lat), str(lon), address]
        worksheet.append_row(new_row, value_input_option='USER_ENTERED')

        new_loc = dict(zip(HEADER, new_row))
        return jsonify(status="success", location=new_loc)
    except Exception as e:
        print(f"위치 업데이트 오류: {e}")
        return jsonify(status="error", message=f"서버 내부 오류 발생"), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
