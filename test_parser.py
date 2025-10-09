from core.command_parser import CommandParser

parser = CommandParser()

# ทดสอบ
ok, result = parser.parse("คลิกปุ่ม File")
print(f"OK: {ok}")
print(f"Result: {result}")