# Python Server

这个目录是 `Server` Node 服务的 Python 等价版本，默认监听 `http://localhost:3001`。

## 启动

```powershell
cd D:\AiStudy\ai-custom-service
pip install -r server-python\requirements.txt
python server-python\app.py
```

服务默认读取 `server-python/scenes/*.json`，所以 Python 服务可以维护独立的场景配置。现有前端配置不需要改，`src/config/index.ts` 仍然可以继续使用：

```ts
export const AIGC_PROXY_HOST = 'http://localhost:3001';
```

## 接口

- `POST /getScenes?Action=getScenes`
- `POST /proxy?Action=StartVoiceChat`
- `POST /proxy?Action=StopVoiceChat`

返回结构和 Node 版保持一致。`/getScenes` 会在缺少 `RoomId`、`UserId` 或 `Token` 时自动生成 RTC Token，并且不会把 `RTCConfig.AppKey` 返回给前端。

## 可选配置

可以在 `server-python/.env` 中配置：

```env
PORT=3001
SCENES_DIR=D:\AiStudy\ai-custom-service\server-python\scenes
```

也可以用 PowerShell 环境变量覆盖：

```powershell
$env:PORT = "3001"
$env:SCENES_DIR = "D:\AiStudy\ai-custom-service\server-python\scenes"
python server-python\app.py
```

也可以用 uvicorn 方式启动：

```powershell
cd D:\AiStudy\ai-custom-service\server-python
uvicorn app:app --host localhost --port 3001
```
