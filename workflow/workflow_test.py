import os
import subprocess
import threading
import shutil
from utils import (
    find_img_and_click,
    load_img,
    click,
    swipe,
    delay,
    while_with_timeout
)

# ตัวแปร global สำหรับจัดการไฟล์ (shared across threads)
used_file_indices = set()
file_lock = threading.Lock()  # 🔒 Lock สำหรับป้องกัน race condition

# ตัวแปรเก็บสถานะว่า device ไหนทำ setup ไปแล้วบ้าง
device_setup_status = {}  # {device_serial: True/False}
status_lock = threading.Lock()

def workflow_test(device, thread_id, showdb=False, first_run=None, mode=1):
    """
    Workflow: Test (Thread-safe version with Auto first_run detection)
    ขั้นตอน: force-stop -> ลบ prefs -> push ไฟล์ใหม่ -> เปิดเกม -> pull ไฟล์

    Args:
        device: ADB device object
        thread_id: ID ของ thread
        showdb: แสดง debug หรือไม่
        first_run: None = ตรวจสอบอัตโนมัติ, True = บังคับทำ setup, False = บังคับข้าม setup
        mode: โหมดการทำงาน (1=normal test, 2=test+7days, 3=test+event, 4=test+7days+event)

    Returns:
        dict: ผลลัพธ์การทำงาน {'success': bool, 'message': str, ...}
    """
    # =============================================
    # ตัวอย่างการใช้ mode:
    # if mode == 1:
    #     # normal test - test ปกติ
    # if mode == 2:
    #     # test + 7days - test แล้วรับ 7days reward
    # if mode == 3:
    #     # test + event - test แล้วไป event shop
    # if mode == 4:
    #     # test + 7days + event - test แล้วทำทั้งสองอย่าง
    # if mode == 1 or mode == 2:
    #     # ทำงานเฉพาะ mode 1 และ 2
    # if mode in [2, 4]:
    #     # ทำงานเฉพาะ mode ที่ต้องรับ 7days
    # if mode in [3, 4]:
    #     # ทำงานเฉพาะ mode ที่ต้องไป event shop
    # =============================================
    try:
        global used_file_indices, device_setup_status
        
        device_serial = device.serial
        
        # ตรวจสอบว่าเป็นรอบแรกหรือไม่ (อัตโนมัติ)
        if first_run is None:
            with status_lock:
                if device_serial not in device_setup_status:
                    # ยังไม่เคย setup -> เป็นรอบแรก
                    device_setup_status[device_serial] = True
                    first_run = True
                else:
                    # setup ไปแล้ว -> ไม่ใช่รอบแรก
                    first_run = False
        
        print(f"[Thread {thread_id} - {device_serial}] ⚙️ Mode: {mode}")
        if first_run:
            print(f"[Thread {thread_id} - {device_serial}] 🚀 เริ่ม Workflow: Test (รอบแรก - มี Setup)")
        else:
            print(f"[Thread {thread_id} - {device_serial}] 🔄 เริ่ม Workflow: Test (รอบถัดไป - ข้าม Setup)")

        # ============================================================
        # SETUP SECTION - ทำเฉพาะครั้งแรก (first_run=True)
        # ============================================================
        file_to_push = None
        
        if first_run:
            print(f"[Thread {thread_id}] First run")
            command = [
                r'tools\adb.exe',
                '-s', device_serial,
                'shell',
                'am',
                'force-stop',
                'com.linecorp.LGRGS'
            ]
            res = subprocess.run(command, capture_output=True, text=True)
            
            if res.returncode != 0:
                print(f"[Thread {thread_id}] ⚠️ Force stop: {res.stderr}")

            command = [
                r'tools\adb.exe',
                '-s', device_serial,
                'shell',
                'rm',
                '-f',
                '/data/data/com.linecorp.LGRGS/shared_prefs/*'
            ]
            res = subprocess.run(command, capture_output=True, text=True)

            find_img_and_click(device=device, pic_local='image/icongame.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=10, mode_pic=1, mode_click=1, resize=1, lv_click=1)
            find_img_and_click(device=device, pic_local='image/login_0.png', threshold_set=0.7, showimg=False, modecoler=False, showdb=False, timeout=60, mode_pic=1, mode_click=1, resize=1, region=None, lv_click=1, loop_image_delay=0.1)
            load_img(device=device, pic_local='image/login_1.png', threshold_set=0.7, timeout=5, showimg=False, modecoler=False, showdb=False, region=None, mode_pic=1, resize=1, loop_image_delay=2)

            click(device=device, local=[940,160])
            delay(0.2)
            click(device=device, local=[940,300])
            delay(0.2)
            click(device=device, local=[940,400])
            delay(0.2)
            click(device=device, local=[400,500])
            delay(2)

            # == Step 4: go back to login
            print(f"[Thread {thread_id}] Step 4: Go Back To Login")
            command = [
                r'tools\adb.exe',
                '-s', device_serial,
                'shell',
                'input',
                'keyevent',
                'KEYCODE_BACK'
            ]

            res = subprocess.run(command, capture_output=True, text=True)

            # == Step 5: login guest
            print(f"[Thread {thread_id}] Step 5: Login Guest")
            find_img_and_click(device=device, pic_local='image/guest_login.png', threshold_set=0.7, showimg=False, modecoler=False, showdb=False, timeout=10, mode_pic=1, mode_click=1, resize=1, region=None, lv_click=1, loop_image_delay=1)
            find_img_and_click(device=device, pic_local='image/login_button.png', threshold_set=0.7, showimg=False, modecoler=False, showdb=False, timeout=10, mode_pic=1, mode_click=1, resize=1, region=None, lv_click=1, loop_image_delay=1)
            delay(2)

            load_img(device=device, pic_local='image/login_1.png', threshold_set=0.7, timeout=5, showimg=False, modecoler=False, showdb=False, region=None, mode_pic=1, resize=1, loop_image_delay=2)
            click(device=device, local=[940,170])
            delay(0.2)
            click(device=device, local=[940,300])
            delay(0.2)
            click(device=device, local=[940,380])
            delay(0.2)

            swipe(device, start=[400, 450], end=[400, 100], duration=1000, showdb=False)
            delay(1)
            click(device=device, local=[400,450])
            delay(2)

            while (True):
                if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=1, loop_image_delay=2)):
                    command = [
                        r'tools\adb.exe',
                        '-s', device_serial,
                        'shell',
                        'am',
                        'force-stop',
                        'com.linecorp.LGRGS'
                    ]
                    res = subprocess.run(command, capture_output=True, text=True)
                    delay(2)
                    break
                else:
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)

            
        else:
            print(f"[Thread {thread_id}] ⏭️ ข้าม Setup เนื่องจากไม่ใช่ first_run")


        # ============================================================
        # MAIN WORKFLOW - ทำทุกครั้ง (ทั้ง first_run และ repeat)
        # ============================================================

        # == Step 3: หาไฟล์จาก input folder (Thread-safe) ==
        print(f"[Thread {thread_id}] Step 3: เลือกไฟล์จาก input...")
        
        input_folder = 'input'
        
        # 🔒 ล็อคเพื่อป้องกันหลาย threads เลือกไฟล์เดียวกัน
        with file_lock:
            # สร้างโฟลเดอร์ถ้ายังไม่มี
            os.makedirs(input_folder, exist_ok=True)
            
            # ดึงรายชื่อไฟล์ .xml ทั้งหมด
            xml_files = [f for f in os.listdir(input_folder) if f.endswith('.xml')]
            
            if not xml_files:
                error_msg = f"❌ ไม่มีไฟล์ .xml ใน {input_folder}"
                print(f"[Thread {thread_id}] {error_msg}")
                print(f"[Thread {thread_id}] 💡 กรุณาเพิ่มไฟล์ .xml ลงใน folder '{input_folder}' ก่อนรัน workflow")
                return {
                    'success': False, 
                    'message': error_msg,
                    'suggestion': f'เพิ่มไฟล์ .xml ลงใน {input_folder}'
                }
            
            # เรียงลำดับไฟล์
            xml_files.sort()
            
            # แสดงจำนวนไฟล์ที่มี
            print(f"[Thread {thread_id}] 📦 พบไฟล์ทั้งหมด {len(xml_files)} ไฟล์ ใช้ไปแล้ว {len(used_file_indices)} ไฟล์")
            
            # หาไฟล์ที่ยังไม่ได้ใช้
            for idx, filename in enumerate(xml_files):
                if idx not in used_file_indices:
                    used_file_indices.add(idx)
                    file_to_push = os.path.join(input_folder, filename)
                    print(f"[Thread {thread_id}] 📁 เลือกไฟล์: {filename} (index: {idx})")
                    break
            
            # ถ้าใช้หมดแล้ว ให้ reset และเริ่มใหม่
            if file_to_push is None:
                print(f"[Thread {thread_id}] ♻️ ใช้ไฟล์หมดแล้ว รีเซ็ตและเริ่มใหม่")
                used_file_indices.clear()
                used_file_indices.add(0)
                file_to_push = os.path.join(input_folder, xml_files[0])
                print(f"[Thread {thread_id}] 📁 เลือกไฟล์: {xml_files[0]} (index: 0)")
        
        # 🔓 ปลดล็อคแล้ว - threads อื่นสามารถเลือกไฟล์ต่อได้


        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'shell',
            'am',
            'force-stop',
            'com.linecorp.LGRGS'
        ]
        res = subprocess.run(command, capture_output=True, text=True)
        delay(1)

        # == Step 4: Push ไฟล์ไปยัง device ==
        print(f"[Thread {thread_id}] Step 4: Push ไฟล์ลง device...")
        delay(0.5)
        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'push',
            file_to_push,
            '/data/data/com.linecorp.LGRGS/shared_prefs/_LINE_COCOS_PREF_KEY.xml'
        ]
        res = subprocess.run(command, capture_output=True, text=True)
        
        if res.returncode != 0:
            print(f"[Thread {thread_id}] ❌ Push ไฟล์ไม่สำเร็จ: {res.stderr}")
            return {'success': False, 'message': f'Push ไฟล์ไม่สำเร็จ: {res.stderr}'}
        
        print(f"[Thread {thread_id}] ✅ Push ไฟล์สำเร็จ")
        delay(0.5)

        # == Step 5: เปิดเกม ==
        print(f"[Thread {thread_id}] Step 5: หาและคลิกไอคอนเกม...")
        find_img_and_click(device=device, pic_local='image/icongame.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=10, mode_pic=1, mode_click=1, resize=1, lv_click=1)

        # รอให้เกมโหลด
        print(f"[Thread {thread_id}] รอเกมโหลด...")
        delay(5)

        while (True):
            find_img_and_click(device=device, pic_local='image/icongame.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=15, mode_pic=1, mode_click=1, resize=1, lv_click=1)
            delay(10)
            if (load_img(device=device, pic_local='image/blank.png', threshold_set=0.7, timeout=3, loop_image_delay=2)):
                command = [
                    r'tools\adb.exe',
                    '-s', device_serial,
                    'shell',
                    'am',
                    'force-stop',
                    'com.linecorp.LGRGS'
                ]

                res = subprocess.run(command, capture_output=True, text=True)

                delay(3)
                continue

            break

        while (True):
            if (load_img(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=1, loop_image_delay=1)):
                
                break
            else:
                find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=3, loop_image_delay=2, region=[600, 0, 920, 200])
                if (load_img(device=device, pic_local='image/close_false.png', threshold_set=0.7, timeout=1, loop_image_delay=1)):
                    click(device=device, local=[50,50])
                    delay(3)

        find_img_and_click(device=device, pic_local='image/gift.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        delay(0.5)
        find_img_and_click(device=device, pic_local='image/accept_all.png', threshold_set=0.7, timeout=8, loop_image_delay=4)
        while(True):
            if (load_img(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
            else:
                delay(0.5)
                find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                break


        delay(1)
        find_img_and_click(device=device, pic_local='image/gift.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        check_timeout = while_with_timeout(180)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            
            if (load_img(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=2, loop_image_delay=1, region=[0, 0, 680, 540])):
                print(f'[Thread {thread_id}] ok1')
                (find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=2, loop_image_delay=1, region=[0, 0, 680, 540]))
            elif (load_img(device=device, pic_local='image/ok_button_2.png', threshold_set=0.7, timeout=2, loop_image_delay=1, region=[0, 0, 680, 540])):
                print(f'[Thread {thread_id}] ok2')
                (find_img_and_click(device=device, pic_local='image/ok_button_2.png', threshold_set=0.7, timeout=2, loop_image_delay=1, region=[0, 0, 680, 540]))
            elif (load_img(device=device, pic_local='image/accept.png', threshold_set=0.7, timeout=2, loop_image_delay=1)):
                print(f'[Thread {thread_id}] accept')
                find_img_and_click(device=device, pic_local='image/accept.png', threshold_set=0.7, timeout=2, loop_image_delay=1)
                delay(2)
                click(device=device, local=[400,300])
            else:
                find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=2, loop_image_delay=1)
                load_img(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=10, loop_image_delay=1)
                find_img_and_click(device=device, pic_local='image/gift.png', threshold_set=0.7, timeout=2, loop_image_delay=1)
                if (load_img(device=device, pic_local='image/accept.png', threshold_set=0.7, timeout=10, loop_image_delay=4)):
                    find_img_and_click(device=device, pic_local='image/accept.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                    delay(2)
                    click(device=device, local=[400,300])
                    continue
                else:
                    find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=10, loop_image_delay=4) 
                    break

            delay(1)

        load_img(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=10, loop_image_delay=1)
        click(device=device, local=[50,160])
        print(f"[Thread {thread_id}] go to shop")
        if (load_img(device=device, pic_local='image/event/found.png', threshold_set=0.7, timeout=30, loop_image_delay=5)):
            while (True):
                if (load_img(device=device, pic_local='image/event/ticket.png', threshold_set=0.7, timeout=2, loop_image_delay=5)):
                    find_img_and_click(device=device, pic_local='image/event/ticket.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                    find_img_and_click(device=device, pic_local='image/event/buy.png', threshold_set=0.7, timeout=3, loop_image_delay=4)

                    if (load_img(device=device, pic_local='image/event/already.png', threshold_set=0.7, timeout=10, loop_image_delay=5)):
                        break
                    
                    delay(1)
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                    delay(1) 
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4) 
                    delay(1)
                elif (load_img(device=device, pic_local='image/event/ruby.png', threshold_set=0.7, timeout=2, loop_image_delay=5)):
                    find_img_and_click(device=device, pic_local='image/event/ruby.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                    find_img_and_click(device=device, pic_local='image/event/buy.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                    
                    if (load_img(device=device, pic_local='image/event/already.png', threshold_set=0.7, timeout=10, loop_image_delay=5)):
                        break
                    
                    delay(1)
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                    delay(1) 
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4) 
                    delay(1)

                else: break
        else: return {'success': False, 'message': 'Timeout exceeded'}


        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'shell',
            'am',
            'force-stop',
            'com.linecorp.LGRGS'
        ]

        res = subprocess.run(command, capture_output=True, text=True)
        if res.returncode == 0:
            print(f'[Thread {thread_id}] ปิดเกม สำเร็จ')

        delay(0.5)

        print(f"[Thread {thread_id}] Step End: คัดลอกไฟล์ที่ใช้ไปเก็บ...")
        output_autologin_folder = 'output/autologin'
        os.makedirs(output_autologin_folder, exist_ok=True)
        
        used_filename = os.path.basename(file_to_push)
        backup_path = os.path.join(output_autologin_folder, used_filename)
        # คัดลอกไฟล์
        shutil.move(file_to_push, backup_path)
        print(f"[Thread {thread_id}] ✅ ย้ายไฟล์ไปที่: {backup_path}")

        delay(1)


        return {'success': True, 'message': 'Workflow Auto Login สำเร็จ'}
        
    except Exception as e:
        print(f'[Thread {thread_id}] ❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        delay(5)
        return {'success': False, 'message': f'Error: {str(e)}'}


# ฟังก์ชันเสริม: รีเซ็ตการใช้ไฟล์ (ถ้าต้องการ)
def reset_file_usage():
    """รีเซ็ตการใช้ไฟล์ทั้งหมด"""
    global used_file_indices
    with file_lock:
        used_file_indices.clear()
        print("♻️ รีเซ็ตการใช้ไฟล์ทั้งหมดแล้ว")


def reset_device_setup(device_serial=None):
    """
    รีเซ็ตสถานะ setup ของ device
    
    Args:
        device_serial: Serial ของ device ที่ต้องการรีเซ็ต (None = รีเซ็ตทั้งหมด)
    """
    global device_setup_status
    with status_lock:
        if device_serial is None:
            device_setup_status.clear()
            print("♻️ รีเซ็ตสถานะ setup ของทุก devices แล้ว")
        else:
            if device_serial in device_setup_status:
                del device_setup_status[device_serial]
                print(f"♻️ รีเซ็ตสถานะ setup ของ {device_serial} แล้ว")
            else:
                print(f"ℹ️ {device_serial} ยังไม่เคย setup")


# ฟังก์ชันตรวจสอบไฟล์ก่อนรัน
def check_input_files(input_folder='input'):
    """ตรวจสอบว่ามีไฟล์ใน input folder หรือไม่"""
    os.makedirs(input_folder, exist_ok=True)
    xml_files = [f for f in os.listdir(input_folder) if f.endswith('.xml')]
    
    print("\n" + "=" * 60)
    print("📁 ตรวจสอบไฟล์ Input")
    print("=" * 60)
    print(f"📂 Folder: {input_folder}")
    
    if not xml_files:
        print("❌ ไม่พบไฟล์ .xml ใน input folder")
        print(f"💡 กรุณาเพิ่มไฟล์ .xml ลงใน '{input_folder}' ก่อนรัน workflow")
        print("=" * 60)
        return False
    
    print(f"✅ พบไฟล์ทั้งหมด {len(xml_files)} ไฟล์:")
    for i, filename in enumerate(xml_files, 1):
        file_path = os.path.join(input_folder, filename)
        file_size = os.path.getsize(file_path)
        print(f"   {i}. {filename} ({file_size:,} bytes)")
    print("=" * 60)
    return True