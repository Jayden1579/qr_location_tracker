import os
from flask import Flask, render_template, request, jsonify
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- Flask 앱 초기화 ---
app = Flask(__name__)

# --- Google Sheets 설정 ---
# 스코프 정의: 스프레드시트 읽기/쓰기 권한
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
# 서비스 계정 키 JSON 파일 경로 (환경변수 또는 기본값)
CREDS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
# 스프레드시트 ID (URL 중간에 있는 키)
SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1u0mKAtOsA_ILl7vyHWysP15BAzz5chYR4N_w9RxLr6o')
# 워크시트 이름 (기본: 'Sheet1')
SHEET_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'Sheet1')

# 서비스 계정 인증
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
gc = gspread.authorize(credentials)
# 스프레드시트 열기 및 워크시트 선택
sh = gc.open_by_key(SHEET_ID)
worksheet = sh.worksheet(SHEET_NAME)

# 샘플 메타데이터 (템플릿에 표시용)
SAMPLE_DATA = {
    "제작일": "2025-06-01",
    "기본 성능": "…",
    # 필요시 추가 정보
}

@app.route("/")
def index():
    """
    메인 페이지: Google Sheets에서 마지막 위치 정보를 가져와서 렌더링
    """
    # 모든 레코드를 불러와서 마지막 행 정보 추출
    records = worksheet.get_all_records()
    if records:
        last = records[-1]
    else:
        last = {}
    return render_template("index.html", sample=SAMPLE_DATA, location=last)

@app.route("/update_location", methods=["POST"])
def update_location():
    """
    위치 업데이트: 클라이언트에서 받은 lat, lon, address를 스프레드시트에 추가
    """
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    address = data.get("address")
    # UTC 기준 ISO 형식 타임스탬프
    timestamp = datetime.utcnow().isoformat() + 'Z'

    # 시트에 새로운 행 추가 (timestamp, lat, lon, address)
    worksheet.append_row([timestamp, lat, lon, address], value_input_option='USER_ENTERED')

    new_loc = {"timestamp": timestamp, "lat": lat, "lon": lon, "address": address}
    return jsonify(status="success", location=new_loc)

if __name__ == "__main__":
    # 포트는 환경변수 PORT 또는 기본 5000
    port = int(os.getenv('PORT', 5000))
    # 0.0.0.0으로 바인딩하여 외부 접근 허용
    app.run(host='0.0.0.0', port=port)
