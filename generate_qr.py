# generate_qr.py

import os
import qrcode
import socket
import sys

def get_local_ip():
    """현재 머신의 로컬 IP를 반환합니다."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 임의의 목적지로 연결 시도 → 로컬 IP 확인
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def main():
    # Render에선 RENDER_EXTERNAL_URL 환경변수에 서비스 주소가 들어있습니다.
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        # 없으면 로컬 개발용으로
        url = f"http://{get_local_ip()}:5000"
    print(f"Generating QR code for URL: {url}")

    # QR 코드 생성
    try:
        img = qrcode.make(url)
        output_path = "sample_info_qr.png"
        img.save(output_path)
        print(f"QR code saved to {output_path}")
    except Exception as e:
        print(f"Failed to generate QR code: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
