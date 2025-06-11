# qr_location_tracker/generate_qr.py

import qrcode
import socket

def get_local_ip():
    """ 현재 컴퓨터의 로컬 IP 주소를 반환합니다. """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # 이 IP 주소는 실제로 연결되지 않아도 됩니다.
        # 소켓을 이용해 라우팅 테이블에서 외부로 나가는 인터페이스의 IP를 알아냅니다.
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1' # 실패 시 로컬호스트 반환
    finally:
        s.close()
    return IP

def generate_qr_code(port=5000):
    """ 서버 주소로 QR 코드를 생성하고 파일로 저장합니다. """
    ip_address = get_local_ip()
    if ip_address == '127.0.0.1':
        print("경고: 로컬 IP 주소를 찾을 수 없습니다. QR 코드가 외부에서 작동하지 않을 수 있습니다.")
        print("컴퓨터가 네트워크에 연결되어 있는지 확인하세요.")
    
    # QR 코드가 가리킬 전체 URL
    url = f"http://{ip_address}:{port}"
    
    # QR 코드 생성
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    
    # 파일로 저장
    filename = 'sample_info_qr.png'
    img.save(filename)
    
    print(f"QR 코드가 생성되었습니다: {filename}")
    print(f"이 QR 코드는 다음 주소를 가리킵니다: {url}")
    print("스마트폰과 컴퓨터가 동일한 Wi-Fi 네트워크에 연결되어 있어야 합니다.")

if __name__ == '__main__':
    generate_qr_code()