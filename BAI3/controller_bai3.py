import json
from threading import Event

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883

CMD_TOPIC = "iot/lab/light01/cmd"
STATUS_TOPIC = "iot/lab/light01/status"

ready = Event()


def on_connect(client, userdata, flags, reason_code, properties):
    ready.clear()

    if reason_code == 0:
        print("Ket noi broker thanh cong!")
        client.subscribe(STATUS_TOPIC, qos=1)
    else:
        print(f"Ket noi that bai: {reason_code}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    if any(code.is_failure for code in reason_codes):
        print("Dang ky topic that bai.")
    else:
        print(f"Da dang ky topic: {STATUS_TOPIC}")
        ready.set()


def on_disconnect(client, userdata, disconnect_flags,
                  reason_code, properties):
    ready.clear()


def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        data = json.loads(payload)

        if not isinstance(data, dict):
            raise ValueError("Payload phai la JSON object.")

        if data.get("device_id") != "light01":
            raise ValueError("device_id khong dung.")

        status = data.get("status")

        if status not in ("ON", "OFF"):
            raise ValueError("Trang thai phai la ON hoac OFF.")

        print("\nTrang thai nhan duoc:")
        print(json.dumps(data))
        print(f"Den hien tai: {'BAT' if status == 'ON' else 'TAT'}")
        print("Nhap lenh tiep roi nhan Enter.")

    except (UnicodeDecodeError, ValueError) as error:
        print(f"\nPhan hoi khong hop le: {error}")


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_disconnect = on_disconnect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # Chờ đăng ký topic trạng thái thành công trước khi nhập lệnh.
    if not ready.wait(timeout=10):
        raise TimeoutError("Chua san sang nhan trang thai sau 10 giay.")

    print("\nNhap ON de bat, OFF de tat, EXIT de thoat.")

    while True:
        command = input("\nNhap lenh: ").strip().upper()

        if command == "EXIT":
            break

        if command not in ("ON", "OFF"):
            print("Lenh sai! Chi nhap ON, OFF hoac EXIT.")
            continue

        if not ready.is_set():
            print("Dang mat ket noi. Hay cho ket noi lai.")
            continue

        result = client.publish(CMD_TOPIC, command, qos=1)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Khong the gui lenh, ma loi: {result.rc}")
            continue

        result.wait_for_publish(timeout=10)

        if result.is_published():
            print(f"Broker da xac nhan nhan lenh {command}.")
        else:
            print("Chua nhan duoc xac nhan gui tu broker.")

except (KeyboardInterrupt, EOFError):
    print("\nDa dung controller.")

except (OSError, TimeoutError, RuntimeError) as error:
    print(f"Loi: {error}")

finally:
    client.disconnect()
    client.loop_stop()