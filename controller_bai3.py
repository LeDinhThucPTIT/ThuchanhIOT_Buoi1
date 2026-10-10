"""Bài 3: Nhập ON/OFF/EXIT và nhận phản hồi trạng thái từ thiết bị đèn."""

import json
import queue
import time

from mqtt_common import Session, device_id, device_topic, json_object, parse_command, parser, run


def main():
    cli = parser(__doc__)
    cli.add_argument("--commands", nargs="+", help="Danh sách lệnh cho demo tự động")
    cli.add_argument("--device-id", type=device_id, help="Thiết bị nhận lệnh ON/OFF không có tên")
    cli.add_argument("--device-ids", nargs="+", type=device_id,
                     help="Các thiết bị điều khiển, ví dụ light01 fan01 pump01")
    args = cli.parse_args()
    devices = args.device_ids or [args.device_id or "light01"]
    default_device = args.device_id or devices[0]
    if default_device not in devices:
        cli.error("--device-id phải nằm trong --device-ids")
    if len(set(devices)) != len(devices):
        cli.error("Danh sách device_id không được trùng")
    responses = queue.Queue()

    def on_message(client, userdata, message):
        try:
            data = json_object(message.payload)
            identifier = message.topic.split("/")[2]
            if data.get("device_id") != identifier or identifier not in devices or data.get("status") not in ("ON", "OFF"):
                raise ValueError("Trạng thái thiết bị không hợp lệ hoặc không khớp topic")
        except (ValueError, UnicodeDecodeError) as exc:
            print(f"Bỏ qua phản hồi không hợp lệ: {exc}", flush=True)
            return
        # Bản retained là trạng thái cũ, không phải phản hồi cho lệnh vừa gửi.
        if not message.retain:
            responses.put((identifier, data["status"]))
        print(f"Trang thai nhan duoc:\n{json.dumps(data, ensure_ascii=False)}", flush=True)

    topics = tuple(device_topic(identifier, "status") for identifier in devices)
    with Session(args, "controller-bai3", topics, on_message) as session:
        print(f"Thiết bị điều khiển: {', '.join(devices)}. Mặc định: {default_device}", flush=True)
        commands = iter(args.commands) if args.commands else None
        while True:
            text = next(commands, "EXIT") if commands is not None else input("Nhap lenh (ON/OFF, device_id ON/OFF, EXIT): ")
            try:
                identifier, command = parse_command(text, default_device, devices)
            except ValueError as exc:
                print(f"Lệnh không hợp lệ. {exc}.", flush=True)
                continue
            if command == "EXIT":
                break
            while True:
                try:
                    responses.get_nowait()  # Bỏ phản hồi cũ trước khi gửi lệnh mới.
                except queue.Empty:
                    break
            session.publish(device_topic(identifier, "cmd"), command)
            print(f"Da gui lenh {command} toi {identifier}", flush=True)
            deadline = time.monotonic() + 5
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    print("Chưa nhận phản hồi. Kiểm tra device_bai3.py đang chạy.", flush=True)
                    break
                try:
                    if responses.get(timeout=remaining) == (identifier, command):
                        break
                except queue.Empty:
                    print("Chưa nhận phản hồi. Kiểm tra device_bai3.py đang chạy.", flush=True)
                    break


if __name__ == "__main__":
    run(main)
