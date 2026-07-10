import paho.mqtt.client as mqtt
import time
import random
import json
import logging
from config import (
    MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASS,
    TOPIC_ENV, TOPIC_LIGHT_CONTROL, TOPIC_LIGHT_STATE,
    TOPIC_AC_CONTROL, TOPIC_AC_STATE, ENV_REPORT_INTERVAL,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("device_simulator")

# 设备初始状态
light_state = {"status": "off", "brightness": 0}
ac_state = {"status": "off", "temperature": 25}


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.info("✅ 设备模拟器连接MQTT成功")
        client.subscribe(TOPIC_LIGHT_CONTROL)
        client.subscribe(TOPIC_AC_CONTROL)
    else:
        logger.error(f"❌ MQTT连接失败，错误码: {rc}")


def on_message(client, userdata, msg):
    global light_state, ac_state
    payload = msg.payload.decode("utf-8")
    logger.info(f"📥 收到指令 [{msg.topic}]: {payload}")

    if TOPIC_LIGHT_CONTROL in msg.topic:
        if "on" in payload:
            light_state["status"] = "on"
            light_state["brightness"] = 80
        elif "off" in payload:
            light_state["status"] = "off"
            light_state["brightness"] = 0
        client.publish(TOPIC_LIGHT_STATE, json.dumps(light_state, ensure_ascii=False))

    if TOPIC_AC_CONTROL in msg.topic:
        if "on" in payload:
            ac_state["status"] = "on"
            ac_state["temperature"] = 24
        elif "off" in payload:
            ac_state["status"] = "off"
        client.publish(TOPIC_AC_STATE, json.dumps(ac_state, ensure_ascii=False))


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    if MQTT_USER and MQTT_PASS:
        client.username_pw_set(MQTT_USER, MQTT_PASS)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        logger.error(f"❌ 连接MQTT Broker失败: {e}")
        return

    try:
        while True:
            env_data = {
                "temperature": round(random.uniform(22, 28), 1),
                "humidity": round(random.uniform(45, 65), 1),
                "light": round(random.uniform(10, 60), 1),
            }
            client.publish(TOPIC_ENV, json.dumps(env_data, ensure_ascii=False))
            logger.info(f"📤 上报环境数据: {env_data}")
            time.sleep(ENV_REPORT_INTERVAL)
    except KeyboardInterrupt:
        logger.info("🛑 设备模拟器已停止")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
