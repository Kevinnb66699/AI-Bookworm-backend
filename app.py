import os
import requests
import zipfile
from app import create_app, db
import logging

# 自动下载 vosk 语音识别模型
MODEL_DIR = "backend/models/vosk-model-en-us-0.42-gigaspeech"
MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip"
ZIP_PATH = "backend/models/vosk-model-en-us-0.42-gigaspeech.zip"

def download_model():
    if not os.path.exists(MODEL_DIR):
        print("模型不存在，正在下载...")
        os.makedirs("backend/models", exist_ok=True)
        with requests.get(MODEL_URL, stream=True) as r:
            r.raise_for_status()
            with open(ZIP_PATH, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        # 解压
        with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
            zip_ref.extractall("backend/models")
        os.remove(ZIP_PATH)
        print("模型下载并解压完成！")
    else:
        print("模型已存在，无需下载。")

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

download_model()

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            # 确保所有表存在
            logger.info("正在创建数据库表...")
            db.create_all()
            logger.info("数据库表创建成功！")
            
            # 检查连接
            logger.info("正在检查数据库连接...")
            db.session.execute("SELECT 1")
            logger.info("数据库连接正常！")
            
        except Exception as e:
            logger.error(f"数据库初始化错误: {str(e)}")
            db.session.rollback()
    
    # 启用调试模式以显示详细错误信息
    app.config['DEBUG'] = True
    logger.info("正在启动 Flask 服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True) 