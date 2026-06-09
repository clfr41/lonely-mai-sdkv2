# 怕寂寞的麦麦 (LonelyMai)

> 让麦麦 ~~在群里“闲得慌”时~~ 主动找话题聊天，扮演一个真实的“赛博群友”。

## 简介

**怕寂寞的麦麦 (LonelyMai)** 是一个 MaiBot 插件，它让麦麦不再只是被动回复消息，而是在群里冷冷清清的时候，主动跳出来找话题聊天。

当群里长时间没人说话，麦麦会根据配置的概率和条件，像真正的群友一样发条消息活跃气氛——可能是对之前聊天的吐槽，可能是突然想到的一个梗，也可能是围绕你预设的话题展开讨论。

## 特性

- 🤖 **赛博群友模式** - 麦麦扮演真实网友，语气随意、接地气，带网络用语和颜文字
- 🎲 **概率触发** - 可配置触发概率，避免麦麦话太多或太沉默
- 🕐 **时间段控制** - 只在指定时间段内主动聊天（如 08:00-23:00）
- 📝 **多种话题来源**
  - `history` - 根据历史聊天记录找话题延续、吐槽或联想
  - `knowledge` - 根据麦麦的人设、知识库、当前时间/季节自由发挥
  - `preset` - 从预置话题列表中随机选择，麦麦围绕主题展开
  - `mixed` - 混合模式，按权重随机选择以上一种
- 🎯 **白名单机制** - 精确控制插件在哪些群或私聊中生效
- ⏱️ **智能间隔** - 支持检查间隔随机波动，让麦麦行为更自然
- 🚫 **隔离时间** - 群里有人聊天时不插嘴，避免打断正常对话
- 📊 **详细日志** - 可配置日志详细程度，方便排查和观察运行状态
- 🎭 **表达风格** - 可额外指定麦麦的说话风格（傲娇、活泼等）
- 🔧 **手动触发** - 支持使用命令 `/lonelymai` 立即触发一次主动发言

## 安装

1. 将本插件文件夹复制到 MaiBot 的插件目录下
2. 重启 MaiBot
3. 修改 `config.toml` 配置白名单和其他参数
4. 再次重启或等待插件自动加载

## 全局配置依赖

本插件会读取 MaiBot 的以下全局配置（若未设置则使用默认值）：

| 全局配置键 | 用途 | 默认值 |
|-----------|------|--------|
| `bot.qq_account` | Bot 自身的 QQ 号，用于过滤历史消息中的机器人消息 | `""`（空） |
| `bot.nickname` | Bot 昵称，用于主动聊天时的自称 | `"麦麦"` |
| `personality.personality` | Bot 人格描述，影响发言风格 | `"一位热心的群友"` |

> 请确保这些全局配置已正确填写，否则可能影响历史消息过滤和发言风格。

## 配置说明

配置文件位于 `config.toml`，各配置项详细说明如下：

### 基础配置 `[plugin]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `true` | 是否启用插件 |
| `config_version` | string | `"1.2.0"` | 配置文件版本号（内部使用，请勿修改） |
| `version` | string | `"1.2.0"` | 插件版本号 |

### 调度配置 `[scheduler]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | bool | `true` | 是否开启主动聊天 |
| `start_time` | string | `"08:00"` | 每日开始时间（24小时制） |
| `end_time` | string | `"23:00"` | 每日结束时间（24小时制） |
| `check_interval` | int | `30` | 检查间隔（分钟） |
| `jitter` | int | `5` | 波动时间（分钟），实际间隔在 `check_interval ± jitter` 之间随机 |
| `probability` | float | `0.2` | 触发概率（0.0~1.0），每次检查时有此概率触发主动聊天 |
| `min_interval_between_chats` | int | `60` | 两次主动聊天之间的最小间隔（分钟） |
| `isolation_time` | int | `15` | 隔离时间（分钟），群内有人发消息后在此时间内不触发 |

**触发概率计算公式：**
```
每小时期望触发次数 = (60 / check_interval) * probability
```
例如 `check_interval=30, probability=0.2`：每小时检查 2 次，期望触发 0.4 次，约每 2.5 小时触发 1 次。

### 白名单配置 `[target]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `allowed_groups` | list | `[]` | 允许的群号列表（字符串数组），**为空则不允许任何群聊** |
| `allowed_friends` | list | `[]` | 允许的 QQ 号列表（字符串数组），**为空则不允许任何私聊** |

⚠️ **重要：** 必须至少配置一个群号或 QQ 号，否则插件不会在任何地方生效！

### 话题配置 `[topic]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `topic_source` | string | `"mixed"` | 话题来源模式：`history` / `knowledge` / `preset` / `mixed` |
| `mixed_history_weight` | float | `1.0` | Mixed 模式下 history 来源的权值（仅 mixed 模式生效） |
| `mixed_knowledge_weight` | float | `1.0` | Mixed 模式下 knowledge 来源的权值（仅 mixed 模式生效） |
| `mixed_preset_weight` | float | `1.0` | Mixed 模式下 preset 来源的权值（仅 mixed 模式生效） |

**历史记录模式 `[topic.history]`：**

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `recent_message_count` | int | `15` | 读取最近多少条历史消息 |
| `recent_hours` | int | `24` | 读取最近多少小时内的消息 |

**预置话题模式 `[topic.preset]`：**

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `topics` | list | `["游戏", "美食", "动漫", "最近的新闻", "天气", "音乐"]` | 预置话题主题列表 |
| `allow_free_play` | bool | `true` | 是否允许麦麦偏离主题自由发挥 |
| `topic_weights` | list | `[]` | 预置话题权值列表，与 topics 一一对应，为空则均匀随机 |

### 消息配置 `[message]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `show_current_time` | bool | `false` | 是否在消息前附带当前时间 |
| `time_format` | string | `"%H:%M"` | 时间格式 |
| `time_prefix_template` | string | `""` | 时间前缀模板，`{time}` 会被替换为当前时间 |

### 日志配置 `[log]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `verbose` | bool | `true` | 是否打印详细日志（跳过原因、检查过程等） |
| `scheduler_log` | bool | `true` | 是否打印调度器运行日志（每次检查的概览） |

### LLM 配置 `[llm]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `model_name` | string | `"replyer"` | 使用的模型名称，对应宿主 task 名 |
| `max_tokens` | int | `200` | 最大输出 token 数（范围 10~2000） |

### 表达风格配置 `[persona]`

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `speak_style` | string | `""` | 主动发言的额外风格要求（配合全局人格使用），如 `"随性活泼，喜欢用短句和表情"` |

## 手动触发

在任何白名单会话中发送 `/lonelymai` 命令，可以立即触发一次主动发言。

- 此命令会忽略时间范围、概率和两次发言最小间隔限制
- 但仍受 `isolation_time`（隔离时间）影响，若群内刚有人发言则不会触发
- 执行成功会返回“已触发主动发言”

### Prompt 模板配置 `[prompt]`

用于自定义不同话题来源下的开场白模板，支持 `{nick}` 和 `{persona}` 两个变量占位符，会分别替换为 Bot 昵称和人格描述。

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `history_intro` | string | `"你是 {nick}, {persona}. 有一段时间没有发消息了, 你决定做些什么."` | history 模式下的开场白 |
| `preset_intro` | string | `"你是 {nick}, {persona}. 现在聊天里冷场了, 你想发条消息活跃一下."` | preset 模式下的开场白 |
| `knowledge_intro` | string | `"你是 {nick}, {persona}. 现在聊天里冷场了, 你想发条消息活跃一下."` | knowledge 模式下的开场白 |

**变量说明：**
- `{nick}` – Bot 昵称，来自全局配置 `bot.nickname`
- `{persona}` – Bot 人格描述，来自全局配置 `personality.personality`

通过修改这些模板，你可以调整麦麦在主动聊天前的“自我定位”或“说话动机”，使其更贴合你想要的角色扮演风格。



## 配置示例

### 基础配置（推荐）

```toml
[target]
allowed_groups = ["123456789"]
allowed_friends = []

[scheduler]
check_interval = 30
jitter = 5
probability = 0.2
min_interval_between_chats = 60
isolation_time = 15

[topic]
topic_source = "mixed"

[llm]
model_name = "replyer"
max_tokens = 200

[persona]
speak_style = ""

[log]
verbose = true
scheduler_log = true
```

### 活跃模式（麦麦更频繁主动聊天）

```toml
[scheduler]
check_interval = 15
jitter = 3
probability = 0.3
min_interval_between_chats = 30
isolation_time = 10
```

### 预置话题模式（让麦麦聊特定主题）

```toml
[topic]
topic_source = "preset"

[topic.preset]
topics = ["原神", "崩坏：星穹铁道", "绝区零", "米哈游新游"]
allow_free_play = true
```

### 历史记录模式（延续群聊话题）

```toml
[topic]
topic_source = "history"

[topic.history]
recent_message_count = 15
recent_hours = 12
```

### 自定义表达风格

```toml
[persona]
speak_style = "傲娇，喜欢用'哼'和'～'，偶尔使用颜文字"
```

### 自定义开场白

[prompt]
history_intro = "咱是 {nick}，{persona}。好久没人说话了，有点寂寞，来冒个泡～"
preset_intro = "{nick}在此！{persona}，看群里冷场了，决定整点活。"
knowledge_intro = "咳咳，{nick}要开始表演了～（{persona}模式）"


## 工作原理

1. **初始化** - Bot 启动时，插件根据白名单注册需要监控的聊天流
2. **定时检查** - 按照 `check_interval ± jitter` 的间隔定期检查
3. **条件判断** - 每次检查判断是否满足以下条件：
   - 当前时间在 `start_time` ~ `end_time` 范围内
   - 距离上次主动聊天已超过 `min_interval_between_chats`
   - 距离群内最后一条消息已超过 `isolation_time`
4. **概率判定** - 生成一个 0~1 的随机数，如果小于 `probability` 则触发
5. **话题生成** - 根据 `topic_source` 选择话题来源，构建提示词调用 LLM 生成消息
6. **发送消息** - 将生成的消息发送到对应的群或私聊

## 日志示例

```
[插件] ✅ LonelyMai v1.2.0 已加载
[启动] ✅ LonelyMai 主动聊天定时任务已启动
[调度器] 开始初始化聊天流...
[调度器] 群聊白名单: ['123456789']
[调度器] ✅ 注册群聊流 | group_id=123456789, stream_id=abc123
[调度器] 🎉 初始化完成，共注册 1 个聊天流

[调度器] ===== 第 1 轮检查 ===== 目标: 1 个聊天流
[调度器][123456789] ⏭ 跳过: 当前时间 02:15 不在允许的时间段 08:00-23:00 内
[调度器] ===== 第 1 轮检查结束 ===== 触发: 0 个

[调度器] ===== 第 5 轮检查 ===== 目标: 1 个聊天流
[调度器][123456789] 🎯 概率判定通过 (0.1523 <= 0.2000)，触发主动聊天！
[主动聊天][123456789] 📋 话题来源: preset
[主动聊天][123456789] 🎯 使用 preset 模式，选中主题: '美食'
[主动聊天][123456789] ✅ 消息已发送: 突然好想吃火锅，有人推荐好吃的店吗
[调度器][123456789] ✅ 主动聊天执行完毕
[调度器] ===== 第 5 轮检查结束 ===== 触发: 1 个
```

## 常见问题

### Q: 插件加载了但没有触发主动聊天？

A: 请检查以下几点：
1. 白名单是否配置正确（`allowed_groups` 或 `allowed_friends` 必须至少配置一个）
2. 当前时间是否在 `start_time` ~ `end_time` 范围内
3. `scheduler.enabled` 是否为 `true`
4. 将 `log.verbose` 设为 `true` 观察日志，查看跳过原因

### Q: 麦麦主动聊天太频繁/太稀少？

A: 调整 `probability` 和 `check_interval`：
- 太频繁：降低 `probability` 或增大 `check_interval`
- 太稀少：提高 `probability` 或减小 `check_interval`

### Q: 如何获取群号？

A: 
- 在 QQ 群资料中查看群号
- 或观察插件启动日志中的 `注册群聊流 | group_id=xxx`

### Q: 支持私聊吗？

A: 支持，但不推荐。私聊场景下麦麦主动找话题可能显得突兀 ~~感觉像是性骚扰一样~~ ，建议主要用于群聊。

### Q: 话题来源选哪种好？

A: 
- 群比较活跃、有历史记录 → `history` 或 `mixed`
- 群比较冷清、想开启新话题 → `knowledge` 或 `preset`
- 想让麦麦聊特定~~奇♂妙~~主题 → `preset`
- 不确定 → `mixed`（推荐）

### Q: 如何自定义麦麦的说话风格？

A: 在 `[persona]` 中设置 `speak_style`，例如 `"傲娇，喜欢用'哼'和'～'"`。此外，全局配置 `personality.personality` 也会影响整体人格。

### Q: `/lonelymai` 命令不生效？

A: 确保当前会话已在白名单中（`allowed_groups` 或 `allowed_friends`），且插件已启用。命令返回“当前会话未在白名单中”时请检查白名单配置。

## 版本历史

### v1.2.0 by clfr41(RIEZ-ON)
- 将插件更新至符合 SDK v2 规范（适用于 MaiBot 1.0.0+）
- 新增 `[llm]` 配置节，支持自定义模型名称和 max_tokens
- 新增 `[persona]` 配置节，支持表达风格定制
- 新增 `[prompt]` 配置节，支持自定义各模式下的开场白模板（`{nick}`、`{persona}` 变量）
- 新增手动触发命令 `/lonelymai`
- 增加对全局配置 `bot.qq_account`、`bot.nickname`、`personality.personality` 的依赖
- 修正 `[topic.history]` 中 `recent_message_count` 默认值（15）
- 一些其他的小问题修复

### v1.1.0
- 新增 Mixed 模式下各话题来源的权值配置（`mixed_history_weight` / `mixed_knowledge_weight` / `mixed_preset_weight`），可按比例控制不同话题来源的选中概率
- 新增预置话题的权值配置（`topic_weights`），可按比例控制不同预置话题的选中概率

### v1.0.0
- 初始版本
- 支持 history/knowledge/preset/mixed 四种话题来源
- 支持白名单机制
- 支持检查间隔随机波动
- 支持隔离时间机制
- 支持详细日志配置
```