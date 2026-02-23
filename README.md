# Multi-Emulator Bot

บอทอัตโนมัติสำหรับควบคุม Android Emulator หลายตัวพร้อมกัน ผ่าน ADB โดยใช้ OCR ในการอ่านหน้าจอและตัดสินใจ workflow ต่าง ๆ

## Features

- รองรับ Emulator หลายตัวพร้อมกัน (Multi-threading)
- ใช้ TesseractOCR ในการอ่านข้อความบนหน้าจอ
- มี Workflow หลายรูปแบบ:
  - **Reid Char** — ค้นหาและ reid ตัวละครที่ต้องการ
  - **Reid Gear** — ค้นหาและ reid อุปกรณ์ที่ต้องการ
  - **Auto Login** — ล็อกอินอัตโนมัติ
  - **Test** — ทดสอบการทำงาน

## Requirements

- Python 3.x
- ADB (Android Debug Bridge)
- TesseractOCR
- Android Emulator (เช่น LDPlayer, BlueStacks)

## Installation

1. Clone repo นี้
2. สร้าง virtual environment และติดตั้ง dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. ตั้งค่า `config.ini` ตามตัวละครและ gear ที่ต้องการ

## Usage

รันบอทด้วยคำสั่ง:
```bash
python app.py
```

## Configuration

แก้ไขไฟล์ `config.ini` เพื่อกำหนดเงื่อนไขการค้นหา:

```ini
[herowant]
name1=First+Emperor=UltraQinShi   # ต้องมีคำว่า "First" AND "Emperor"
name5=Qin+Shi-Sally=QinShi        # ต้องมี "Qin Shi" แต่ห้ามมี "Sally"

[gearwant]
gear1=Leonard+Headphones=LH
```

**รูปแบบ:** `keyword1+keyword2-keyword3=OutputName`
- `+` = ต้องมีคำนี้ (AND)
- `-` = ห้ามมีคำนี้ (NOT)
- `=` = ชื่อที่ใช้บันทึกไฟล์

## Project Structure

```
bot/
├── app.py          # Main entry point
├── utils.py        # Utility functions
├── config.ini      # Hero/Gear configuration
├── workflow/       # Workflow modules
│   ├── workflow_reid_char.py
│   ├── workflow_reid_gear.py
│   ├── workflow_autologin.py
│   └── workflow_test.py
└── tools/          # ADB binaries
```
