"""Bài 1: Gửi lời chào kèm họ tên và mã sinh viên."""

import os
import time

from mqtt_common import MESSAGE_TOPIC, Session, parser, positive_float, positive_int, run


def main():
    cli = parser(__doc__)
    cli.add_argument("--name", default=os.getenv("STUDENT_NAME", ""))
    cli.add_argument("--student-id", default=os.getenv("STUDENT_ID", ""))
    cli.add_argument("--message", default="Xin chao tu client Python MQTT")
    cli.add_argument("--messages", nargs="+", help="Các nội dung gửi lần lượt; ưu tiên hơn --message")
    cli.add_argument("--count", type=positive_int, default=1,
                     help="Số lần gửi mỗi nội dung; mặc định 1")
    cli.add_argument("--interval", type=positive_float, default=1.0)
    args = cli.parse_args()
    name = (args.name or input("Họ tên sinh viên: ")).strip()
    student_id = (args.student_id or input("Mã sinh viên: ")).strip()
    if not name or not student_id:
        cli.error("Họ tên và mã sinh viên không được để trống")
    messages = args.messages or [args.message]
    if any(not message.strip() for message in messages):
        cli.error("Nội dung thông điệp không được để trống")
    with Session(args, "publisher-bai1") as session:
        sent = 0
        for _ in range(args.count):
            for message in messages:
                payload = f"{message} - {student_id} - {name}"
                session.publish(MESSAGE_TOPIC, payload)
                sent += 1
                print(f"Đã gửi [{sent}]: {MESSAGE_TOPIC}\nPayload: {payload}", flush=True)
                if sent < args.count * len(messages):
                    time.sleep(args.interval)


if __name__ == "__main__":
    run(main)
