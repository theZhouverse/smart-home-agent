"""智能家居系统统一配置"""

# MQTT连接配置
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_USER = None
MQTT_PASS = None

# MQTT主题定义
TOPIC_ENV = "tuya/home/env/living_room"
TOPIC_LIGHT_CONTROL = "tuya/home/device/light_001/control"
TOPIC_LIGHT_STATE = "tuya/home/device/light_001/state"
TOPIC_AC_CONTROL = "tuya/home/device/ac_001/control"
TOPIC_AC_STATE = "tuya/home/device/ac_001/state"

# 设备控制主题映射
DEVICE_TOPIC_MAP = {
    "light_001": TOPIC_LIGHT_CONTROL,
    "ac_001": TOPIC_AC_CONTROL,
}

# 默认环境数据上报间隔（秒）
ENV_REPORT_INTERVAL = 5

# 控制Agent重试配置
MAX_RETRY = 3
RETRY_INTERVAL = 1
