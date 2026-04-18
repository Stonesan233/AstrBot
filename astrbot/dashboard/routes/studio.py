import asyncio
import traceback

from quart import jsonify, request

from astrbot.core import logger
from astrbot.core.core_lifecycle import AstrBotCoreLifecycle

from .route import Response, Route, RouteContext


class _DashboardEvent:
    """轻量级 event stub，用于从 Dashboard 触发 studio chat。

    提供 _internal_delegate 所需的最小接口：
    - unified_msg_origin / sender_id  → 用于 session_id 生成
    - send()                         → 中间进度推送（dashboard 用轮询，此处 no-op）
    """
    def __init__(self, message_str: str = ""):
        self.unified_msg_origin = "dashboard"
        self.sender_id = "dashboard_user"
        self.message_str = message_str

    async def send(self, msg: str):
        pass  # Dashboard 通过轮询 /history 获取实时更新

    def plain_result(self, text: str):
        return text


class StudioRoute(Route):
    """Studio 工作室 Dashboard API 路由

    暴露 Studio 插件内部状态供前端 StudioPage.vue 调用。
    """

    def __init__(
        self,
        context: RouteContext,
        core_lifecycle: AstrBotCoreLifecycle,
    ) -> None:
        super().__init__(context)
        self.core_lifecycle = core_lifecycle
        self.routes = [
            ("/studio/status", ("GET", self.get_status)),
            ("/studio/history", ("GET", self.get_history)),
            ("/studio/chat", ("POST", self.send_chat)),
            ("/studio/member", ("POST", self.add_member)),
            ("/studio/member", ("DELETE", self.remove_member)),
            ("/studio/reset", ("POST", self.reset_conversation)),
        ]
        self.register_routes()

    # ------------------------------------------------------------------
    # Helper: locate the loaded StudioPlugin instance
    # ------------------------------------------------------------------

    def _find_studio_plugin(self):
        """从 core_lifecycle.star_context 的已注册插件中查找 StudioPlugin 实例"""
        try:
            ctx = getattr(self.core_lifecycle, "star_context", None)
            if ctx is None:
                return None
            for star in ctx.get_all_stars():
                if star.name and "studio" in star.name.lower():
                    plugin = star.star_cls
                    if plugin is not None:
                        return plugin
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # GET /api/studio/status
    # ------------------------------------------------------------------

    async def get_status(self):
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(
                    Response().ok(data={
                        "engine_ok": False,
                        "members": {},
                        "active_count": 0,
                        "total_count": 0,
                        "member_count": 0,
                        "auto_delegate": False,
                        "auto_stop": False,
                        "max_rounds": 10,
                        "persist_members": False,
                        "auto_review": False,
                    }).__dict__
                )

            config = getattr(plugin, "config", {}) or {}
            members = getattr(plugin, "studio_members", {})
            conversations = getattr(plugin, "conversations", {})
            executor_ok = getattr(plugin, "_executor", None) is not None

            active_count = sum(
                1 for c in conversations.values()
                if c.get("status") == "active"
            )

            data = {
                "engine_ok": executor_ok,
                "members": {
                    name: {
                        "name": info.get("name", name),
                        "emoji": info.get("emoji", "🤖"),
                        "persona_prompt": info.get("persona_prompt", ""),
                        "created_at": info.get("created_at", 0),
                    }
                    for name, info in members.items()
                },
                "active_count": active_count,
                "total_count": len(conversations),
                "member_count": len(members),
                "auto_delegate": bool(config.get("auto_delegate", True)),
                "auto_stop": bool(config.get("auto_stop_on_complete", True)),
                "max_rounds": config.get("max_internal_turns", 10),
                "persist_members": bool(config.get("persist_members", True)),
                "auto_review": bool(config.get("auto_review", False)),
            }
            return jsonify(Response().ok(data=data).__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"获取 Studio 状态失败: {e!s}").__dict__)

    # ------------------------------------------------------------------
    # GET /api/studio/history
    # ------------------------------------------------------------------

    async def get_history(self):
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(Response().ok(data={}).__dict__)

            conversations = getattr(plugin, "conversations", {})
            support_all = request.args.get("support_all_history", "false").lower() == "true"

            # 序列化所有会话
            history = {}
            all_turns = []
            active_task_id = ""
            active_session_status = "idle"

            for sid, conv in conversations.items():
                turns = []
                for t in conv.get("turns", []):
                    turn_data = {
                        "task_id": t.get("task_id", ""),
                        "from_member": t.get("from_member", ""),
                        "to_member": t.get("to_member", ""),
                        "message": t.get("message", ""),
                        "response": t.get("response", ""),
                        "delegated_to": t.get("delegated_to"),
                        "auto_delegated": bool(t.get("auto_delegated", False)),
                        "timestamp": t.get("timestamp", 0),
                    }
                    turns.append(turn_data)
                    if support_all:
                        all_turns.append({**turn_data, "session_id": sid})

                history[sid] = {
                    "id": conv.get("id", sid),
                    "turns": turns,
                    "initial_member": conv.get("initial_member"),
                    "status": conv.get("status", "idle"),
                    "max_rounds": conv.get("max_rounds", 10),
                    "created_at": conv.get("created_at", 0),
                    "updated_at": conv.get("updated_at", 0),
                    "last_modified_by": conv.get("last_modified_by"),
                    "last_review_by": conv.get("last_review_by"),
                    "last_action_type": conv.get("last_action_type"),
                    "auto_delegate_count": conv.get("auto_delegate_count", 0),
                    "current_task_id": conv.get("current_task_id", ""),
                }

                if conv.get("status") == "active":
                    active_task_id = conv.get("current_task_id", "")
                    active_session_status = "active"

            result_data = history
            if support_all:
                all_turns.sort(key=lambda x: x.get("timestamp", 0))
                result_data = {
                    "conversations": history,
                    "all_turns": all_turns,
                    "active_task_id": active_task_id,
                    "active_session_status": active_session_status,
                }

            return jsonify(Response().ok(data=result_data).__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"获取 Studio 历史失败: {e!s}").__dict__)

    # ------------------------------------------------------------------
    # POST /api/studio/chat
    # ------------------------------------------------------------------

    async def send_chat(self):
        """接收前端消息，在后台启动 studio 协作，立即返回。
        前端通过轮询 /studio/history 观察实时进度。
        """
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(Response().error("Studio 插件未加载").__dict__)

            data = await request.json
            if not isinstance(data, dict):
                return jsonify(Response().error("请求必须为 JSON 对象").__dict__)

            message = (data.get("message") or "").strip()
            if not message:
                return jsonify(Response().error("消息不能为空").__dict__)

            # 检查是否有正在进行的协作
            conversations = getattr(plugin, "conversations", {})
            for conv in conversations.values():
                if conv.get("status") == "active":
                    return jsonify(
                        Response().error("已有协作正在进行中，请等待完成或重置后再试").__dict__
                    )

            # 创建 mock event 并在后台启动协作
            mock_event = _DashboardEvent(message_str=f"/studio chat {message}")

            async def _run():
                try:
                    result = await plugin._handle_chat(mock_event, message)
                    logger.info(f"[StudioRoute] chat completed: {result[:100]}")
                except Exception as exc:
                    logger.error(f"[StudioRoute] chat error: {exc}\n{traceback.format_exc()}")
                    # 确保会话状态不会卡在 active
                    for conv in getattr(plugin, "conversations", {}).values():
                        if conv.get("status") == "active":
                            conv["status"] = "error"

            asyncio.ensure_future(_run())

            return jsonify(Response().ok(message="协作已启动，请观察协作记录").__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"发送消息失败: {e!s}").__dict__)

    # ------------------------------------------------------------------
    # POST /api/studio/member
    # ------------------------------------------------------------------

    async def add_member(self):
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(Response().error("Studio 插件未加载").__dict__)

            data = await request.json
            if not isinstance(data, dict):
                return jsonify(Response().error("请求必须为 JSON 对象").__dict__)

            name = (data.get("name") or "").strip()
            persona = (data.get("persona_prompt") or "").strip()
            if not name:
                return jsonify(Response().error("成员名称不能为空").__dict__)
            if not persona:
                return jsonify(Response().error("人格提示词不能为空").__dict__)

            result = plugin._handle_add(f"{name} {persona}")
            if "已添加" in result:
                return jsonify(Response().ok(message=result).__dict__)
            else:
                return jsonify(Response().error(result).__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"添加成员失败: {e!s}").__dict__)

    # ------------------------------------------------------------------
    # DELETE /api/studio/member
    # ------------------------------------------------------------------

    async def remove_member(self):
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(Response().error("Studio 插件未加载").__dict__)

            data = await request.json
            if not isinstance(data, dict):
                return jsonify(Response().error("请求必须为 JSON 对象").__dict__)

            name = (data.get("name") or "").strip()
            if not name:
                return jsonify(Response().error("成员名称不能为空").__dict__)

            result = plugin._handle_remove(name)
            if "已移除" in result:
                return jsonify(Response().ok(message=result).__dict__)
            else:
                return jsonify(Response().error(result).__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"移除成员失败: {e!s}").__dict__)

    # ------------------------------------------------------------------
    # POST /api/studio/reset
    # ------------------------------------------------------------------

    async def reset_conversation(self):
        try:
            plugin = self._find_studio_plugin()
            if plugin is None:
                return jsonify(Response().error("Studio 插件未加载").__dict__)

            conversations = getattr(plugin, "conversations", {})
            # 清空所有会话
            conversations.clear()
            return jsonify(Response().ok(message="协作已重置").__dict__)
        except Exception as e:
            logger.error(traceback.format_exc())
            return jsonify(Response().error(f"重置协作失败: {e!s}").__dict__)
