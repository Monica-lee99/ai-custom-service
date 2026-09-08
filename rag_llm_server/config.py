import os
from pathlib import Path
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
load_dotenv(SERVER_DIR / ".env")
load_dotenv()

class Config:
    VOLC_AK = os.getenv("VOLC_ACCESS_KEY")
    VOLC_SK = os.getenv("VOLC_SECRET_KEY")
    ARK_ENDPOINT_ID = os.getenv("ARK_ENDPOINT_ID")
    ARK_API_KEY = os.getenv("ARK_API_KEY")

    RTC_APP_ID = os.getenv("RTC_APP_ID")
    RTC_APP_KEY = os.getenv("RTC_APP_KEY")
    RTC_ROOM_ID = os.getenv("RTC_ROOM_ID", "ChatRoom01")
    RTC_USER_ID = os.getenv("RTC_USER_ID", "Huoshan01")
    RTC_TASK_ID = os.getenv("RTC_TASK_ID", "ChatTask01")
    AGENT_USER_ID = os.getenv("AGENT_USER_ID", "AiAgent")
    ASR_APP_ID = os.getenv("ASR_APP_ID", "")
    TTS_APP_ID = os.getenv("TTS_APP_ID", "")
    
    SERVER_URL = os.getenv("SERVER_URL", "")

settings = Config()
