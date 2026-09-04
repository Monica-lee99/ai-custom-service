import json
import os
import inspect
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from scene_service import (
    ValidationError,
    assert_value,
    build_proxy_body,
    build_scenes_response,
    load_scenes,
)
from volcengine_signer import sign_headers


SERVER_DIR = Path(__file__).resolve().parent
DEFAULT_SCENES_DIR = SERVER_DIR / "scenes"
RTC_HOST = "rtc.volcengineapi.com"

load_dotenv(SERVER_DIR / ".env")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["content-type"],
)

SCENES = load_scenes(Path(os.environ.get("SCENES_DIR", DEFAULT_SCENES_DIR)))


class ProxyRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    SceneID: str | None = None


def make_error_response(action, exc):
    return {
        "ResponseMetadata": {
            "Action": action,
            "Error": {"Code": -1, "Message": str(exc)},
        }
    }


def make_success_response(action, result):
    return {"ResponseMetadata": {"Action": action}, "Result": result}


async def post_json(url, headers, body, params):
    payload = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            params=params,
            headers=headers,
            content=payload,
        )
        return response.json()


async def read_json_body(http_request):
    body = await http_request.body()
    if not body:
        return {}
    return json.loads(body.decode("utf-8"))


async def wrapped_response(api_name, http_request, logic, contain_response_metadata=True):
    try:
        body = await read_json_body(http_request)
        result = logic(body)
        if inspect.isawaitable(result):
            result = await result
        if contain_response_metadata:
            return make_success_response(api_name, result)
        return result
    except Exception as exc:
        return make_error_response(api_name, exc)


@app.post("/getScenes")
async def get_scenes(http_request: Request):
    return await wrapped_response(
        "getScenes",
        http_request,
        lambda _body: build_scenes_response(SCENES),
    )


@app.post("/proxy")
async def proxy_open_api(http_request: Request):
    query = http_request.query_params
    action = query.get("Action", "")

    async def logic(body):
        version = query.get("Version", "2024-12-01")
        assert_value(action, "Action 不能为空")
        assert_value(version, "Version 不能为空")

        proxy_request = ProxyRequest.model_validate(body)
        scene_id = proxy_request.SceneID
        assert_value(scene_id, "SceneID 不能为空, SceneID 用于指定场景的 JSON")

        scene_data = SCENES.get(scene_id)
        assert_value(scene_data, f"{scene_id} 不存在, 请先在 server-python/scenes 下定义该场景的 JSON.")

        account_config = scene_data.get("AccountConfig", {})
        assert_value(account_config.get("accessKeyId"), "AccountConfig.accessKeyId 不能为空")
        assert_value(account_config.get("secretKey"), "AccountConfig.secretKey 不能为空")

        proxy_body = build_proxy_body(action, scene_data)
        payload = json.dumps(proxy_body, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        query_params = {"Action": action, "Version": version}
        headers = {
            "Host": RTC_HOST,
            "Content-Type": "application/json",
        }
        signed_headers = sign_headers(
            account_config["accessKeyId"],
            account_config["secretKey"],
            "POST",
            "/",
            query_params,
            headers,
            payload,
        )
        return await post_json(f"https://{RTC_HOST}", signed_headers, proxy_body, query_params)

    return await wrapped_response(
        "proxy",
        http_request,
        logic,
        contain_response_metadata=False,
    )


@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def not_found(path_name):
    return JSONResponse(
        status_code=404,
        content=make_error_response("unknown", ValidationError("API 不存在")),
    )


def main():
    port = int(os.environ.get("PORT", "3001"))
    print(f"AIGC Python FastAPI Server is running at http://localhost:{port}")
    uvicorn.run(app, host="localhost", port=port)


if __name__ == "__main__":
    main()
