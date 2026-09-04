import json
import time
import uuid
from copy import deepcopy
from pathlib import Path

from rtc_token import AccessToken, Privileges


class ValidationError(Exception):
    def __str__(self):
        return f"Error: {self.args[0]}"


def assert_value(value, message):
    invalid = value is None or value is False or value == "" or value == 0
    if isinstance(value, str) and " " in value:
        invalid = True
    if invalid:
        raise ValidationError(message)


def load_scenes(directory):
    scenes = {}
    scene_dir = Path(directory)
    for path in sorted(scene_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            scenes[path.stem] = json.load(file)
    return scenes


def nested_get(data, path):
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def build_scenes_response(
    scenes,
    uuid_factory=None,
    now_fn=None,
    nonce_factory=None,
):
    uuid_factory = uuid_factory or (lambda: str(uuid.uuid4()))
    now_fn = now_fn or (lambda: int(time.time()))
    nonce_factory = nonce_factory or (lambda: None)

    result = []
    for scene_id, scene_data in scenes.items():
        scene_config = scene_data.setdefault("SceneConfig", {})
        rtc_config = scene_data.setdefault("RTCConfig", {})
        voice_chat = scene_data.setdefault("VoiceChat", {})

        app_id = rtc_config.get("AppId")
        room_id = rtc_config.get("RoomId")
        user_id = rtc_config.get("UserId")
        app_key = rtc_config.get("AppKey")
        token = rtc_config.get("Token")

        assert_value(app_id, f"{scene_id} 场景的 RTCConfig.AppId 不能为空")

        if app_id and (not token or not user_id or not room_id):
            room_id = room_id or uuid_factory()
            user_id = user_id or uuid_factory()

            rtc_config["RoomId"] = room_id
            rtc_config["UserId"] = user_id
            voice_chat["RoomId"] = room_id

            agent_config = voice_chat.setdefault("AgentConfig", {})
            target_user_ids = agent_config.setdefault("TargetUserId", [""])
            if not target_user_ids:
                target_user_ids.append("")
            target_user_ids[0] = user_id

            assert_value(app_key, f"自动生成 Token 时, {scene_id} 场景的 AppKey 不可为空")

            access_token = AccessToken(
                app_id,
                app_key,
                room_id,
                user_id,
                nonce=nonce_factory(),
                issued_at=now_fn(),
            )
            access_token.add_privilege(Privileges.PRIV_SUBSCRIBE_STREAM, 0)
            access_token.add_privilege(Privileges.PRIV_PUBLISH_STREAM, 0)
            access_token.expire_time(now_fn() + 24 * 3600)
            rtc_config["Token"] = access_token.serialize()

        scene_for_response = deepcopy(scene_config)
        scene_for_response["id"] = scene_id
        scene_for_response["botName"] = nested_get(voice_chat, ["AgentConfig", "UserId"])
        scene_for_response["isInterruptMode"] = (
            nested_get(voice_chat, ["Config", "InterruptMode"]) == 0
        )

        optional_fields = {
            "isVision": nested_get(
                voice_chat, ["Config", "LLMConfig", "VisionConfig", "Enable"]
            ),
            "isScreenMode": (
                nested_get(
                    voice_chat,
                    ["Config", "LLMConfig", "VisionConfig", "SnapshotConfig", "StreamType"],
                )
                == 1
                if nested_get(
                    voice_chat,
                    ["Config", "LLMConfig", "VisionConfig", "SnapshotConfig", "StreamType"],
                )
                is not None
                else None
            ),
            "isAvatarScene": nested_get(
                voice_chat, ["Config", "AvatarConfig", "Enabled"]
            ),
            "avatarBgUrl": nested_get(
                voice_chat, ["Config", "AvatarConfig", "BackgroundUrl"]
            ),
        }
        for key, value in optional_fields.items():
            if value is not None:
                scene_for_response[key] = value

        rtc_for_response = deepcopy(rtc_config)
        rtc_for_response.pop("AppKey", None)
        result.append({"scene": scene_for_response, "rtc": rtc_for_response})

    return {"scenes": result}


def build_proxy_body(action, scene_data):
    voice_chat = scene_data.get("VoiceChat", {})
    if action == "StartVoiceChat":
        return voice_chat
    if action == "StopVoiceChat":
        app_id = voice_chat.get("AppId")
        room_id = voice_chat.get("RoomId")
        task_id = voice_chat.get("TaskId")
        assert_value(app_id, "VoiceChat.AppId 不能为空")
        assert_value(room_id, "VoiceChat.RoomId 不能为空")
        assert_value(task_id, "VoiceChat.TaskId 不能为空")
        return {"AppId": app_id, "RoomId": room_id, "TaskId": task_id}
    return {}
