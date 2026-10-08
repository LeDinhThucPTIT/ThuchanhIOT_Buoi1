from threading import Event
import paho.mqtt.client as mqtt

BROKER =  "test.mosquitto.org"
PORT = 1883
TOPIC = "iot/lab/message"

HO_TEN = "Le Dinh Thuc"
MA_SINH_VIEN = "B23DCCN803"

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

    payload = (
        f"Xin chao tu client Python MQTT"
        f" - {MA_SINH_VIEN} - {HO_TEN}"
    )

    result = client.publish(TOPIC, payload, qos=1)

    if result.rc != mqtt.MQTT_ERR_SUCCESS:
        raise RuntimeError(f"Khong the gui, ma loi: {result.rc}")

  
    result.wait_for_publish(timeout=10)

    if not result.is_published():
        raise TimeoutError("Chua nhan duoc xac nhan gui tu broker.")

    print(f"Da gui len topic: {TOPIC}")
    print(f"Payload: {payload}")

except (OSError, TimeoutError, RuntimeError) as error:
    print(f"Loi: {error}")

except KeyboardInterrupt:
    print("\nDa dung publisher.")

finally:
    client.disconnect()
    client.loop_stop()