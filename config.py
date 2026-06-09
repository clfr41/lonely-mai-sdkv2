"""LonelyMai 插件配置模型。"""

from typing import List
from maibot_sdk import Field, PluginConfigBase


class PluginSection(PluginConfigBase):
    enabled: bool = Field(default=True, description="是否启用插件")
    config_version: str = Field(default="1.2.0", description="配置文件版本号")
    version: str = Field(default="1.2.0", description="插件版本")


class SchedulerSection(PluginConfigBase):
    enabled: bool = Field(default=True, description="是否开启主动聊天")
    start_time: str = Field(default="08:00", description="每日开始时间 (HH:MM)")
    end_time: str = Field(default="23:00", description="每日结束时间 (HH:MM)")
    check_interval: int = Field(default=30, description="检查间隔（分钟）")
    jitter: int = Field(default=5, description="间隔波动（分钟）")
    probability: float = Field(default=0.2, description="触发概率 0~1")
    min_interval_between_chats: int = Field(default=60, description="两次主动聊天最小间隔（分钟）")
    isolation_time: int = Field(default=15, description="隔离时间（分钟）")


class TargetSection(PluginConfigBase):
    allowed_groups: List[str] = Field(default_factory=list, description="白名单群号列表")
    allowed_friends: List[str] = Field(default_factory=list, description="白名单QQ号列表")


class TopicHistorySection(PluginConfigBase):
    recent_message_count: int = Field(default=15, description="读取最近消息数量")
    recent_hours: int = Field(default=24, description="读取最近几小时内的消息")


class TopicPresetSection(PluginConfigBase):
    topics: List[str] = Field(default_factory=lambda: ["游戏","美食","动漫","最近的新闻","天气","音乐"], description="预置话题列表")
    allow_free_play: bool = Field(default=True, description="是否允许自由发挥")
    topic_weights: List[float] = Field(default_factory=list, description="话题权重列表")


class TopicSection(PluginConfigBase):
    topic_source: str = Field(default="mixed", description="模式: history/knowledge/preset/mixed")
    mixed_history_weight: float = Field(default=1.0)
    mixed_knowledge_weight: float = Field(default=1.0)
    mixed_preset_weight: float = Field(default=1.0)
    history: TopicHistorySection = Field(default_factory=TopicHistorySection)
    preset: TopicPresetSection = Field(default_factory=TopicPresetSection)


class MessageSection(PluginConfigBase):
    show_current_time: bool = Field(default=False)
    time_format: str = Field(default="%H:%M")
    time_prefix_template: str = Field(default="")


class LogSection(PluginConfigBase):
    verbose: bool = Field(default=True)
    scheduler_log: bool = Field(default=True)


class LLMSection(PluginConfigBase):
    model_name: str = Field(default="replyer", description="使用的模型名称（对应宿主 task 名）")
    max_tokens: int = Field(default=200, ge=10, le=2000, description="最大输出 token 数")


class PersonaSection(PluginConfigBase):
    """表达风格配置"""
    __ui_label__ = "表达风格"
    __ui_icon__ = "message-circle"
    __ui_order__ = 6

    speak_style: str = Field(
        default="",
        description="主动发言的额外风格要求（配合全局人格使用），如 '随性活泼，喜欢用短句和表情'"
    )


class PromptSection(PluginConfigBase):
    """Prompt 模板配置 - 各模式下的开场白"""
    history_intro: str = Field(
        default="你是 {nick}, {persona}. 有一段时间没有发消息了, 你决定做些什么.",
        description="history 模式下的开场白模板，支持 {nick}, {persona} 变量"
    )
    preset_intro: str = Field(
        default="你是 {nick}, {persona}. 现在聊天里冷场了, 你想发条消息活跃一下.",
        description="preset 模式下的开场白模板"
    )
    knowledge_intro: str = Field(
        default="你是 {nick}, {persona}. 现在聊天里冷场了, 你想发条消息活跃一下.",
        description="knowledge 模式下的开场白模板"
    )


class LonelyMaiConfig(PluginConfigBase):
    plugin: PluginSection = Field(default_factory=PluginSection)
    scheduler: SchedulerSection = Field(default_factory=SchedulerSection)
    target: TargetSection = Field(default_factory=TargetSection)
    topic: TopicSection = Field(default_factory=TopicSection)
    message: MessageSection = Field(default_factory=MessageSection)
    log: LogSection = Field(default_factory=LogSection)
    llm: LLMSection = Field(default_factory=LLMSection)
    persona: PersonaSection = Field(default_factory=PersonaSection)
    prompt: PromptSection = Field(default_factory=PromptSection)   # 新增