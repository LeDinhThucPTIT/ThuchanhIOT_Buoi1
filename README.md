# Thực hành lập trình Python với giao thức MQTT

## 1. Thông tin sinh viên

- Họ tên: Lê Đình Thức - MSV: B23DCCN803

## 2. Mục tiêu

Thực hành kết nối ứng dụng Python tới MQTT broker, gửi và nhận
thông điệp qua topic, tổ chức payload JSON và mô phỏng hệ thống
giám sát, điều khiển thiết bị IoT.

Bài thực hành gồm:
- Bài 1: Gửi và nhận thông điệp MQTT.
- Bài 2: Mô phỏng cảm biến nhiệt độ, độ ẩm.
- Bài 3: Mô phỏng điều khiển đèn thông minh hai chiều.

## 3. Môi trường và cấu hình

- Ngôn ngữ: Python 3.
- Thư viện: paho-mqtt 2.x.
- Công cụ: Visual Studio Code và terminal.
- Thiết bị IoT được mô phỏng bằng Python.

Cài đặt thư viện:

```cmd
py -m pip install "paho-mqtt>=2,<3"
```

Cấu hình broker trong các file:

```python
BROKER = "test.mosquitto.org"
PORT = 1883
```

Broker được sử dụng qua MQTT TCP, không dùng TLS và không yêu cầu
username/password. Các chương trình giao tiếp với nhau phải cấu hình
cùng broker, cổng và topic tương ứng.

## 4. Cấu trúc chương trình

```text
BUOI1/
├── BAI1/
│   ├── publisher_bai1.py
│   └── subscriber_bai1.py
├── BAI2/
│   ├── sensor_publisher_bai2.py
│   └── monitor_subscriber_bai2.py
├── BAI3/
│   ├── device_bai3.py
│   └── controller_bai3.py
└── README.md
```

Các lệnh dưới đây được chạy từ thư mục gốc BUOI1.
Mỗi bài sử dụng hai terminal.

## 5. Bài 1 — Gửi và nhận thông điệp

### Quy trình thực hiện

1. Xây dựng subscriber kết nối tới broker.
2. Subscriber đăng ký topic `iot/lab/message` và chờ thông điệp.
3. Xây dựng publisher gửi lời chào kèm họ tên và mã sinh viên
   lên cùng topic.
4. Broker chuyển thông điệp tới subscriber.
5. Subscriber giải mã payload và hiển thị topic, nội dung,
   thời điểm nhận.

### Cách chạy

Terminal 1 — chạy subscriber trước:

```cmd
py BAI1/subscriber_bai1.py
```

Chờ thông báo đăng ký topic thành công.

Terminal 2 — chạy publisher:

```cmd
py BAI1/publisher_bai1.py
```

### Kết quả đạt được

Hai chương trình kết nối thành công và trao đổi thông điệp
qua đúng topic.

Kết quả thực tế tại subscriber:

```text
Nhan duoc message:
Topic: iot/lab/message
Payload: Xin chao tu client Python MQTT - B23DCCN803 - Le Dinh Thuc
Time: 15:35:05
```

Subscriber hiển thị đầy đủ thông tin theo yêu cầu và tiếp tục
lắng nghe đến khi người dùng nhấn Ctrl+C.

## 6. Bài 2 — Mô phỏng cảm biến nhiệt độ và độ ẩm

### Quy trình thực hiện

1. Xây dựng chương trình mô phỏng cảm biến `sensor01`.
2. Sinh nhiệt độ ngẫu nhiên trong khoảng 25–40°C và độ ẩm
   trong khoảng 30–80%, làm tròn một chữ số thập phân.
3. Tạo payload gồm `device_id`, `temperature`, `humidity`
   và chuyển sang JSON bằng `json.dumps()`.
4. Publish dữ liệu lên topic `iot/lab/sensor01/data`.
5. Sau mỗi lần gửi thành công, nghỉ 3 giây rồi tiếp tục.
6. Chương trình giám sát subscribe cùng topic, đọc JSON
   bằng `json.loads()` và hiển thị dữ liệu.
7. Kiểm tra hai điều kiện độc lập:
   - Nhiệt độ > 35°C: cảnh báo nhiệt độ cao.
   - Độ ẩm < 40%: cảnh báo độ ẩm thấp.

### Cách chạy

Terminal 1 — chạy giám sát trước:

```cmd
py BAI2/monitor_subscriber_bai2.py
```

Terminal 2 — chạy cảm biến:

```cmd
py BAI2/sensor_publisher_bai2.py
```

### Kết quả đạt được

Cảm biến gửi liên tục các payload JSON. Chương trình giám sát
nhận được dữ liệu, hiển thị tên thiết bị, nhiệt độ, độ ẩm
và thời gian nhận.

Một số kết quả quan sát được:

| Nhiệt độ | Độ ẩm | Kết quả |
|---|---|---|
| 26.6°C | 35.4% | Cảnh báo độ ẩm thấp |
| 28.8°C | 69.7% | Không cảnh báo |
| 33.1°C | 40.5% | Không cảnh báo |
| 36.5°C | 43.7% | Cảnh báo nhiệt độ cao |

Ví dụ tại thời điểm 15:39:22:

```text
Time: 15:39:22
Device: sensor01
Temperature: 36.5 C
Humidity: 43.7 %
CANH BAO: Nhiet do cao
```

Kết quả cho thấy chương trình phân tích được JSON và cảnh báo
đúng ngưỡng đối với các mẫu đã quan sát. Khoảng cách nhận dữ liệu
xấp xỉ 3 giây, có thể tăng do thời gian truyền và xác nhận MQTT.

## 7. Bài 3 — Điều khiển đèn thông minh

### Quy trình thực hiện

1. Xây dựng thiết bị mô phỏng `light01`, trạng thái ban đầu là OFF.
2. Thiết bị subscribe topic `iot/lab/light01/cmd`.
3. Controller subscribe topic `iot/lab/light01/status`.
4. Người dùng nhập ON hoặc OFF tại controller.
5. Controller publish lệnh lên topic điều khiển.
6. Thiết bị nhận lệnh hợp lệ và cập nhật biến trạng thái đèn.
7. Thiết bị publish trạng thái dạng JSON lên topic phản hồi.
8. Controller nhận phản hồi và hiển thị trạng thái hiện tại.

Controller sử dụng xử lý mạng nền để vẫn nhận phản hồi MQTT
trong khi chờ nhập lệnh từ bàn phím.

### Cách chạy

Terminal 1 — chạy thiết bị trước:

```cmd
py BAI3/device_bai3.py
```

Chờ thiết bị đăng ký topic thành công.

Terminal 2 — chạy controller:

```cmd
py BAI3/controller_bai3.py
```

Các lệnh hỗ trợ:

| Lệnh | Chức năng |
|---|---|
| ON | Bật đèn |
| OFF | Tắt đèn |
| EXIT | Kết thúc controller |

### Kết quả đạt được

Thiết bị nhận được cả lệnh ON và OFF, cập nhật trạng thái
tương ứng và tạo phản hồi JSON.

Khi nhận ON, terminal thiết bị hiển thị:

```text
Nhan lenh: ON
Den: BAT
Da dua phan hoi vao hang doi gui: {"device_id": "light01", "status": "ON"}
```

Khi nhận OFF, terminal thiết bị hiển thị:

```text
Nhan lenh: OFF
Den: TAT
Da dua phan hoi vao hang doi gui: {"device_id": "light01", "status": "OFF"}
```

Controller nhận được phản hồi OFF:

```text
Trang thai nhan duoc:
{"device_id": "light01", "status": "OFF"}
Den hien tai: TAT
```

Kết quả xác nhận hệ thống giao tiếp hai chiều: controller gửi
lệnh tới thiết bị và thiết bị phản hồi trạng thái về controller.

## 8. Vấn đề gặp phải và cách khắc phục

### Thiếu thư viện

Ban đầu chương trình báo:

```text
ModuleNotFoundError: No module named 'paho'
```

Khắc phục bằng cách cài paho-mqtt với cùng Python Launcher
được sử dụng để chạy chương trình:

```cmd
py -m pip install "paho-mqtt>=2,<3"
```

### Timeout khi kết nối broker

Kết nối tới `mqtt.eclipseprojects.io:1883` bị timeout.
Kiểm tra bằng Test-NetConnection cho kết quả
`TcpTestSucceeded: False`.

Sau khi chuyển cấu hình các chương trình sang
`test.mosquitto.org:1883`, chương trình kết nối và trao đổi
dữ liệu thành công.

### NameError khi tạo lời chào

Publisher từng báo NameError do đưa mã sinh viên trực tiếp
vào dấu ngoặc nhọn của f-string khiến Python hiểu đó là tên biến.

Khắc phục bằng cách lưu thông tin trong các biến chuỗi
`MA_SINH_VIEN`, `HO_TEN`, rồi sử dụng các biến này để tạo payload.

## 9. Tổng kết

Ba bài thực hành đã triển khai được các chức năng:
- Gửi và nhận thông điệp theo mô hình publish/subscribe.
- Truyền dữ liệu cảm biến dạng JSON và cảnh báo theo ngưỡng.
- Điều khiển thiết bị và nhận phản hồi trạng thái qua hai topic.

Nhấn Ctrl+C để dừng các chương trình chạy liên tục.
Nhập EXIT để kết thúc controller của bài 3.
