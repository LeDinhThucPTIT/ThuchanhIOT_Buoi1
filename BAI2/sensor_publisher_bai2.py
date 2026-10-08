import json
import random
import time
from threading import Event

import paho.mqtt.client as mqtt

BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC = "iot/lab/sensor01/data"

connection_finished = Event()
connected = False


def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    connected = reason_code == 0

    if connected:
        print("Ket noi broker thanh cong!")
    else:
        print(f"Ket noi that bai: {reason_code}")

    connection_finished.set()


client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2
)
client.on_connect = on_connect

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    if not connection_finished.wait(timeout=10):
        raise TimeoutError("Broker khong phan hoi trong 10 giay.")

    if not connected:
        raise ConnectionError("Broker tu choi ket noi.")

    print("Gui du lieu moi 3 giay. Nhan Ctrl+C de thoat.\n")

    while True:
        data = {
            "device_id": "sensor01",
            "temperature": round(random.uniform(25, 40), 1),
            "humidity": round(random.uniform(30, 80), 1)
        }

        payload = json.dumps(data)

        result = client.publish(TOPIC, payload, qos=1)

        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Khong the gui, ma loi: {result.rc}")

        result.wait_for_publish(timeout=10)

        if not result.is_published():
            raise TimeoutError("Chua nhan duoc xac nhan gui tu broker.")

        print(f"Da gui: {payload}")
        time.sleep(3)

except KeyboardInterrupt:
    print("\nDa dung cam bien.")

except (OSError, TimeoutError, RuntimeError) as error:
    print(f"Loi: {error}")

finally:
    client.disconnect()
    client.loop_stop()