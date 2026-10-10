# Thực hành Python với MQTT

Bộ mã nguồn cho ba bài thực hành: truyền thông điệp, giám sát cảm biến và điều khiển đèn thông minh. Họ tên, mã sinh viên và MQTT broker được cấu hình khi chạy; không cần sửa mã nguồn.

## 1. Cài đặt

Các chương trình MQTT dùng Python 3.9 trở lên và `paho-mqtt`. Broker Python cục bộ và kiểm thử cần Python 3.10 trở lên.

Trên macOS/Linux, mở terminal trong thư mục dự án:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-broker.txt
```

Trên Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements-broker.txt
```

Mỗi terminal mới cần kích hoạt `.venv`. Nếu đã có broker của lớp, chỉ cần cài `python -m pip install -r requirements.txt`.

## 2. MQTT broker

Mặc định tất cả chương trình kết nối `127.0.0.1:1883`, MQTT 3.1.1 qua TCP, không yêu cầu tài khoản. Chạy broker cục bộ trong một terminal riêng và giữ terminal này mở:

```bash
python broker_local.py
```

Broker này dùng aMQTT, chỉ nhận kết nối trên máy đang chạy. Đèn và cảm biến là mô phỏng phần mềm; không cần phần cứng.

Nếu port 1883 đang được sử dụng:

```bash
python broker_local.py --port 1884
```

Khi đó thêm `--port 1884` cho **mọi** chương trình bên dưới. Nếu dùng broker bên ngoài, bỏ qua `broker_local.py` và thêm cùng `--host DIA_CHI_BROKER --port PORT` cho cả hai chương trình của từng bài.

Các biến môi trường tùy chọn:

| Biến | Mặc định | Ý nghĩa |
| --- | --- | --- |
| `MQTT_HOST` | `127.0.0.1` | Địa chỉ broker |
| `MQTT_PORT` | `1883` | Cổng MQTT |
| `MQTT_USERNAME` | Không đặt | Tài khoản broker |
| `MQTT_PASSWORD` | Không đặt | Mật khẩu broker |
| `MQTT_TLS` | `0` | Đặt `1` để bật TLS |
| `MQTT_CA_CERT` | Không đặt | Đường dẫn CA riêng; mặc định dùng CA hệ thống |
| `STUDENT_NAME` | Không đặt | Họ tên sinh viên |
| `STUDENT_ID` | Không đặt | Mã sinh viên |

Ví dụ cấu hình broker của lớp trên macOS/Linux; thay địa chỉ bằng broker thực tế:

```bash
export MQTT_HOST="dia-chi-broker-cua-lop"
export MQTT_PORT="1883"
export STUDENT_NAME="Họ tên của bạn"
export STUDENT_ID="Mã sinh viên của bạn"
```

PowerShell dùng `$env:MQTT_HOST="dia-chi-broker-cua-lop"` và tương tự cho các biến khác. Các biến chỉ áp dụng trong terminal đã đặt chúng. Mọi chương trình hỗ trợ `--host`, `--port`, `--username`, `--password`, `--tls`, `--ca-cert`; dùng `--help` để xem tùy chọn. Khi broker yêu cầu TLS, bật `--tls` và đặt đúng port do broker cung cấp, thường là 8883. Cấu hình tài khoản qua biến môi trường để tránh ghi mật khẩu vào mã nguồn hoặc Git.

## 3. Bài 1 gửi và nhận thông điệp

Terminal A, chạy subscriber trước và chờ dòng `Đang lắng nghe`:

```bash
python subscriber_bai1.py
```

Terminal B:

```bash
python publisher_bai1.py --name "Họ tên của bạn" --student-id "Mã sinh viên của bạn"
```

Nếu bỏ `--name`/`--student-id` và chưa đặt biến môi trường, chương trình hỏi từ bàn phím. Để gửi nhiều lần:

```bash
python publisher_bai1.py --count 3 --interval 1
```

Gửi nhiều nội dung khác nhau liên tiếp:

```bash
python publisher_bai1.py --messages "Xin chào" "Dữ liệu mới" "Tạm biệt" --interval 0.5
```

`--messages` ưu tiên hơn `--message`. Khi kết hợp `--count 2`, toàn bộ danh sách được gửi hai lượt theo đúng thứ tự. Subscriber chạy liên tục đến khi nhấn `Ctrl+C`.

Topic: `iot/lab/message`. Subscriber hiển thị topic, lời chào kèm danh tính và thời điểm nhận theo giờ máy đang chạy:

```text
Nhan duoc message:
Topic: iot/lab/message
Payload: Xin chao tu client Python MQTT - Mã sinh viên của bạn - Họ tên của bạn
Time: 10:15:20
```

## 4. Bài 2 mô phỏng cảm biến

Terminal A:

```bash
python monitor_subscriber_bai2.py
```

Terminal B:

```bash
python sensor_publisher_bai2.py
```

Publisher gửi JSON lên `iot/lab/sensor01/data` mỗi 3 giây, nhiệt độ ngẫu nhiên 20–40 °C và độ ẩm 30–80%. Payload gồm đúng ba trường `device_id`, `temperature`, `humidity`.

Để chắc chắn xuất hiện cả hai cảnh báo, chạy:

```bash
python sensor_publisher_bai2.py --temperature 36.1 --humidity 38.7 --count 3
```

Kết quả mong đợi trên monitor:

```text
Device: sensor01
Temperature: 36.1 C
Humidity: 38.7 %
CANH BAO: Nhiet do cao
CANH BAO: Do am thap
```

Cảnh báo khi nhiệt độ **> 35** và độ ẩm **< 40**. Tại đúng 35 °C và 40% không cảnh báo. Dữ liệu JSON sai hoặc thiếu trường được thông báo và bỏ qua; monitor tiếp tục chạy. `--count 0` là chạy liên tục, `--interval` đổi chu kỳ nếu cần thử nhanh.

### Mở rộng nhiều cảm biến và bảng theo dõi

Terminal A, theo dõi tất cả cảm biến với mỗi mẫu trên một dòng:

```bash
python monitor_subscriber_bai2.py --format table
```

Terminal B, mô phỏng hai cảm biến trong cùng chương trình:

```bash
python sensor_publisher_bai2.py --device-ids sensor01 sensor02
```

Mỗi chu kỳ, mỗi cảm biến gửi một mẫu riêng lên `iot/lab/<device_id>/data`; hai cảm biến có giá trị ngẫu nhiên độc lập. `--count 3` nghĩa là ba mẫu **cho mỗi cảm biến**. Mặc định monitor subscribe `iot/lab/+/data` và kiểm tra `device_id` trong payload khớp topic. Dùng `--device-ids sensor02` để chỉ xem sensor02, hoặc giữ `--format lines` để xem từng khối dữ liệu như bài cơ bản.

```text
Time     | Device       | Temp (C) | Hum (%)  | Cảnh báo
10:15:20 | sensor01     |     28.5 |     65.2 | Bình thường
10:15:20 | sensor02     |     36.1 |     38.7 | CANH BAO: Nhiet do cao; CANH BAO: Do am thap
```

## 5. Bài 3 điều khiển đèn

Terminal A, chạy thiết bị trước và chờ dòng `Thiết bị light01 sẵn sàng`:

```bash
python device_bai3.py
```

Terminal B:

```bash
python controller_bai3.py
```

Nhập `ON`, `OFF`, sau đó `EXIT` để thoát controller. Thiết bị subscribe `iot/lab/light01/cmd` và publish JSON trên `iot/lab/light01/status` sau **mỗi** lệnh hợp lệ, kể cả lệnh lặp lại:

```json
{"device_id": "light01", "status": "ON"}
```

Thiết bị bắt đầu ở trạng thái `OFF`. Topic trạng thái có `retain=True`, nên controller mở sau thiết bị vẫn nhận trạng thái mới nhất. Lệnh điều khiển không retained. Lệnh sai không thay đổi đèn; controller và thiết bị đều báo lỗi. Controller chờ tối đa 5 giây cho phản hồi; nếu chưa có, kiểm tra thiết bị đang chạy và cả hai dùng cùng broker.

Demo không cần nhập bàn phím:

```bash
python controller_bai3.py --commands ON OFF EXIT
```

Mặc định chương trình dùng một thiết bị `light01` và một controller. Trạng thái retained chỉ là trạng thái được gửi gần nhất, không phải dấu hiệu thiết bị còn online.

### Mở rộng điều khiển đèn quạt và bơm

Terminal A, mô phỏng cả ba thiết bị với trạng thái độc lập:

```bash
python device_bai3.py --device-ids light01 fan01 pump01
```

Terminal B:

```bash
python controller_bai3.py --device-ids light01 fan01 pump01
```

Nhập `light01 ON`, `fan01 ON`, `pump01 OFF` để chọn thiết bị. Lệnh `ON`/`OFF` không có tên áp dụng cho thiết bị đầu tiên trong danh sách, hoặc thiết bị được chọn bằng `--device-id`. Dùng `EXIT` để thoát. Thiết bị chưa có trong danh sách hoặc lệnh sai sẽ báo lỗi và không gửi lên broker.

| Thiết bị | Topic lệnh | Topic trạng thái |
| --- | --- | --- |
| `light01` | `iot/lab/light01/cmd` | `iot/lab/light01/status` |
| `fan01` | `iot/lab/fan01/cmd` | `iot/lab/fan01/status` |
| `pump01` | `iot/lab/pump01/cmd` | `iot/lab/pump01/status` |

Một controller riêng cho quạt:

```bash
python controller_bai3.py --device-id fan01
```

Demo tự động cho ba thiết bị; đặt mỗi lệnh gồm hai từ trong dấu ngoặc kép:

```bash
python controller_bai3.py --device-ids light01 fan01 pump01 --commands "light01 ON" "fan01 ON" "pump01 ON" "fan01 OFF" EXIT
```

Tất cả thiết bị được chọn phải chạy trước. Có thể chạy một chương trình device cho cả ba, hoặc nhiều terminal với `--device-ids light01`, `--device-ids fan01`, `--device-ids pump01`. Mỗi ID chỉ nên có một mô phỏng đang chạy. ID có 1–64 ký tự, bắt đầu bằng chữ hoặc số, chỉ chứa chữ, số, `_` và `-`.

## 6. Kiểm tra và kết quả

Nhấn `Ctrl+C` để dừng subscriber, sensor, thiết bị và broker. Publisher hữu hạn tự thoát sau khi broker xác nhận các thông điệp QoS 1. Subscribe được đăng ký lại khi client tự kết nối lại.

Chạy kiểm thử tự động; bộ kiểm thử mở broker riêng trên cổng tạm, khởi chạy sáu chương trình thật và dọn các tiến trình khi xong:

```bash
python -m unittest discover -s tests -v
```

## 7. Các file nộp bài

- `publisher_bai1.py`, `subscriber_bai1.py`
- `sensor_publisher_bai2.py`, `monitor_subscriber_bai2.py`
- `device_bai3.py`, `controller_bai3.py`
- `mqtt_common.py` — module dùng chung, cần đi cùng sáu chương trình
- `requirements.txt`, `README.md`, `README.txt`
- `broker_local.py`, `requirements-broker.txt`, `tests/test_lab.py` — broker và kiểm thử tùy chọn
