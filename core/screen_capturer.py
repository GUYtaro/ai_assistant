# core/screen_capturer.py
# -------------------------
# จับภาพหน้าจอ + แปลงเป็น base64
# ใช้ร่วมกับ ScreenReader (OCR) และ VisionSystem (LLM Multimodal)
# -------------------------

import io
import base64
import mss
from PIL import Image

def screenshot_pil(region=None, monitor=0, resize_to=None, fmt="PNG"):
    """
    ถ่าย screenshot แล้วคืนค่าเป็น PIL.Image
    - region: (left, top, width, height) หรือ None -> จับเต็มหน้าจอ
    - monitor: เลือกจอ (0 = all monitors, 1 = จอหลัก, 2+ = จออื่นๆ)
    - resize_to: (w, h) ถ้าต้องการย่อภาพ
    - fmt: "PNG" หรือ "JPEG"
    """
    with mss.mss() as sct:
        # เลือก monitor
        if monitor == 0:
            mon = sct.monitors[0]   # all monitors
        else:
            mon = sct.monitors[monitor]

        # ถ้ามี region ก็ตัดเฉพาะส่วนนั้น
        if region:
            left, top, width, height = region
            mon = {"left": left, "top": top, "width": width, "height": height}

        sct_img = sct.grab(mon)
        img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

    # resize ถ้าระบุ
    if resize_to:
        img = img.resize(resize_to, Image.LANCZOS)

    return img


def image_to_data_uri(img: Image.Image, fmt="JPEG", quality=80):
    """
    แปลง PIL.Image เป็น Data URI (base64)
    - fmt: 'JPEG' หรือ 'PNG'
    - quality: ใช้เมื่อ JPEG (0-100)
    คืนค่า -> (data_uri, raw_bytes)
    """
    buf = io.BytesIO()
    if fmt.upper() == "JPEG":
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        mime = "image/jpeg"
    else:
        img.save(buf, format="PNG", optimize=True)
        mime = "image/png"

    raw_bytes = buf.getvalue()
    b64 = base64.b64encode(raw_bytes).decode("ascii")
    data_uri = f"data:{mime};base64,{b64}"
    return data_uri, raw_bytes


def screenshot_data_uri(region=None, monitor=0, resize_to=(1024, 768), fmt="JPEG", quality=80):
    """
    จับภาพหน้าจอ -> แปลงเป็น Data URI + raw bytes
    - resize_to = (1024,768) เพื่อลด payload ก่อนส่งไป LLM
    คืนค่า -> (data_uri, raw_bytes, PIL.Image)
    """
    img = screenshot_pil(region=region, monitor=monitor, resize_to=resize_to, fmt=fmt)
    data_uri, raw_bytes = image_to_data_uri(img, fmt=fmt, quality=quality)
    return data_uri, raw_bytes, img


# ✅ ทดสอบ standalone
if __name__ == "__main__":
    print("📸 กำลังจับภาพหน้าจอ...")
    img = screenshot_pil()
    print(f"ขนาดภาพ: {img.size}")
    img.show()

    data_uri, raw, _ = screenshot_data_uri()
    print(f"Data URI ตัวอย่าง (50 ตัวแรก): {data_uri[:50]}...")
