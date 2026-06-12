import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # 数据库
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sql_app.db")

    # DeepSeek
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "sk-YOUR_DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Kimi (Moonshot)
    KIMI_API_KEY: str = os.getenv("KIMI_API_KEY", "sk-YOUR_KIMI_API_KEY")
    KIMI_BASE_URL: str = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    KIMI_MODEL: str = os.getenv("KIMI_MODEL", "moonshot-v1-8k")

    # 豆包 (Doubao / 火山引擎)
    DOUBAO_API_KEY: str = os.getenv("DOUBAO_API_KEY", "sk-YOUR_DOUBAO_API_KEY")
    DOUBAO_BASE_URL: str = os.getenv("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
    DOUBAO_MODEL: str = os.getenv("DOUBAO_MODEL", "doubao-pro-32k")

    # 淘宝/电商 API（可选）
    TAOBAO_API_KEY: str = os.getenv("TAOBAO_API_KEY", "")

    # 高德地图 API（可选）
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    # 服务器配置
    SERVER_HOST: str = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "5000"))


settings = Settings()
