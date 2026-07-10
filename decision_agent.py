import logging
import time
from environment_agent import EnvironmentAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("decision_agent")


class DecisionAgent:
    def __init__(self, env_agent=None):
        """接收外部传入的EnvironmentAgent实例（避免重复创建）"""
        if env_agent is None:
            self.env_agent = EnvironmentAgent()
            self.env_agent.start()
            time.sleep(2)
        else:
            self.env_agent = env_agent

    def _get_latest_state(self):
        return self.env_agent.get_state()

    def make_decision(self, user_command):
        state = self._get_latest_state()
        env_data = state["environment"]
        decisions = []

        logger.info(f"🤔 收到用户指令: {user_command} | 环境数据: {env_data}")

        # 回家模式
        if "回家模式" in user_command:
            logger.info("📝 处理「回家模式」决策")
            light_level = env_data.get("light", 100)
            if light_level < 30:
                decisions.append({
                    "device_id": "light_001",
                    "action": "on",
                    "brightness": 80
                })
            temp = env_data.get("temperature", 25)
            if temp > 26:
                decisions.append({
                    "device_id": "ac_001",
                    "action": "on",
                    "temperature": 24
                })

        # 睡眠模式
        elif "睡眠模式" in user_command:
            logger.info("📝 处理「睡眠模式」决策")
            decisions.append({
                "device_id": "light_001",
                "action": "off"
            })
            decisions.append({
                "device_id": "ac_001",
                "action": "on",
                "temperature": 27
            })

        # 手动控制 - 打开灯
        elif "打开灯" in user_command:
            decisions.append({
                "device_id": "light_001",
                "action": "on",
                "brightness": 100
            })

        # 手动控制 - 关闭灯
        elif "关闭灯" in user_command:
            decisions.append({
                "device_id": "light_001",
                "action": "off"
            })

        # 手动控制 - 打开空调
        elif "打开空调" in user_command:
            decisions.append({
                "device_id": "ac_001",
                "action": "on",
                "temperature": 24
            })

        # 手动控制 - 关闭空调
        elif "关闭空调" in user_command:
            decisions.append({
                "device_id": "ac_001",
                "action": "off"
            })

        if not decisions:
            logger.warning(f"⚠️ 无匹配的决策: {user_command}")
        else:
            logger.info(f"✅ 生成决策: {decisions}")

        return decisions

    def stop(self):
        pass  # env_agent 由外部管理生命周期


# 测试代码
if __name__ == "__main__":
    decision_agent = DecisionAgent()

    test_commands = ["回家模式", "睡眠模式", "打开灯", "关闭灯", "打开空调", "关闭空调"]
    for cmd in test_commands:
        print(f"\n=====================")
        decisions = decision_agent.make_decision(cmd)
        print(f"用户指令: {cmd}")
        print(f"生成的控制决策: {decisions}")
        time.sleep(1)

    decision_agent.stop()
