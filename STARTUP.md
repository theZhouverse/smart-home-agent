# 智能家居多Agent系统 - 启动指南

## 1. 环境要求

| 依赖 | 版本 | 状态 |
|------|------|------|
| Python | 3.10+ | ✅ Anaconda (D:\Anaconda) |
| MQTT Broker | Mosquitto 2.0.20 | ✅ 已安装为 Windows 服务 (localhost:1883) |
| paho-mqtt | 2.1.0 | ✅ 已安装 |

---

## 2. 启动顺序

> **重要**: 必须按以下顺序启动。

### 第一步：确认 MQTT Broker 运行中

Mosquitto 已安装为 Windows 服务，开机自启。验证：

```powershell
Get-Service mosquitto | Select-Object Status
# 应输出: Running
```

如果未运行：
```powershell
Start-Service mosquitto
```

### 第二步：启动设备模拟器

新开一个终端：

```powershell
cd d:\projects\smart-home-agent-master\smart-home-agent-master
python device_simulator.py
```

预期输出：
```
✅ 设备模拟器连接MQTT成功
📤 上报环境数据: {'temperature': 26.5, 'humidity': 61.4, 'light': 55.1}
📤 上报环境数据: {'temperature': 25.0, 'humidity': 60.4, 'light': 49.4}
...
```

### 第三步：启动主控程序

再新开一个终端：

```powershell
cd d:\projects\smart-home-agent-master\smart-home-agent-master
python smart_home.py
```

预期输出：
```
🚀 初始化智能家居系统...
✅ 环境感知Agent连接MQTT成功
📥 订阅主题: tuya/home/env/living_room
📥 订阅主题: tuya/home/device/light_001/state
📥 订阅主题: tuya/home/device/ac_001/state
✅ 智能家居系统初始化完成

=====================================
🎯 智能家居控制系统（支持的指令）：
   - 回家模式 | 睡眠模式
   - 打开灯 | 关闭灯 | 打开空调 | 关闭空调
   - 退出
=====================================

请输入控制指令:
```

---

## 3. 使用示例

```
请输入控制指令: 打开灯

📝 开始执行决策: [{'device_id': 'light_001', 'action': 'on', 'brightness': 100}]
📤 下发指令成功: light_001 → on {'brightness': 100}
✅ 执行完成：成功1/1条指令
🌡️ 当前环境状态: {'temperature': 25.3, 'humidity': 52.1, 'light': 35.7}
💡 当前灯状态: 状态=on, 亮度=80, 温度=N/A℃
❄️ 当前空调状态: 状态=off, 亮度=N/A, 温度=25℃
```

---

## 4. 自动化测试

```powershell
# 模块导入测试（无需 Broker）
python test_modules.py

# 端到端集成测试（需先启动模拟器）
python test_integration.py
```

---

## 5. 配置说明

MQTT 连接配置在 [config.py](file:///d:/projects/smart-home-agent-master/smart-home-agent-master/config.py)：

```python
MQTT_BROKER = "localhost"   # Mosquitto 本机地址
MQTT_PORT = 1883
MQTT_USER = None            # Mosquitto 本地模式无需认证
MQTT_PASS = None
```

---

## 6. 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `❌ MQTT连接失败` | Mosquitto 服务未启动 | `Start-Service mosquitto` |
| `❌ 解析消息失败` | 消息格式异常 | 检查模拟器是否正常发送数据 |
| `⚠️ 无匹配的控制决策` | 输入了不支持的指令 | 输入支持的关键词 |
| 端口被占用 | 已有进程占用 1883 | `netstat -ano \| findstr 1883` 查看 |

---

## 7. 停止系统

1. 主控终端按 `Ctrl+C`
2. 模拟器终端按 `Ctrl+C`
3. Mosquitto 服务不需要停止（Windows 服务后台运行即可）
