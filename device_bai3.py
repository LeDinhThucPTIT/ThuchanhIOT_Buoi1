"""Bài 3: Mô phỏng đèn, quạt, bơm nhận ON/OFF và phản hồi trạng thái."""

import json
import threading

import paho.mqtt.client as mqtt

from mqtt_common import Session, device_id, device_topic, parser, run


def main():
    cli = parser(__doc__)
    cli.add_argument("--device-ids", nargs="+", type=device_id, default=["light01"],
                     help="Ví dụ light01 fan01 pump01")
    args = cli.parse_args()
    if len(set(args.device_ids)) != len(args.device_ids):
        cli.error("Danh sách device_id không được trùng")
    states = {identifier: {"device_id": identifier, "status": "OFF"}
              for identifier in args.device_ids}

    def on_message(client, userdata, message):
        try:
            command = message.payload.decode("utf-8").strip().upper()
        except UnicodeDecodeError:
            print("Bỏ qua lệnh không phải UTF-8", flush=True)
            return
        if command not in ("ON", "OFF"):
            print(f"Lệnh không hợp lệ: {command!r}. Chỉ chấp nhận ON/OFF.", flush=True)
            return
        identifier = message.topic.split("/")[2]
        state = states[identifier]
        state["status"] = command
        payload = json.dumps(state)
        # Callback chạy trên luồng mạng: không wait_for_publish ở đây để tránh deadlock.
        info = client.publish(device_topic(identifier, "status"), payload, qos=1, retain=True)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Lỗi gửi trạng thái: {mqtt.error_string(info.rc)}", flush=True)
        else:
            label = "Đèn" if identifier.startswith("light") else "Quạt" if identifier.startswith("fan") else "Bơm" if identifier.startswith("pump") else "Thiết bị"
            print(f"{label}: {command} ({identifier})\nPhản hồi: {payload}", flush=True)

    topics = tuple(device_topic(identifier, "cmd") for identifier in args.device_ids)
    with Session(args, "device-bai3", topics, on_message) as session:
        # Trạng thái retained giúp controller nhận trạng thái khi mở sau thiết bị.
        for identifier, state in states.items():
            session.publish(device_topic(identifier, "status"), json.dumps(state), retain=True)
            print(f"Thiết bị {identifier} sẵn sàng. Trạng thái ban đầu: OFF", flush=True)
        threading.Event().wait()


if __name__ == "__main__":
    run(main)
