THUC HANH PYTHON MQTT

Broker mac dinh: 127.0.0.1:1883, MQTT 3.1.1, TCP, khong tai khoan.
Co the doi bang --host/--port hoac bien MQTT_HOST/MQTT_PORT.
Ho ten va ma sinh vien: --name/--student-id hoac STUDENT_NAME/STUDENT_ID.

Cai dat (Python 3.10+ neu dung broker cuc bo):
  python3 -m venv .venv
  macOS/Linux: source .venv/bin/activate
  Windows PowerShell: .venv\Scripts\Activate.ps1
  python -m pip install -r requirements-broker.txt

Mo terminal rieng, kich hoat .venv va chay:
  python broker_local.py

Moi bai can hai terminal da kich hoat .venv. Chay subscriber/device truoc.

Bai 1:
  python subscriber_bai1.py
  python publisher_bai1.py --name "Ho ten cua ban" --student-id "Ma sinh vien cua ban"
  Ket qua: nhan topic iot/lab/message, loi chao, danh tinh va thoi diem nhan.

Bai 2:
  python monitor_subscriber_bai2.py
  python sensor_publisher_bai2.py
  Ket qua: JSON sensor01 moi 3 giay; canh bao khi nhiet do >35 va do am <40.
  Thu ca hai canh bao:
  python sensor_publisher_bai2.py --temperature 36.1 --humidity 38.7 --count 3

Bai 3:
  python device_bai3.py
  python controller_bai3.py
  Nhap ON/OFF de dieu khien, EXIT de thoat.
  Ket qua: lenh tren iot/lab/light01/cmd, JSON trang thai tren iot/lab/light01/status.

Nhan Ctrl+C de dung cac chuong trinh chay lien tuc.
Kiem thu: python -m unittest discover -s tests -v
GOI Y MO RONG DA TRIEN KHAI
  Bai 1: gui danh sach thong diep theo thu tu; subscriber chay den Ctrl+C.
  python publisher_bai1.py --messages "Xin chao" "Du lieu moi" "Tam biet" --count 2
  Bai 2: nhieu cam bien, bang hien thi theo dong, loc cam bien.
  python monitor_subscriber_bai2.py --format table
  python sensor_publisher_bai2.py --device-ids sensor01 sensor02
  Chi theo doi sensor02: python monitor_subscriber_bai2.py --device-ids sensor02
  Bai 3: ON/OFF, lenh sai, EXIT, den/quat/bom co trang thai doc lap.
  python device_bai3.py --device-ids light01 fan01 pump01
  python controller_bai3.py --device-ids light01 fan01 pump01
  Nhap "light01 ON", "fan01 ON", "pump01 OFF", hoac EXIT.
Ket qua ngay 10/10/2026: 12/12 kiem thu dat tren macOS, Python 3.14.7.
Phai nop kem mqtt_common.py vi ca sau chuong trinh deu import module nay.
Xem README.md de biet cau hinh TLS, tai khoan, bien moi truong va cach xu ly loi.
