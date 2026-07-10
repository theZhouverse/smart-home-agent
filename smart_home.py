import logging
import time
from environment_agent import EnvironmentAgent
from decision_agent import DecisionAgent
from control_agent import ControlAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("smart_home")


class SmartHomeSystem:
    def __init__(self):
        logger.info("🚀 初始化智能家居系统...")

        # 共享单个EnvironmentAgent实例
        self.env_agent = EnvironmentAgent()
        self.env_agent.start()
        time.sleep(3)

        self.decision_agent = DecisionAgent(env_agent=self.env_agent)
        self.control_agent = ControlAgent(env_agent=self.env_agent)

        logger.info("✅ 智能家居系统初始化完成")

    def _safe_device_state(self, device_id):
        """安全获取设备状态"""
        devices = self.env_agent.get_state().get("devices", {})
        state = devices.get(device_id, {})
        if state:
            return (f"状态={state.get('status', 'unknown')}, "
                    f"亮度={state.get('brightness', 'N/A')}, "
                    f"温度={state.get('temperature', 'N/A')}℃")
        return "等待数据..."

    def run(self):
        print("\n=====================================")
        print("🎯 智能家居控制系统（支持的指令）：")
        print("   - 回家模式 | 睡眠模式")
        print("   - 打开灯 | 关闭灯 | 打开空调 | 关闭空调")
        print("   - 退出")
        print("=====================================\n")

        while True:
            user_cmd = input("请输入控制指令: ").strip()

            if user_cmd == "退出":
                logger.info("🛑 退出智能家居系统")
                break

            if not user_cmd:
                print("⚠️ 指令不能为空，请重新输入")
                continue

            decisions = self.decision_agent.make_decision(user_cmd)
            if not decisions:
                print("❌ 无匹配的控制决策，请输入支持的指令")
                continue

            print(f"\n📝 开始执行决策: {decisions}")
            success_count = 0
            for decision in decisions:
                if self.control_agent.execute_decision(decision):
                    success_count += 1
                    time.sleep(1)

            env_state = self.env_agent.get_state().get("environment", {})
            print(f"\n✅ 执行完成：成功{success_count}/{len(decisions)}条指令")
            print(f"🌡️ 当前环境状态: {env_state}")
            print(f"💡 当前灯状态: {self._safe_device_state('light_001')}")
            print(f"❄️ 当前空调状态: {self._safe_device_state('ac_001')}\n")

    def stop(self):
        self.env_agent.stop()
        self.control_agent.stop()
        logger.info("🛑 智能家居系统已停止")


if __name__ == "__main__":
    smart_home = None
    try:
        smart_home = SmartHomeSystem()
        smart_home.run()
    except KeyboardInterrupt:
        print("\n⚠️ 手动终止程序")
    finally:
        if smart_home:
            smart_home.stop()
