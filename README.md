# Smart Home Agent - 智能家居多Agent控制系统

基于 MQTT 协议的多 Agent 协作智能家居系统，实现 **环境感知 → 智能决策 → 设备控制** 的完整自动化闭环。

## 系统架构

```
用户指令 ──→ DecisionAgent ──→ ControlAgent ──→ MQTT ──→ 设备模拟器
                │                  │                          │
                │ 查询环境          │ 检查在线                  │ 上报状态
                ▼                  ▼                          ▼
           EnvironmentAgent ◄──────────────────── MQTT 状态消息
```

| Agent | 职责 |
|-------|------|
| EnvironmentAgent | 订阅 MQTT 主题，维护环境和设备全局状态 |
| DecisionAgent | 根据用户指令 + 环境数据，生成控制决策列表 |
| ControlAgent | 带自省重试机制，通过 MQTT 下发设备控制指令 |

## 快速开始

### 环境要求

- Python 3.10+
- MQTT Broker（Mosquitto / EMQX）
- paho-mqtt 2.1.0

### 安装依赖

```bash
pip install paho-mqtt
```

### 启动

**终端 1 — 设备模拟器：**
```bash
python device_simulator.py
```

**终端 2 — 主控程序：**
```bash
python smart_home.py
```

### 使用

```
请输入控制指令: 回家模式
请输入控制指令: 睡眠模式
请输入控制指令: 打开灯
请输入控制指令: 关闭空调
```

## 项目结构

```
smart-home-agent/
├── config.py              # 统一配置（MQTT地址、主题、重试参数）
├── device_simulator.py    # 设备模拟器（模拟灯和空调，周期性上报数据）
├── environment_agent.py   # 环境感知Agent（订阅MQTT，维护全局状态）
├── decision_agent.py      # 决策Agent（指令+环境 → 控制决策）
├── control_agent.py       # 控制Agent（下发指令，自省重试）
├── smart_home.py          # 主控程序（整合三层Agent，CLI交互）
├── ARCHITECTURE.md        # 架构详细文档
└── STARTUP.md             # 启动说明文档
```

## 设计特点

- **多 Agent 协作**：感知/决策/执行三层解耦，Agent 间通过 MQTT 通信
- **单例共享**：EnvironmentAgent 全局唯一，通过依赖注入共享
- **自省重试**：ControlAgent 执行前检查设备在线状态，失败自动重试
- **安全解析**：使用 `ast.literal_eval` 替代 `eval` 防止注入
- **统一配置**：所有常量和主题集中在 `config.py` 管理
