import json
import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883

CMD_TOPIC = "iot/lab/light01/cmd"
STATUS_TOPIC = "iot/lab/light01/status"

light_status = "OFF"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Ket noi broker thanh cong!")
        client.subscribe(CMD_TOPIC, qos=1)
    else:
        print(f"Ket noi that bai: {reason_code}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    if any(code.is_failure for code in reason_codes):
        print("Dang ky topic that bai.")
    else:
        print(f"Da dang ky topic: {CMD_TOPIC}")
        print(f"Trang thai ban dau: {light_status}")
        print("Dang cho lenh... Nhan Ctrl+C de thoat.\n")


def on_message(client, userdata, message):
    global light_status

    try:
        command = message.payload.decode("utf-8").strip().upper()
    except UnicodeDecodeError:
        print("Lenh khong hop le: payload khong phai UTF-8.")
        return

    if command not in ("ON", "OFF"):
        print(f"Lenh khong hop le: {command}")
        return

    light_status = command

    data = {
        "device_id": "light01",
        "status": light_status
    }

    payload = json.dumps(data)
    result = client.publish(STATUS_TOPIC, payload, qos=1)

    print(f"Nhan lenh: {command}")
    print(f"Den: {'BAT' if light_status == 'ON' else 'TAT'}")

    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        print(f"Da dua phan hoi vao hang doi gui: {payload}")
    else:
        print(f"Loi gui phan hoi: {result.rc}")

    print("-" * 40)


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)

client.on_connect = on_connect
client.on_subscribe = on_subscribe
client.on_message = on_message

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()

except KeyboardInterrupt:
    print("\nDa dung thiet bi.")

except OSError as error:
    print(f"Loi ket noi: {error}")

finally:
    client.disconnect()