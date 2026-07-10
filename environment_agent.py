import paho.mqtt.client as mqtt
import time
import ast
import logging
from config import MQTT_BROKER, MQTT_PORT, TOPIC_ENV, TOPIC_LIGHT_STATE, TOPIC_AC_STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("environment_agent")

# 全局状态池（单例）
GLOBAL_STATE = {
    "environment": {},
    "devices": {
        "light_001": {},
        "ac_001": {}
    }
}

class EnvironmentAgent:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """单例模式：确保全局只有一个EnvironmentAgent实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 防止重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

        self.sub_topics = [TOPIC_ENV, TOPIC_LIGHT_STATE, TOPIC_AC_STATE]
        self._started = False

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("✅ 环境感知Agent连接MQTT成功")
            for topic in self.sub_topics:
                client.subscribe(topic)
                logger.info(f"📥 订阅主题: {topic}")
        else:
            logger.error(f"❌ MQTT连接失败，错误码: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = ast.literal_eval(payload)  # 安全解析（替代eval）
            topic = msg.topic

            if topic == TOPIC_ENV:
                GLOBAL_STATE["environment"] = data
                logger.info(f"🌡️ 更新环境状态: {data}")

            elif topic == TOPIC_LIGHT_STATE:
                GLOBAL_STATE["devices"]["light_001"] = data
                logger.info(f"💡 更新灯状态: {data}")

            elif topic == TOPIC_AC_STATE:
                GLOBAL_STATE["devices"]["ac_001"] = data
                logger.info(f"❄️ 更新空调状态: {data}")

        except (ValueError, SyntaxError) as e:
            logger.error(f"❌ 解析消息失败（格式错误）: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 处理消息异常: {str(e)}")

    def start(self):
        if self._started:
            return
        try:
            self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.client.loop_start()
            self._started = True
            logger.info("🚀 环境感知Agent启动成功")
        except Exception as e:
            logger.error(f"❌ 启动Agent失败（请检查MQTT Broker是否在线）: {str(e)}")

    def stop(self):
        if not self._started:
            return
        self.client.loop_stop()
        self.client.disconnect()
        self._started = False
        logger.info("🛑 环境感知Agent已停止")

    def get_state(self):
        return GLOBAL_STATE


# 测试代码
if __name__ == "__main__":
    env_agent = EnvironmentAgent()
    env_agent.start()

    try:
        for i in range(10):
            time.sleep(1)
            print(f"\n=== 第{i+1}秒 全局状态 ===")
            print(f"环境数据: {GLOBAL_STATE['environment']}")
            print(f"灯状态: {GLOBAL_STATE['devices']['light_001']}")
            print(f"空调状态: {GLOBAL_STATE['devices']['ac_001']}")
    except KeyboardInterrupt:
        pass
    finally:
        env_agent.stop()
