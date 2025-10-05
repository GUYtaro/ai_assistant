# core/vision_system.py
# -------------------------
# VisionSystem = รวมพลัง Screenshot + LLM Vision
# ใช้สำหรับถามคำถามที่เกี่ยวกับภาพหน้าจอโดยตรง
# -------------------------

from core.screen_capturer import screenshot_data_uri
from core.llm_client import LLMClient


class VisionSystem:
    def __init__(self, llm: LLMClient = None):
        # ถ้าไม่ได้ส่ง LLMClient เข้ามา จะสร้างใหม่อัตโนมัติ
        self.llm = llm or LLMClient()

    def ask_with_screenshot(self, user_prompt, region=None, resize_to=(1024, 768)):
        """
        📸 ถ่ายภาพหน้าจอ -> แปลงเป็น base64 (Data URI) -> ส่งเข้า LLM
        - user_prompt: คำถามที่ผู้ใช้ต้องการให้ AI วิเคราะห์
        - region: (left, top, width, height) ถ้าไม่ระบุ = ทั้งจอ
        - resize_to: ขนาดย่อเพื่อประหยัดเวลาและ bandwidth
        """
        try:
            data_uri, raw, img = screenshot_data_uri(region=region, resize_to=resize_to)
            reply = self.llm.ask_with_image(user_prompt, data_uri)
            return reply
        except Exception as e:
            return f"[VISION ERROR] เกิดปัญหาในการประมวลผล: {e}"

    def analyze(self, user_prompt: str = "อธิบายสิ่งที่เห็นบนหน้าจอ", region=None):
        """
        🔍 ฟังก์ชัน wrapper เพื่อให้เรียกสั้น ๆ จาก assistant/main.py
        ใช้สำหรับให้โมเดลวิเคราะห์ภาพหน้าจอแบบอัตโนมัติ
        """
        return self.ask_with_screenshot(user_prompt, region)
