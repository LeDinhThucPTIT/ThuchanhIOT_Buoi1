from datetime import datetime
import paho.mqtt.client as mqtt

BROKER =  "test.mosquitto.org"
PORT = 1883
TOPIC = "iot/lab/message"


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
        print("Dang cho thong diep... Nhan Ctrl+C de thoat.\n")


def on_message(client, userdata, message):
    payload = message.payload.decode("utf-8", errors="replace")
    received_time = datetime.now().strftime("%H:%M:%S")

    print("Nhan duoc message:")
    print(f"Topic: {message.topic}")
    print(f"Payload: {payload}")
    print(f"Time: {received_time}")
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
    print("\nDa dung subscriber.")

except OSError as error:
    print(f"Loi ket noi: {error}")

finally:
    client.disconnect()