import os
import wave
import json
import logging
from vosk import Model, KaldiRecognizer

# 配置日志
logger = logging.getLogger(__name__)

class SpeechService:
    def __init__(self):
        # 在初始化时就加载模型
        model_path = '/app/models/vosk-model-en-us-0.42-gigaspeech'
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Vosk model not found at {model_path}")
        
        # 预加载模型
        self.model = Model(model_path)
        logger.info("Vosk model loaded successfully")
    
    def recognize(self, audio_path):
        """
        使用Vosk模型识别音频文件
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            str: 识别出的文本
        """
        # 读取音频文件
        wf = wave.open(audio_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            raise ValueError("Audio file must be WAV format mono PCM.")
        
        # 创建识别器
        rec = KaldiRecognizer(self.model, wf.getframerate())
        rec.SetWords(True)
        
        # 识别音频
        result = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                part = json.loads(rec.Result())
                if part.get("text"):
                    result.append(part["text"])
        
        # 获取最后一部分结果
        final = json.loads(rec.FinalResult())
        if final.get("text"):
            result.append(final["text"])
        
        # 合并所有识别结果
        return " ".join(result)

# 创建全局实例
speech_service = SpeechService() 