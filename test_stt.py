from core.stt_client import STTClient

stt = STTClient(model_size="tiny", language="th")
text = stt.listen_once(duration=5)
print("คุณพูดว่า:", text)
