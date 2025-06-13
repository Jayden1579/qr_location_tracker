import os
from flask import Flask, render_template, request, jsonify
import gspread
from google.oauth2.service_account import Credentials # oauth2client 대신 google-auth 사용
from datetime import datetime, timezone, timedelta

# --- Flask 앱 초기화 ---
app = Flask(__name__)

# --- Google Sheets 설정 ---
try:
    # 스코프 정의: 스프레드시트 및 드라이브 읽기/쓰기 권한
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]
    CREDS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1u0mKAtOsA_ILl7vyHWysP15BAzz5chYR4N_w9RxLr6o')
    SHEET_NAME = os.getenv('GOOGLE_SHEETS_NAME', 'Sheet1')

    # 서비스 계정 인증 (새로운 방식)
    creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)

    # 스프레드시트 열기 및 워크시트 선택
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    
    # 시트 헤더 가져오기 (첫 번째 행)
    HEADER = worksheet.row_values(1)

except FileNotFoundError:
    print(f"오류: '{CREDS_FILE}' 파일을 찾을 수 없습니다. 서비스 계정 키 파일이 올바른 위치에 있는지 확인하세요.")
    worksheet = None # 앱이 비정상 종료되지 않도록 None으로 설정
except gspread.exceptions.SpreadsheetNotFound:
    print(f"오류: 스프레드시트 ID '{SHEET_ID}'를 찾을 수 없습니다. ID가 정확한지, 서비스 계정에 공유되었는지 확인하세요.")
    worksheet = None
except Exception as e:
    print(f"Google Sheets 초기화 중 예상치 못한 오류 발생: {e}")
    worksheet = None

# 샘플 메타데이터
SAMPLE_DATA = {
    "제작일": "2025-06-01",
    "기본 성능": "…",
}

@app.route("/")
def index():
    """
    메인 페이지: Google Sheets에서 마지막 위치 정보를 가져와서 렌더링
    """
    last_location = {}
    if worksheet:
        try:
            # get_all_records() 대신 모든 값을 가져와 마지막 행만 처리 (더 효율적)
            all_values = worksheet.get_all_values()
            if len(all_values) > 1: # 헤더 외에 데이터가 있을 경우
                last_row_values = all_values[-1]
                # 헤더와 값을 짝지어 딕셔너리 생성
                last_location = dict(zip(HEADER, last_row_values))
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API 오류: {e}")
            # 오류 발생 시 빈 객체를 전달하여 페이지가 깨지지 않도록 함
            last_location = {"error": "데이터를 불러오는 데 실패했습니다."}
            
    return render_template("index.html", sample=SAMPLE_DATA, location=last_location)

@app.route("/update_location", methods=["POST"])
def update_location():
    """
    위치 업데이트: 클라이언트에서 받은 lat, lon, address를 스프레드시트에 추가
    """
    if not worksheet:
        return jsonify(status="error", message="서버의 Google Sheets 연결이 설정되지 않았습니다."), 500

    try:
        data = request.get_json()
        if not all(k in data for k in ["lat", "lon", "address"]):
            return jsonify(status="error", message="lat, lon, address 데이터가 필요합니다."), 400

        lat = data["lat"]
        lon = data["lon"]
        address = data["address"]
        
        # 한국 시간(KST, UTC+9)으로 타임스탬프 생성
        kst = timezone(timedelta(hours=9))
        timestamp = datetime.now(kst).isoformat()

        new_row = [timestamp, lat, lon, address]
        worksheet.append_row(new_row, value_input_option='USER_ENTERED')

        new_loc = dict(zip(HEADER, new_row))
        return jsonify(status="success", location=new_loc)

    except gspread.exceptions.APIError as e:
        return jsonify(status="error", message=f"Google Sheets API 오류: {e}"), 500
    except Exception as e:
        return jsonify(status="error", message=f"서버 내부 오류: {e}"), 500

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) # 개발 중에는 debug=True 옵션이 유용
