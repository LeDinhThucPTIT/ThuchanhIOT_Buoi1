"""Kiểm tra ba bài bằng các tiến trình thật và broker MQTT cục bộ."""

import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mqtt_common import COMMAND_TOPIC, SENSOR_TOPIC, STATUS_TOPIC, Session, alerts, parse_command, parser, sensor_values


class Process:
    def __init__(self, script, *args):
        env = {key: value for key, value in os.environ.items()
               if not key.startswith(("MQTT_", "STUDENT_"))}
        env["PYTHONUNBUFFERED"] = "1"
        self.process = subprocess.Popen(
            [sys.executable, str(ROOT / script), *map(str, args)],
            cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        self.lines = []
        self.condition = threading.Condition()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.process.stdout:
            with self.condition:
                self.lines.append((time.monotonic(), line.rstrip()))
                self.condition.notify_all()

    @property
    def output(self):
        with self.condition:
            return "\n".join(line for _, line in self.lines)

    def wait_text(self, text, count=1, timeout=10):
        deadline = time.monotonic() + timeout
        with self.condition:
            while "\n".join(line for _, line in self.lines).count(text) < count:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AssertionError(f"Không thấy {text!r}:\n{self.output}")
                self.condition.wait(min(remaining, 0.2))

    def finish(self, timeout=15):
        code = self.process.wait(timeout=timeout)
        self.reader.join(timeout=2)
        if code != 0:
            raise AssertionError(f"Exit code {code}:\n{self.output}")
        return self.output

    def stop(self):
        if self.process.poll() is None:
            self.process.send_signal(signal.SIGINT)
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.reader.join(timeout=2)
        self.process.stdout.close()


class PayloadTests(unittest.TestCase):
    def test_device_command_selection(self):
        devices = ["light01", "fan01", "pump01"]
        self.assertEqual(parse_command(" on ", "light01", devices), ("light01", "ON"))
        self.assertEqual(parse_command("fan01 off", "light01", devices), ("fan01", "OFF"))
        self.assertEqual(parse_command("exit", "light01", devices), (None, "EXIT"))
        for command in ("", "INVALID", "other01 ON", "fan01 EXIT", "fan01 ON OFF"):
            with self.subTest(command=command), self.assertRaises(ValueError):
                parse_command(command, "light01", devices)

    def test_strict_thresholds(self):
        self.assertEqual(alerts(35, 40), [])
        self.assertEqual(alerts(35.1, 40), ["CANH BAO: Nhiet do cao"])
        self.assertEqual(alerts(35, 39.9), ["CANH BAO: Do am thap"])
        self.assertEqual(len(alerts(36.1, 38.7)), 2)

    def test_invalid_sensor_payloads(self):
        for payload in [b"invalid", b"[]", b"{}", b"\xff",
                        b'{"device_id":"sensor01","temperature":true,"humidity":50}',
                        b'{"device_id":"sensor01","temperature":NaN,"humidity":50}',
                        b'{"device_id":"sensor01","temperature":28,"humidity":101}']:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    sensor_values(payload)


class MQTTIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.broker = Process("broker_local.py", "--port", cls.port)
        cls.addClassCleanup(cls.broker.stop)
        cls.broker.wait_text("Broker sẵn sàng")

    def launch(self, script, *args):
        process = Process(script, "--host", "127.0.0.1", "--port", self.port, *args)
        self.addCleanup(process.stop)
        return process

    def test_bai1_message_topic_identity_and_time(self):
        subscriber = self.launch("subscriber_bai1.py")
        subscriber.wait_text("Đang lắng nghe")
        publisher = self.launch("publisher_bai1.py", "--name", "Sinh viên thử nghiệm",
                                "--student-id", "TEST001", "--count", 2, "--interval", 0.1)
        publisher.finish()
        subscriber.wait_text("Nhan duoc message:", count=2)
        self.assertIn("Topic: iot/lab/message", subscriber.output)
        self.assertIn("TEST001 - Sinh viên thử nghiệm", subscriber.output)
        self.assertRegex(subscriber.output, r"Time: \d{2}:\d{2}:\d{2}")
        subscriber.stop()
        self.assertEqual(subscriber.process.returncode, 0)
        self.assertIn("Đã dừng chương trình", subscriber.output)

    def test_bai1_distinct_message_batch_in_order(self):
        subscriber = self.launch("subscriber_bai1.py")
        subscriber.wait_text("Đang lắng nghe")
        publisher = self.launch("publisher_bai1.py", "--name", "Sinh viên", "--student-id", "TEST002",
                                "--messages", "Xin chào", "Dữ liệu mới", "Tạm biệt", "--count", 2, "--interval", 0.05)
        publisher.finish()
        subscriber.wait_text("Nhan duoc message:", count=6)
        payloads = [line.removeprefix("Payload: ") for _, line in subscriber.lines if line.startswith("Payload:")]
        expected = [f"{message} - TEST002 - Sinh viên" for message in ("Xin chào", "Dữ liệu mới", "Tạm biệt")] * 2
        self.assertEqual(payloads, expected)

    def test_bai2_multiple_sensors_table_and_filter(self):
        monitor = self.launch("monitor_subscriber_bai2.py")
        table = self.launch("monitor_subscriber_bai2.py", "--format", "table")
        filtered = self.launch("monitor_subscriber_bai2.py", "--device-ids", "sensor02")
        for process in (monitor, table, filtered):
            process.wait_text("Đang lắng nghe")
        sensor = self.launch("sensor_publisher_bai2.py", "--device-ids", "sensor01", "sensor02",
                             "--count", 2, "--interval", 0.1, "--temperature", 36.1, "--humidity", 38.7)
        sensor.finish()
        monitor.wait_text("CANH BAO: Nhiet do cao", count=4)
        filtered.wait_text("Device: sensor02", count=2)
        table.wait_text("CANH BAO: Do am thap", count=4)
        self.assertEqual(monitor.output.count("Device: sensor01"), 2)
        self.assertEqual(monitor.output.count("Device: sensor02"), 2)
        self.assertNotIn("Device: sensor01", filtered.output)
        self.assertRegex(table.output, r"\d{2}:\d{2}:\d{2} \| sensor02\s+\|\s+36\.1\s+\|\s+38\.7")
        samples = [json.loads(line) for _, line in sensor.lines if line.startswith('{"device_id"')]
        self.assertEqual([sample["device_id"] for sample in samples], ["sensor01", "sensor02"] * 2)
        self.assertIn("iot/lab/sensor02/data", sensor.output)
        args = parser("test").parse_args(["--host", "127.0.0.1", "--port", str(self.port)])
        with Session(args, "test-mismatch") as session:
            session.publish("iot/lab/sensor02/data", json.dumps({"device_id": "sensor01", "temperature": 28, "humidity": 60}))
        monitor.wait_text("khớp với topic")

    def test_bai3_three_devices_keep_independent_states(self):
        device = self.launch("device_bai3.py", "--device-ids", "light01", "fan01", "pump01")
        device.wait_text("Thiết bị pump01 sẵn sàng")
        states = {}
        changed = threading.Condition()

        def observe(client, userdata, message):
            data = json.loads(message.payload)
            with changed:
                states[data["device_id"]] = data["status"]
                changed.notify_all()

        args = parser("test").parse_args(["--host", "127.0.0.1", "--port", str(self.port)])
        with Session(args, "test-states", ("iot/lab/+/status",), observe):
            with changed:
                self.assertTrue(changed.wait_for(lambda: all(identifier in states for identifier in ("light01", "fan01", "pump01")), timeout=5))
            controller = self.launch("controller_bai3.py", "--device-id", "fan01", "--commands", "ON", "EXIT")
            output = controller.finish()
            self.assertIn("Da gui lenh ON toi fan01", output)
            self.assertNotIn("Chưa nhận phản hồi", output)
            with changed:
                self.assertTrue(changed.wait_for(lambda: states.get("fan01") == "ON", timeout=5))
                self.assertEqual({key: states[key] for key in ("light01", "fan01", "pump01")}, {"light01": "OFF", "fan01": "ON", "pump01": "OFF"})
            controller = self.launch("controller_bai3.py", "--device-ids", "light01", "fan01", "pump01",
                                     "--commands", "other01 ON", "pump01 INVALID", "light01 ON", "pump01 ON", "fan01 OFF", "EXIT")
            output = controller.finish()
            self.assertEqual(output.count("Lệnh không hợp lệ"), 2)
            self.assertNotIn("Chưa nhận phản hồi", output)
            with changed:
                self.assertTrue(changed.wait_for(lambda: states.get("fan01") == "OFF" and states.get("pump01") == "ON", timeout=5))
                self.assertEqual({key: states[key] for key in ("light01", "fan01", "pump01")}, {"light01": "ON", "fan01": "OFF", "pump01": "ON"})

    def test_device_ids_cannot_change_topic_structure(self):
        for script in ("sensor_publisher_bai2.py", "monitor_subscriber_bai2.py", "device_bai3.py", "controller_bai3.py"):
            with self.subTest(script=script):
                process = self.launch(script, "--device-ids", "sensor/+/data")
                self.assertEqual(process.process.wait(timeout=5), 2)
                process.reader.join(timeout=2)
                self.assertIn("device_id gồm", process.output)

    def test_bai2_json_alerts_and_default_three_second_interval(self):
        monitor = self.launch("monitor_subscriber_bai2.py")
        monitor.wait_text("Đang lắng nghe")
        sensor = self.launch("sensor_publisher_bai2.py", "--count", 2,
                             "--temperature", 36.1, "--humidity", 38.7)
        sensor.finish()
        monitor.wait_text("CANH BAO: Do am thap", count=2)
        self.assertEqual(monitor.output.count("CANH BAO: Nhiet do cao"), 2)
        self.assertIn("Device: sensor01", monitor.output)
        samples = [(stamp, json.loads(line)) for stamp, line in sensor.lines
                   if line.startswith('{"device_id"')]
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0][1], {"device_id": "sensor01", "temperature": 36.1, "humidity": 38.7})
        self.assertGreaterEqual(samples[1][0] - samples[0][0], 2.9)

        args = parser("test").parse_args(["--host", "127.0.0.1", "--port", str(self.port)])
        with Session(args, "test-injector") as session:
            session.publish(SENSOR_TOPIC, "malformed JSON")
            session.publish(SENSOR_TOPIC, json.dumps({"device_id": "sensor01", "temperature": 35, "humidity": 40}))
        monitor.wait_text("Bỏ qua dữ liệu không hợp lệ")
        monitor.wait_text("Temperature: 35.0 C")
        self.assertEqual(monitor.output.count("CANH BAO: Nhiet do cao"), 2)
        self.assertEqual(monitor.output.count("CANH BAO: Do am thap"), 2)

    def test_bai3_commands_status_and_invalid_input(self):
        device = self.launch("device_bai3.py")
        device.wait_text("Thiết bị light01 sẵn sàng")
        args = parser("test").parse_args(["--host", "127.0.0.1", "--port", str(self.port)])
        with Session(args, "test-injector") as session:
            session.publish(COMMAND_TOPIC, "INVALID")
        device.wait_text("Lệnh không hợp lệ")
        controller = self.launch("controller_bai3.py", "--commands", "WRONG", "ON", "ON", "OFF", "EXIT")
        output = controller.finish()
        self.assertIn("Lệnh không hợp lệ", output)
        self.assertEqual(output.count("Da gui lenh ON"), 2)
        self.assertIn("Da gui lenh OFF", output)
        self.assertIn('"status": "ON"', output)
        self.assertIn('"status": "OFF"', output)
        self.assertNotIn("Chưa nhận phản hồi", output)
        device.wait_text("Đèn: ON", count=2)
        device.wait_text("Đèn: OFF")
        self.assertEqual(device.output.count("Phản hồi:"), 3)

    def test_connection_error_is_clear(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            unused_port = sock.getsockname()[1]
            process = Process("subscriber_bai1.py", "--host", "127.0.0.1", "--port", unused_port)
            self.addCleanup(process.stop)
            self.assertEqual(process.process.wait(timeout=10), 1)
            process.reader.join(timeout=2)
            self.assertIn("Kiểm tra broker", process.output)
            self.assertNotIn("Traceback", process.output)

    def test_controller_does_not_treat_retained_status_as_reply(self):
        args = parser("test").parse_args(["--host", "127.0.0.1", "--port", str(self.port)])
        with Session(args, "test-retained") as session:
            session.publish(STATUS_TOPIC, json.dumps({"device_id": "light01", "status": "OFF"}), retain=True)
        controller = self.launch("controller_bai3.py", "--commands", "OFF", "EXIT")
        output = controller.finish()
        self.assertIn('"status": "OFF"', output)
        self.assertIn("Chưa nhận phản hồi", output)


if __name__ == "__main__":
    unittest.main()
