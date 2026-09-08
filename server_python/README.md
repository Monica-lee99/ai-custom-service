# Python FastAPI 代理

此目录是上传 Demo 的 Python 版 RTC OpenAPI 代理，默认监听 `http://localhost:3001`。

## 启动

```powershell
cd D:\AiStudy\ai-custom-service
python -m pip install -r server_python\requirements.txt
python server_python\main.py
```

## 场景配置

复制 `scenes/template.json` 为 `scenes/Custom.json`，填写：

- `AccountConfig.accessKeyId` / `secretKey`：火山引擎 AK/SK。
- `RTCConfig.AppId` / `AppKey`：RTC 应用配置。
- `VoiceChat`：ASR、TTS、LLM 和 Agent 配置。

`Custom.json` 不提交到 Git；`template.json` 会保留并提交。
