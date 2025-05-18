import pytesseract
from PIL import Image
import io

class OCRService:
    def __init__(self):
        # 设置Tesseract路径（Windows系统）
        pytesseract.pytesseract.tesseract_cmd = r'D:\Tesseract OCR\tesseract.exe'

    def recognize_text(self, image_data):
        try:
            # 如果是文件对象
            if hasattr(image_data, 'read'):
                image = Image.open(image_data)
            # 如果是字节数据
            elif isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                raise ValueError("不支持的图片格式")

            # 进行文字识别
            # 使用中文和英文语言包
            text = pytesseract.image_to_string(image, lang='chi_sim+eng')
            
            # 清理识别结果
            text = text.strip()
            
            if not text:
                raise Exception("未能识别出文字")
                
            return text
        except Exception as e:
            raise Exception(f"文字识别失败: {str(e)}")

ocr_service = OCRService() 