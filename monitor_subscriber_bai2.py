"""Bài 2: Phân tích dữ liệu JSON và cảnh báo nhiệt độ/độ ẩm."""

import threading
from datetime import datetime

from mqtt_common import Session, alerts, device_id, device_topic, parser, run, sensor_values


def on_message(client, userdata, message):
    try:
        data, temperature, humidity = sensor_values(message.payload, message.topic.split("/")[2])
    except (ValueError, UnicodeDecodeError) as exc:
        print(f"Bỏ qua dữ liệu không hợp lệ: {exc}", flush=True)
        return
    lines = [
        f"Time: {datetime.now().strftime('%H:%M:%S')}",
        f"Device: {data['device_id']}",
        f"Temperature: {temperature:.1f} C",
        f"Humidity: {humidity:.1f} %",
        *alerts(temperature, humidity),
    ]
    if userdata == "table":
        warnings = "; ".join(alerts(temperature, humidity)) or "Bình thường"
        print(f"{datetime.now():%H:%M:%S} | {data['device_id']:<12} | {temperature:>8.1f} | {humidity:>8.1f} | {warnings}", flush=True)
    else:
        print("\n".join(lines) + "\n", flush=True)


def main():
    cli = parser(__doc__)
    cli.add_argument("--device-ids", nargs="+", type=device_id,
                     help="Chỉ theo dõi các cảm biến này; mặc định theo dõi tất cả")
    cli.add_argument("--format", choices=("lines", "table"), default="lines")
    args = cli.parse_args()
    topics = tuple(device_topic(identifier, "data") for identifier in args.device_ids) if args.device_ids else ("iot/lab/+/data",)
    if args.format == "table":
        print("Time     | Device       | Temp (C) | Hum (%)  | Cảnh báo", flush=True)
    session = Session(args, "monitor-bai2", topics, on_message)
    session.client.user_data_set(args.format)
    with session:
        threading.Event().wait()


if __name__ == "__main__":
    run(main)
