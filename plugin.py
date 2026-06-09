"""怕寂寞的麦麦 (LonelyMai) 新版适配 -- 完整内聚,不依赖额外文件."""

import asyncio
import random
import time
from datetime import datetime, time as datetime_time
from typing import Any, Dict, Optional

from maibot_sdk import Command, MaiBotPlugin

from .config import LonelyMaiConfig


# ==================== 工具函数（内嵌） ====================

def peel_envelope(data: Any, max_depth: int = 4) -> Any:
    """递归脱掉 {"success": True, "result": {...}} 信封。"""
    for _ in range(max_depth):
        if isinstance(data, dict) and "success" in data and "result" in data:
            data = data["result"]
        else:
            break
    return data


def parse_time(time_str: str) -> datetime_time:
    hour, minute = map(int, time_str.split(":"))
    return datetime_time(hour, minute)


def is_in_time_range(current: datetime_time, start: datetime_time, end: datetime_time) -> bool:
    if start <= end:
        return start <= current <= end
    else:  # 跨夜
        return current >= start or current <= end


# ==================== 聊天流状态 ====================

class ChatStreamState:
    def __init__(self, stream_id: str, target_id: str):
        self.stream_id = stream_id
        self.target_id = target_id
        self.last_proactive_time: float = 0.0


# ==================== 插件主类 ====================

class LonelyMaiPlugin(MaiBotPlugin):
    config_model = LonelyMaiConfig

    def __init__(self):
        super().__init__()
        self._states: Dict[str, ChatStreamState] = {}
        self._scheduler_task: Optional[asyncio.Task] = None
        self._bot_qq: str = ""
        self._persona: str = ""
        self._nickname: str = "麦麦"

    # ========== 生命周期 ==========

    async def on_load(self) -> None:
        if not self.config.plugin.enabled:
            self.ctx.logger.info("LonelyMai 已禁用")
            return

        # 防止重复启动
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None

        self._bot_qq = await self._get_global_str("bot.qq_account", "")
        self._persona = await self._get_global_str("personality.personality", "一位热心的群友")
        self._nickname = await self._get_global_str("bot.nickname", "麦麦")

        await self._init_target_streams()

        self._scheduler_task = asyncio.create_task(self._schedule_loop())
        self.ctx.logger.info("LonelyMai 调度器已启动")

    async def on_unload(self) -> None:
        if self._scheduler_task and not self._scheduler_task.done():
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        self.ctx.logger.info("LonelyMai 已卸载")

    async def on_config_update(self, *args, **kwargs):
        """配置热更新回调（预留）。"""
        pass

    async def _get_global_str(self, key: str, default: str = "") -> str:
        try:
            val = await self.ctx.config.get(key, default)
        except Exception as e:
            self.ctx.logger.warning(f"读取全局配置 {key} 失败: {e}")
            return default
        val = peel_envelope(val)
        if isinstance(val, dict):
            val = val.get("value", default)
        return str(val or default)

    async def _init_target_streams(self) -> None:
        self._states.clear()
        for group_qq in self.config.target.allowed_groups:
            sid = await self._resolve_session_id(group_qq, True)
            if sid:
                self._states[group_qq] = ChatStreamState(sid, group_qq)
                self.ctx.logger.info(f"注册群聊: {group_qq}")
            else:
                self.ctx.logger.warning(f"无法解析群聊: {group_qq}")

        for user_qq in self.config.target.allowed_friends:
            sid = await self._resolve_session_id(user_qq, False)
            if sid:
                self._states[user_qq] = ChatStreamState(sid, user_qq)
                self.ctx.logger.info(f"注册私聊: {user_qq}")
            else:
                self.ctx.logger.warning(f"无法解析私聊: {user_qq}")

        self.ctx.logger.info(f"共注册 {len(self._states)} 个目标流")

    async def _resolve_session_id(self, qq: str, is_group: bool) -> Optional[str]:
        try:
            if is_group:
                result = await self.ctx.chat.get_stream_by_group_id(qq)
            else:
                result = await self.ctx.chat.get_stream_by_user_id(qq)
        except Exception as e:
            self.ctx.logger.error(f"ctx.chat 查询失败 ({qq}): {e}")
            return None

        result = peel_envelope(result)
        if not isinstance(result, dict):
            return None

        stream = result.get("stream", result if "session_id" in result else None)
        if not stream:
            return None
        if isinstance(stream, dict):
            return stream.get("session_id") or stream.get("stream_id")
        return getattr(stream, "session_id", None) or getattr(stream, "stream_id", None)

    # ========== 调度循环 ==========

    async def _schedule_loop(self) -> None:
        while True:
            try:
                if not self.config.plugin.enabled or not self.config.scheduler.enabled:
                    await asyncio.sleep(60)
                    continue

                base_interval = max(1, self.config.scheduler.check_interval)
                jitter = self.config.scheduler.jitter
                actual_minutes = base_interval + random.randint(-jitter, jitter) if jitter > 0 else base_interval
                sleep_seconds = max(60, actual_minutes * 60)

                self.ctx.logger.info(f"[调度器] 下次检查: +{sleep_seconds // 60}min")
                await asyncio.sleep(sleep_seconds)

                for target_id, state in list(self._states.items()):
                    if (target_id not in self.config.target.allowed_groups and
                        target_id not in self.config.target.allowed_friends):
                        continue

                    try:
                        await self._check_and_trigger(state, target_id)
                    except Exception as e:
                        self.ctx.logger.error(f"[{target_id}] 检查异常: {e}", exc_info=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.ctx.logger.error(f"调度器异常: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _check_and_trigger(self, state: ChatStreamState, target_id: str) -> None:
        cfg = self.config
        now = datetime.now()
        current_time = now.time()
        start = parse_time(cfg.scheduler.start_time)
        end = parse_time(cfg.scheduler.end_time)

        if not is_in_time_range(current_time, start, end):
            return

        min_interval = cfg.scheduler.min_interval_between_chats * 60
        if state.last_proactive_time and (now.timestamp() - state.last_proactive_time) < min_interval:
            return

        isolation_seconds = cfg.scheduler.isolation_time * 60
        if isolation_seconds > 0:
            last_msg_time = await self._get_last_msg_time(state.stream_id)
            if last_msg_time is not None and (now.timestamp() - last_msg_time) < isolation_seconds:
                return

        if random.random() >= cfg.scheduler.probability:
            return

        self.ctx.logger.info(f"[{target_id}] 🎯 触发主动聊天")
        if await self._do_proactive_chat(state, target_id):
            state.last_proactive_time = now.timestamp()

    # ========== 消息时间查询 ==========

    async def _get_last_msg_time(self, session_id: str) -> Optional[float]:
        """获取最近一条非 bot 消息的时间戳。"""
        try:
            end_ts = time.time()
            start_ts = end_ts - 3600 * 24 * 7  # 一周内
            raw = await self.ctx.message.get_by_time_in_chat(
                session_id,
                start_time=str(start_ts),
                end_time=str(end_ts),
                limit=5,
                limit_mode="latest",
            )
            raw = peel_envelope(raw)
            if not isinstance(raw, list):
                return None

            for msg in raw:
                if not isinstance(msg, dict):
                    continue
                sender_id = self._get_msg_user_id(msg)
                if self._bot_qq and sender_id == self._bot_qq:
                    continue
                ts = msg.get("timestamp", 0)
                try:
                    return float(ts)
                except (TypeError, ValueError):
                    pass
            return None
        except Exception:
            return None

    # ========== 主动聊天核心 ==========

    async def _do_proactive_chat(self, state: ChatStreamState, target_id: str) -> bool:
        try:
            topic_cfg = self.config.topic
            msg_cfg = self.config.message
            now = datetime.now()

            source = topic_cfg.topic_source
            if source == "mixed":
                sources = ["history", "knowledge", "preset"]
                weights = [
                    topic_cfg.mixed_history_weight,
                    topic_cfg.mixed_knowledge_weight,
                    topic_cfg.mixed_preset_weight,
                ]
                source = random.choices(sources, weights=weights, k=1)[0]

            prompt = await self._build_prompt(source, topic_cfg, now, target_id, state.stream_id)
            content = await self._call_llm(prompt, target_id)
            if not content:
                return False

            if msg_cfg.show_current_time:
                time_str = now.strftime(msg_cfg.time_format)
                prefix = msg_cfg.time_prefix_template.replace("{time}", time_str)
                final = prefix + content
            else:
                final = content

            await self.ctx.send.text(final, state.stream_id)
            self.ctx.logger.info(f"[{target_id}] ✅ 已发送: {final[:80]}")
            return True

        except Exception as e:
            self.ctx.logger.error(f"[{target_id}] 💥 主动聊天失败: {e}", exc_info=True)
            return False

    async def _build_prompt(self, source: str, topic_cfg, now: datetime, target_id: str, session_id: str) -> str:
        time_str = now.strftime("%Y年%m月%d日 %H:%M")
        persona = self._persona or "一位热心的群友"
        nick = self._nickname or "麦麦"
        speak_style = self.config.persona.speak_style or ""

        style_requirement = f"\n9. 表达风格: {speak_style}" if speak_style else ""

        # 根据模式获取对应的开场白模板（从配置读取）
        if source == "history":
            intro_template = self.config.prompt.history_intro
        elif source == "preset":
            intro_template = self.config.prompt.preset_intro
        else:  # knowledge
            intro_template = self.config.prompt.knowledge_intro

        intro = intro_template.format(nick=nick, persona=persona)

        if source == "history":
            history_text = await self._get_recent_history(session_id, topic_cfg)
            return f"""当前时间是 {time_str}.
{intro}
请参考以下最近的聊天记录:
{history_text}
要求:
1. 要像真正的朋友聊天一样自然, 不要像客服或助手
2. 语气随意, 接地气, 可以带一点网络用语和颜文字
3. 不要加任何前缀或解释, 直接发你要说的内容
4. 字数控制在 20-80 字之间, 简短有力
5. 不要每次都以"在吗", "你好"开头, 可以直接切入话题
6. 不要承认你是机器人, 若有人质疑你是机器人, 直接反击
7. 符合你的人设, 不要超出你的能力范围{style_requirement}"""

        elif source == "preset":
            preset_cfg = topic_cfg.preset
            topics = preset_cfg.topics
            weights = preset_cfg.topic_weights
            if not topics:
                return await self._build_prompt("knowledge", topic_cfg, now, target_id, session_id)
            if weights and len(weights) == len(topics):
                topic = random.choices(topics, weights=weights, k=1)[0]
            else:
                topic = random.choice(topics)

            free_hint = "你可以以这个主题为引子, 然后自由发挥, 聊相关的事情, 吐槽, 或者联想到的其他内容." if preset_cfg.allow_free_play else "请围绕这个主题展开, 不要偏离太远."

            return f"""当前时间是 {time_str}.
{intro}
今天你想聊的话题主题是: {topic}
请结合你的人设和兴趣, 围绕这个主题想一条消息发到聊天里. {free_hint}
要求:
1. 要像真正的朋友聊天一样自然, 不要像客服或助手
2. 语气随意, 接地气, 可以带一点网络用语和颜文字
3. 不要加任何前缀或解释, 直接发你要说的内容
4. 字数控制在 20-80 字之间, 简短有力
5. 不要每次都以"在吗", "你好"开头, 可以直接切入话题
6. 不要承认你是机器人, 若有人质疑你是机器人, 直接反击
7. 符合你的人设, 不要超出你的能力范围{style_requirement}"""

        else:  # knowledge / default
            return f"""当前时间是 {time_str}.
{intro}
请根据当前时间, 季节, 节日, 最近的热点, 或者你突然想到的一个有趣的事情, 发条消息到聊天里.
要求:
1. 要像真正的朋友聊天一样自然, 不要像客服或助手
2. 可以分享琐事, 吐槽, 提问, 或者突然想到的一个梗
3. 语气随意, 接地气, 可以带一点网络用语和颜文字
4. 不要加任何前缀或解释, 直接发你要说的内容
5. 字数控制在 20-80 字之间, 简短有力
6. 不要每次都以"在吗", "你好"开头, 可以直接切入话题
7. 不要承认你是机器人, 若有人质疑你是机器人, 直接反击
8. 符合你的人设, 不要超出你的能力范围{style_requirement}"""

    async def _get_recent_history(self, session_id: str, topic_cfg) -> str:
        recent_hours = topic_cfg.history.recent_hours
        recent_count = topic_cfg.history.recent_message_count
        end_ts = time.time()
        start_ts = end_ts - recent_hours * 3600

        try:
            raw = await self.ctx.message.get_by_time_in_chat(
                session_id,
                start_time=str(start_ts),
                end_time=str(end_ts),
                limit=recent_count,
                limit_mode="latest",
            )
        except Exception as e:
            self.ctx.logger.warning(f"获取历史消息失败: {e}")
            return "暂无历史聊天记录"

        raw = peel_envelope(raw)
        if not isinstance(raw, list) or not raw:
            return "暂无历史聊天记录"

        lines = []
        for msg in raw:
            if not isinstance(msg, dict):
                continue
            sender = self._get_sender_name(msg)
            text = self._get_msg_text(msg)
            t = self._get_msg_time_str(msg)
            if text:
                lines.append(f"[{t}] {sender}: {text}")
        lines.reverse()
        return "\n".join(lines)

    @staticmethod
    def _get_sender_name(msg: dict) -> str:
        info = msg.get("message_info") or {}
        user = info.get("user_info") or {}
        return str(user.get("user_nickname") or user.get("user_id") or "某人")

    @staticmethod
    def _get_msg_text(msg: dict) -> str:
        return str(msg.get("processed_plain_text") or "").strip()

    @staticmethod
    def _get_msg_time_str(msg: dict) -> str:
        ts = msg.get("timestamp", 0)
        try:
            t = datetime.fromtimestamp(float(ts))
            return t.strftime("%H:%M")
        except Exception:
            return "??:??"

    @staticmethod
    def _get_msg_user_id(msg: dict) -> str:
        info = msg.get("message_info") or {}
        user = info.get("user_info") or {}
        return str(user.get("user_id", "") or "")

    async def _call_llm(self, prompt: str, target_id: str) -> Optional[str]:
        """调用 LLM, 使用配置中指定的模型名称和最大 token."""
        try:
            result = await self.ctx.llm.generate(
                prompt=prompt,
                model=self.config.llm.model_name,
                temperature=0.8,
                max_tokens=self.config.llm.max_tokens,
            )
        except Exception as e:
            self.ctx.logger.error(f"[{target_id}] LLM 调用异常: {e}", exc_info=True)
            return None

        result = peel_envelope(result)
        if isinstance(result, dict) and result.get("success"):
            return str(result.get("response", "")).strip()

        self.ctx.logger.error(f"[{target_id}] LLM 调用失败: {result}")
        return None

    # ========== 手动命令 ==========

    @Command("lonelymai_trigger", description="手动触发一次主动发言", pattern=r"^/lonelymai$")
    async def cmd_trigger(self, stream_id: str = "", **kwargs):
        if not stream_id:
            return False, "无法获取当前会话 ID", True

        target = None
        for tid, st in self._states.items():
            if st.stream_id == stream_id:
                target = tid
                break
        if not target:
            return False, "当前会话未在白名单中", True

        success = await self._do_proactive_chat(self._states[target], target)
        if success:
            return True, "已触发主动发言", True
        else:
            return False, "主动发言失败（LLM 错误或发送失败）", True


def create_plugin():
    return LonelyMaiPlugin()