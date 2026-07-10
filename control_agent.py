import paho.mqtt.client as mqtt
import logging
import time
from config import MQTT_BROKER, MQTT_PORT, DEVICE_TOPIC_MAP, MAX_RETRY, RETRY_INTERVAL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("control_agent")


class ControlAgent:
    def __init__(self, env_agent=None):
        self.env_agent = env_agent

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"❌ MQTT连接失败: {e}")

        self.max_retry = MAX_RETRY
        self.retry_interval = RETRY_INTERVAL

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("✅ 设备控制Agent连接MQTT成功")
        else:
            logger.error(f"❌ MQTT连接失败，错误码: {rc}")

    def _check_device_online(self, device_id):
        if self.env_agent is None:
            return device_id in DEVICE_TOPIC_MAP

        device_state = self.env_agent.get_state()["devices"].get(device_id, {})
        is_online = bool(device_state) or device_id in DEVICE_TOPIC_MAP
        logger.info(f"🔍 检查设备 {device_id} 在线状态: {is_online}")
        return is_online

    def _send_command(self, device_id, action, **kwargs):
        if device_id not in DEVICE_TOPIC_MAP:
            logger.error(f"❌ 未知设备: {device_id}")
            return False

        command = action
        if kwargs:
            command += f" {kwargs}"

        topic = DEVICE_TOPIC_MAP[device_id]
        result = self.client.publish(topic, command)
        result.wait_for_publish()

        if result.rc == 0:
            logger.info(f"📤 下发指令成功: {device_id} → {command}")
            return True
        else:
            logger.error(f"❌ 下发指令失败: {device_id} → {command}")
            return False

    def execute_decision(self, decision):
        device_id = decision["device_id"]
        action = decision["action"]
        kwargs = {k: v for k, v in decision.items() if k not in ["device_id", "action"]}

        if not self._check_device_online(device_id):
            logger.warning(f"⚠️ 设备 {device_id} 离线，开始重试...")
            for retry in range(self.max_retry):
                time.sleep(self.retry_interval)
                if self._check_device_online(device_id):
                    logger.info(f"✅ 设备 {device_id} 在线（重试{retry+1}次）")
                    break
                if retry == self.max_retry - 1:
                    logger.error(f"❌ 设备 {device_id} 重试{self.max_retry}次仍离线")
                    return False

        for retry in range(self.max_retry):
            if self._send_command(device_id, action, **kwargs):
                return True
            else:
                logger.warning(f"⚠️ 下发指令重试 {retry+1}/{self.max_retry}")
                time.sleep(self.retry_interval)

        logger.error(f"❌ 指令执行失败（重试{self.max_retry}次）: {decision}")
        return False

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("🛑 设备控制Agent已停止")


# 测试代码
if __name__ == "__main__":
    from environment_agent import EnvironmentAgent

    env = EnvironmentAgent()
    env.start()
    time.sleep(2)

    control_agent = ControlAgent(env_agent=env)

    test_decision = {"device_id": "light_001", "action": "on", "brightness": 100}
    print("\n=== 执行测试决策：打开灯 ===")
    success = control_agent.execute_decision(test_decision)
    print(f"指令执行结果: {'成功' if success else '失败'}")

    time.sleep(3)

    test_decision2 = {"device_id": "ac_001", "action": "on", "temperature": 24}
    print("\n=== 执行测试决策：开空调 ===")
    success2 = control_agent.execute_decision(test_decision2)
    print(f"指令执行结果: {'成功' if success2 else '失败'}")

    control_agent.stop()
    env.stop()
