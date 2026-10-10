"""Bài 2: Mô phỏng cảm biến nhiệt độ/độ ẩm gửi JSON mỗi 3 giây."""

import json
import math
import random
import time

from mqtt_common import Session, device_id, device_topic, nonnegative_int, parser, positive_float, run


def main():
    cli = parser(__doc__)
    cli.add_argument("--interval", type=positive_float, default=3.0)
    cli.add_argument("--count", type=nonnegative_int, default=0,
                     help="Số chu kỳ cho mỗi thiết bị; 0 = chạy liên tục")
    cli.add_argument("--device-ids", nargs="+", type=device_id, default=["sensor01"],
                     help="Các cảm biến mô phỏng, ví dụ sensor01 sensor02")
    cli.add_argument("--temperature", type=float, help="Giá trị cố định để kiểm tra cảnh báo")
    cli.add_argument("--humidity", type=float, help="Giá trị cố định để kiểm tra cảnh báo")
    args = cli.parse_args()
    if len(set(args.device_ids)) != len(args.device_ids):
        cli.error("Danh sách device_id không được trùng")
    if args.temperature is not None and not math.isfinite(args.temperature):
        cli.error("temperature phải hữu hạn")
    if args.humidity is not None and (not math.isfinite(args.humidity) or not 0 <= args.humidity <= 100):
        cli.error("humidity phải trong khoảng 0..100")
    with Session(args, "sensor-bai2") as session:
        sent = 0
        while args.count == 0 or sent < args.count:
            for identifier in args.device_ids:
                data = {
                    "device_id": identifier,
                    "temperature": args.temperature if args.temperature is not None else round(random.uniform(20, 40), 1),
                    "humidity": args.humidity if args.humidity is not None else round(random.uniform(30, 80), 1),
                }
                topic = device_topic(identifier, "data")
                payload = json.dumps(data, ensure_ascii=False, allow_nan=False)
                session.publish(topic, payload)
                print(f"Đã gửi: {topic}\n{payload}", flush=True)
            sent += 1
            if args.count == 0 or sent < args.count:
                time.sleep(args.interval)


if __name__ == "__main__":
    run(main)
