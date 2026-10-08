import json
from datetime import datetime

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "iot/lab/sensor01/data"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Ket noi broker thanh cong!")
        client.subscribe(TOPIC, qos=1)
    else:
        print(f"Ket noi that bai: {reason_code}")


def on_subscribe(client, userdata, mid, reason_codes, properties):
    if any(code.is_failure for code in reason_codes):
        print("Dang ky topic that bai.")
    else:
        print(f"Da dang ky topic: {TOPIC}")
        print("Dang giam sat... Nhan Ctrl+C de thoat.\n")


def on_message(client, userdata, message):
    try:
        payload = message.payload.decode("utf-8")
        data = json.loads(payload)

        if not isinstance(data, dict):
            raise ValueError("Payload phai la mot JSON object.")

        device_id = data["device_id"]
        temperature = data["temperature"]
        humidity = data["humidity"]

        if not isinstance(device_id, str):
            raise ValueError("device_id phai la chuoi.")

        # Không nhận boolean hoặc chuỗi thay cho số.
        if type(temperature) not in (int, float):
            raise ValueError("temperature phai la so.")

        if type(humidity) not in (int, float):
            raise ValueError("humidity phai la so.")

        print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Device: {device_id}")
        print(f"Temperature: {temperature:.1f} C")
        print(f"Humidity: {humidity:.1f} %")

        if temperature > 35:
            print("CANH BAO: Nhiet do cao")

        if humidity < 40:
            print("CANH BAO: Do am thap")

        print("-" * 40)

    except (UnicodeDecodeError, ValueError, KeyError) as error:
        print(f"Du lieu khong hop le: {error}")


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
    print("\nDa dung giam sat.")

except OSError as error:
    print(f"Loi ket noi: {error}")

finally:
    client.disconnect()