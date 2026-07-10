# 智能家居多Agent系统 - 架构文档

## 1. 系统概述

基于 MQTT 协议的智能家居控制系统，采用多 Agent 协作架构，实现环境感知、智能决策和设备控制的闭环自动化。

- **通信协议**: MQTT (paho-mqtt 2.1.0)
- **Python 版本**: 3.10+
- **设计模式**: 多Agent协作、单例模式、依赖注入

---

## 2. 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     SmartHomeSystem (主控)                       │
│   smart_home.py - 用户交互入口，协调所有Agent                     │
└──────┬──────────────────────┬──────────────────────┬────────────┘
       │ 注入                  │ 注入                  │ 注入
       ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐
│DecisionAgent │    │  ControlAgent    │    │EnvironmentAgent  │
│  decision_   │◄───│  control_agent   │◄───│ environment_     │
│  agent.py    │    │  .py             │    │ agent.py (单例)  │
│              │    │                  │    │                  │
│ 根据用户指令  │    │ 执行设备控制指令  │    │ 订阅MQTT更新      │
│ +环境数据     │    │ 自省重试机制     │    │ 全局状态池        │
│ 生成决策列表  │    │                  │    │                  │
└──────┬───────┘    └────────┬─────────┘    └────────┬─────────┘
       │                     │                        │
       │                     │ publish                │ subscribe
       │                     ▼                        ▲
       │              ┌──────────────────────────────────┐
       │              │         MQTT Broker               │
       │              │     (EMQX 10.0.52.210:1883)      │
       │              └──────┬──────────────┬────────────┘
       │                     │              │
       │                     │ control      │ state/env
       │                     ▼              ▲
       │              ┌──────────────────────────────────┐
       │              │     DeviceSimulator (模拟器)      │
       │              │     device_simulator.py           │
       │              │                                   │
       │              │  模拟灯(light_001) + 空调(ac_001)  │
       │              │  5秒周期上报环境数据               │
       │              └──────────────────────────────────┘
       │
       └──────────► 决策结果: [{device_id, action, ...}]
```

---

## 3. 模块详解

### 3.1 config.py - 统一配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MQTT_BROKER` | MQTT服务器地址 | 10.0.52.210 |
| `MQTT_PORT` | MQTT端口 | 1883 |
| `MQTT_USER` / `MQTT_PASS` | MQTT认证 | admin / public |
| `TOPIC_ENV` | 环境数据主题 | tuya/home/env/living_room |
| `TOPIC_LIGHT_CONTROL` | 灯控制主题 | tuya/home/device/light_001/control |
| `TOPIC_LIGHT_STATE` | 灯状态主题 | tuya/home/device/light_001/state |
| `TOPIC_AC_CONTROL` | 空调控制主题 | tuya/home/device/ac_001/control |
| `TOPIC_AC_STATE` | 空调状态主题 | tuya/home/device/ac_001/state |
| `MAX_RETRY` | 最大重试次数 | 3 |
| `ENV_REPORT_INTERVAL` | 环境上报间隔(秒) | 5 |

### 3.2 environment_agent.py - 环境感知Agent

**职责**: 订阅 MQTT 主题，收集并维护全局环境状态。

**设计要点**:
- **单例模式**: 通过 `__new__` 确保全局只有一个实例，避免重复 MQTT 连接
- **安全解析**: 使用 `ast.literal_eval()` 替代 `eval()`，防止注入攻击
- **防重复初始化**: `__init__` 中 `_initialized` 标志避免重复创建连接
- **防重复启停**: `start()`/`stop()` 内部有状态检查

```
订阅主题:
  ├── tuya/home/env/living_room       → GLOBAL_STATE["environment"]
  ├── tuya/home/device/light_001/state → GLOBAL_STATE["devices"]["light_001"]
  └── tuya/home/device/ac_001/state   → GLOBAL_STATE["devices"]["ac_001"]
```

**数据流**:
```
MQTT消息 → _on_message() → ast.literal_eval() 解析 → 更新 GLOBAL_STATE
```

### 3.3 decision_agent.py - 决策Agent

**职责**: 根据用户指令和环境数据生成设备控制决策列表。

**设计要点**:
- **依赖注入**: 通过构造函数接收 `env_agent` 实例，不自行创建
- **环境感知决策**: 回家模式下根据光线和温度条件判断是否开灯/空调

**决策规则**:

| 用户指令 | 条件 | 生成的决策 |
|----------|------|-----------|
| 回家模式 | 光线 < 30% | 开灯(亮度80) |
| 回家模式 | 温度 > 26℃ | 开空调(24℃) |
| 睡眠模式 | 无条件 | 关灯 + 开空调(27℃) |
| 打开灯 | 无条件 | 开灯(亮度100) |
| 关闭灯 | 无条件 | 关灯 |
| 打开空调 | 无条件 | 开空调(24℃) |
| 关闭空调 | 无条件 | 关空调 |

### 3.4 control_agent.py - 设备控制Agent

**职责**: 接收决策列表，通过 MQTT 下发设备控制指令。

**设计要点**:
- **自省重试机制**: 执行前先检查设备在线状态，失败后最多重试3次
- **依赖注入**: 通过构造函数接收 `env_agent` 获取设备在线状态

**执行流程**:
```
execute_decision(decision)
  │
  ├── 1. _check_device_online(device_id)  ← 从 env_agent 获取设备状态
  │     └── 离线 → 重试最多 max_retry 次
  │
  └── 2. _send_command(device_id, action, **kwargs)
        └── 失败 → 重试最多 max_retry 次
```

### 3.5 device_simulator.py - 设备模拟器

**职责**: 模拟真实智能家居设备，接收 MQTT 控制指令并上报状态。

**设计要点**:
- **独立运行**: 作为独立进程启动，模拟真实的 IoT 设备行为
- **JSON 序列化**: 使用 `json.dumps()` 标准化消息格式

```
行为循环:
  ├── 每5秒: 发布随机环境数据(temperature/humidity/light)
  ├── 收到 light_001/control → 更新灯状态 → 发布 light_001/state
  └── 收到 ac_001/control    → 更新空调状态 → 发布 ac_001/state
```

### 3.6 smart_home.py - 主控程序

**职责**: 系统启动入口，整合三个 Agent，提供命令行交互界面。

**设计要点**:
- **单例共享**: 创建单个 `EnvironmentAgent`，注入给 `DecisionAgent` 和 `ControlAgent`
- **安全状态读取**: `_safe_device_state()` 用 `.get()` 链式调用避免 KeyError

---

## 4. MQTT 主题拓扑

```
tuya/home/
├── env/living_room          (发布: 模拟器 → 订阅: 环境Agent)
├── device/
│   ├── light_001/
│   │   ├── control          (发布: 控制Agent → 订阅: 模拟器)
│   │   └── state            (发布: 模拟器 → 订阅: 环境Agent)
│   └── ac_001/
│       ├── control          (发布: 控制Agent → 订阅: 模拟器)
│       └── state            (发布: 模拟器 → 订阅: 环境Agent)
```

---

## 5. 核心数据流

```
用户输入 "回家模式"
      │
      ▼
SmartHomeSystem.run()
      │
      ▼
DecisionAgent.make_decision("回家模式")
      │ 读取 env_agent.get_state()["environment"]
      │ 判断: light < 30% → 开灯, temp > 26℃ → 开空调
      ▼
返回: [{device_id: "light_001", action: "on", brightness: 80},
       {device_id: "ac_001", action: "on", temperature: 24}]
      │
      ▼
ControlAgent.execute_decision() × 2
      │ _check_device_online() → _send_command()
      │ MQTT publish → "tuya/home/device/light_001/control"
      │ MQTT publish → "tuya/home/device/ac_001/control"
      ▼
DeviceSimulator.on_message()
      │ 更新本地状态 → publish state 主题
      ▼
EnvironmentAgent._on_message()
      │ 更新 GLOBAL_STATE
      ▼
smart_home 打印执行结果 + 当前状态
```

---

## 6. 设计亮点

| 设计 | 说明 |
|------|------|
| 单例 EnvironmentAgent | 避免3个独立 MQTT 连接，节省资源 |
| 依赖注入 | DecisionAgent/ControlAgent 通过构造函数接收 env_agent |
| 自省重试 | ControlAgent 执行前检查设备状态，失败自动重试 |
| 统一配置 | 所有常量集中在 config.py，一处修改全局生效 |
| 安全解析 | ast.literal_eval 替代 eval，防止代码注入 |
