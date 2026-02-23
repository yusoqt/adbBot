import os
import subprocess
import pyperclip
import threading
from utils import (
    find_img_and_click,
    load_img,
    click,
    swipe,
    delay,
    checkwant,
    while_with_timeout,
)

clipboard_lock = threading.Lock()

def workflow_reid_char(device, thread_id, showdb=False, mode=1):
    """
    Workflow: Reid
    ขั้นตอน: find_click -> find_click -> check_char -> end

    Args:
        device: ADB device object
        thread_id: ID ของ thread
        showdb: แสดง debug หรือไม่
        mode: โหมดการทำงาน (1=normal reid, 2=reid+7days, 3=reid+event shop, 4=reid+7days+event shop)

    Returns:
        dict: ผลลัพธ์การทำงาน {'success': bool, 'message': str, ...}
    """
    # =============================================
    # ตัวอย่างการใช้ mode:
    # if mode == 1:
    #     # normal reid - reid ปกติ
    # if mode == 2:
    #     # reid + 7days - reid แล้วรับ 7days reward
    # if mode == 3:
    #     # reid + event shop - reid แล้วไปซื้อของใน event shop
    # if mode == 4:
    #     # reid + 7days + event shop - reid แล้วทำทั้งสองอย่าง
    # if mode in [2, 4]:
    #     # ทำงานเฉพาะ mode ที่ต้องรับ 7days
    # if mode in [3, 4]:
    #     # ทำงานเฉพาะ mode ที่ต้องไป event shop
    # =============================================
    try:

        device_serial = device.serial
        print(f"[Thread {thread_id} - {device_serial}] 🚀 เริ่ม Workflow: Reid (mode={mode})")

        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'shell',
            'am',
            'force-stop',
            'com.linecorp.LGRGS'
        ]

        res = subprocess.run(command, capture_output=True, text=True)

        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'shell',
            'rm',
            '/data/data/com.linecorp.LGRGS/shared_prefs/*' # _LINE_COCOS_PREF_KEY.xml
        ]

        res = subprocess.run(command, capture_output=True, text=True)

        # == Step 1: คลิกไอคอนเกม
        print(f"[Thread {thread_id}] Step 1: หาและคลิกไอคอนเกม...")
        if (load_img(device=device, pic_local='image/icongame.png', threshold_set=0.7, timeout=10, loop_image_delay=2)):
            find_img_and_click(device=device, pic_local='image/icongame.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=3, mode_pic=1, mode_click=1, resize=1, lv_click=1)

        elif (load_img(device=device, pic_local='image/event/iconevent.png', threshold_set=0.7, timeout=10, loop_image_delay=2)):
            find_img_and_click(device=device, pic_local='image/event/iconevent.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=3, mode_pic=1, mode_click=1, resize=1, lv_click=1)

        # == Step 2: คลิกไอคอน apple
        print(f"[Thread {thread_id}] Step 2: Click Apple Icon")
        find_img_and_click(device=device, pic_local='image/login_0.png', threshold_set=0.7, showimg=False, modecoler=False, showdb=False, timeout=60, mode_pic=1, mode_click=1, resize=1, region=None, lv_click=1, loop_image_delay=0.1)

        # == Step 3: click agree all
        print(f"[Thread {thread_id}] Step 3: Click Agree All")
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

        # == Step 6: fight
        print(f"[Thread {thread_id}] Step 6: Fight")
        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=1, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                break
            else:
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)

        delay(1)
        
        for i in range(5):
            click(device=device, local=[100,100])
            delay(1)

        click(device=device, local=[279,473])
        delay(2)
        click(device=device, local=[378,480])
        delay(2)

        for i in range(4):
            find_img_and_click(device=device, pic_local='image/mineral.png', threshold_set=0.7, timeout=10, loop_image_delay=2)
            delay(1)
        
        delay(2)
        find_img_and_click(device=device, pic_local='image/mineral.png', threshold_set=0.7, timeout=10, loop_image_delay=2)

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=1, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                break
            else:
                click(device=device, local=[180,473])
                delay(0.5)
                click(device=device, local=[279,473])
                delay(0.5)
                click(device=device, local=[378,480])
                delay(0.5)
                click(device=device, local=[473,473])
                delay(0.5)
                click(device=device, local=[577,473])
                delay(0.5)
                click(device=device, local=[675,473])
                delay(0.5)

        delay(1)

        if (load_img(device=device, pic_local='image/fail.png', threshold_set=0.7, timeout=15, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                delay(1)
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

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/stage_1.png', threshold_set=0.7, timeout=2, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/stage_1.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                break
            else:
                click(device=device, local=[180,473])
                delay(0.2)
                click(device=device, local=[279,450])
                delay(0.5)
                click(device=device, local=[378,450])
                delay(0.5)
                click(device=device, local=[473,450])
                delay(0.5)
                click(device=device, local=[577,450])
                delay(0.2)
                click(device=device, local=[675,473])
                delay(0.2)
                click(device=device, local=[775,473])
                delay(0.2)
                click(device=device, local=[500,100])
                delay(0.2)
        
        # == Step 7: tutorial
        print(f"[Thread {thread_id}] Step 7: Tutorial")
        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                break
            else:
                click(device=device, local=[200,400])
                delay(0.5)
                click(device=device, local=[450,500])
                delay(0.5)
                click(device=device, local=[50,50])
                delay(0.5)
                click(device=device, local=[279,450])
                delay(0.5)
                click(device=device, local=[378,450])
                delay(0.5)
                click(device=device, local=[473,450])
                delay(0.5)
                click(device=device, local=[577,450])
                delay(0.5)

        delay(1)
        

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                delay(0.5)
                click(device=device, local=[300,450])
                delay(10)
                click(device=device, local=[400,450])
                delay(2)
                click(device=device, local=[400,450])
                break
            else:
                find_img_and_click(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=2, loop_image_delay=4)
                delay(0.5)


        find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=30, loop_image_delay=4)
        find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=30, loop_image_delay=4)
        delay(2)

        for i in range(5):
            click(device=device, local=[200,500])
            delay(1)



        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            swipe(device, start=[170, 200], end=[170, 500], duration=400, showdb=False)
            delay(3)
            if (load_img(device=device, pic_local='image/error.png', threshold_set=0.7, timeout=1, loop_image_delay=4)):
                swipe(device, start=[500, 500], end=[500, 80], duration=400, showdb=False)
                return {'success': False, 'message': f'Error: {str(e)}'}
            swipe(device, start=[170, 500], end=[170, 200], duration=400, showdb=False)
            delay(2)
            if (load_img(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=2, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/skip_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/save.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=20, loop_image_delay=4)
                break

        # == Step 8: Re-Game
        print(f"[Thread {thread_id}] Step 8: Re-Game")

        if (load_img(device=device, pic_local='image/fail.png', threshold_set=0.7, timeout=15, loop_image_delay=2) or (load_img(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=2) and not load_img(device=device, pic_local='image/login_0.png', threshold_set=0.7, timeout=15, loop_image_delay=2))):
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                delay(1)

                if (not load_img(device=device, pic_local='image/guest_login.png', threshold_set=0.7, timeout=5, showimg=False, modecoler=False, showdb=False, region=None, mode_pic=1, resize=1, loop_image_delay=2)):


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

                    command = [
                        r'tools\adb.exe',
                        '-s', device_serial,
                        'shell',
                        'input',
                        'keyevent',
                        'KEYCODE_BACK'
                    ]

                    res = subprocess.run(command, capture_output=True, text=True)

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

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/stage_1.png', threshold_set=0.7, timeout=2, loop_image_delay=4)):
                delay(3)
                find_img_and_click(device=device, pic_local='image/stage_1.png', threshold_set=0.85, timeout=10, loop_image_delay=4)
                delay(5)
                break
            else: 
                click(device=device, local=[500,100])


        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/fintoregame.png', threshold_set=0.7, timeout=2, loop_image_delay=4)):
                delay(0.5)
                break
            else:
                click(device=device, local=[279,450])
                delay(0.5)
                click(device=device, local=[378,450])
                delay(0.5)
                click(device=device, local=[473,450])
                delay(0.5)
                click(device=device, local=[577,450])
                delay(0.5)
                

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
            print('ปิดเกม สำเร็จ :')

        delay(3)

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/icongame.png', threshold_set=0.7, timeout=10, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/icongame.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=3, mode_pic=1, mode_click=1, resize=1, lv_click=1)

            elif (load_img(device=device, pic_local='image/event/iconevent.png', threshold_set=0.7, timeout=10, loop_image_delay=2)):
                find_img_and_click(device=device, pic_local='image/event/iconevent.png', threshold_set=0.8, showimg=False, modecoler=True, showdb=showdb, timeout=3, mode_pic=1, mode_click=1, resize=1, lv_click=1)
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

            
            if (load_img(device=device, pic_local='image/fail.png', threshold_set=0.7, timeout=15, loop_image_delay=2) or (load_img(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=2) and not load_img(device=device, pic_local='image/login_0.png', threshold_set=0.7, timeout=15, loop_image_delay=2))):
                    find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                    delay(1)

                    if (not load_img(device=device, pic_local='image/guest_login.png', threshold_set=0.7, timeout=5, showimg=False, modecoler=False, showdb=False, region=None, mode_pic=1, resize=1, loop_image_delay=2)):


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

                        command = [
                            r'tools\adb.exe',
                            '-s', device_serial,
                            'shell',
                            'input',
                            'keyevent',
                            'KEYCODE_BACK'
                        ]

                        res = subprocess.run(command, capture_output=True, text=True)

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
                
            break

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            if (load_img(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=1, loop_image_delay=4) and not (load_img(device=device, pic_local='image/close.png', threshold_set=0.85, timeout=1, loop_image_delay=4))):
                find_img_and_click(device=device, pic_local='image/7days_icon.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
                delay(2)
                break
            else:
                find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=5, loop_image_delay=4, region=[0, 0, 920, 540])
            

        click(device=device, local=[350,480])
        delay(5)
        find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
        delay(2)

        find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
        delay(0.5)
        find_img_and_click(device=device, pic_local='image/gift.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        delay(0.5)
        find_img_and_click(device=device, pic_local='image/accept_all.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        while(True):
            if (load_img(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=5, loop_image_delay=4)
            else:
                delay(0.5)
                find_img_and_click(device=device, pic_local='image/close.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
                break

        # for shop event ################################################################################
        # load_img(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=10, loop_image_delay=1)
        # click(device=device, local=[50,160])
        # print(f"[Thread {thread_id}] go to shop")
        # if (load_img(device=device, pic_local='image/event/found.png', threshold_set=0.7, timeout=30, loop_image_delay=5)):
        #     while (True):
        #         if (load_img(device=device, pic_local='image/event/ticket.png', threshold_set=0.7, timeout=2, loop_image_delay=5)):
        #             find_img_and_click(device=device, pic_local='image/event/ticket.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
        #             find_img_and_click(device=device, pic_local='image/event/buy.png', threshold_set=0.7, timeout=3, loop_image_delay=4)

        #             if (load_img(device=device, pic_local='image/event/already.png', threshold_set=0.7, timeout=10, loop_image_delay=5)):
        #                 break
                    
        #             delay(1)
        #             find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
        #             delay(1) 
        #             find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=3, loop_image_delay=4) 
        #             delay(1)
        #         else: break
        # else: return {'success': False, 'message': 'Timeout exceeded'}

        # delay(1)
        # click(device=device, local=[50,50])
        # delay(1)

        ################################################################################################

        # == Step 9: Gacha

        find_img_and_click(device=device, pic_local='image/gacha.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        load_img(device=device, pic_local='image/random1time.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        # Gacha 1 pos: 150
        if (mode == 1):
            click(device=device, local=[800,150])
        # Gacha 2 pos: 300
        if (mode == 2):
            click(device=device, local=[800,300])
        # Gacha 3 pos: 380
        if (mode == 3):
            click(device=device, local=[800,380])
        delay(3)
        find_img_and_click(device=device, pic_local='image/random1time.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)


        # == Step 10: Check Hero
        matched_chars = []   # list หลักเก็บผลลัพธ์

        check_timeout = while_with_timeout(360)
        while (True):
            if check_timeout():
                return {'success': False, 'message': 'Timeout exceeded'}
            print("check Char")
            if (load_img(device=device, pic_local='image/random_again.png', threshold_set=0.7, timeout=20, loop_image_delay=4)):
                print(f"[Thread {thread_id}] 📝 เช็ค Character...")
                
                temp_set = set()  # ใช้ set ชั่วคราวป้องกันค่าซ้ำในแต่ละรอบ

                for i in range(8): 
                    print(f"[Thread {thread_id}] 🔍 รอบที่ {i+1}/8")
                    
                    hero_name = checkwant(
                        device=device,
                        mode=1,  # 1 = character
                        region=[0, 0, 960, 540],
                        showdb=True
                    )

                    if hero_name:
                        print(f"[Thread {thread_id}] ✅ เจอ Hero: {hero_name}")
                        temp_set.add(hero_name)   # add ลง set ชั่วคราว
                        delay(1)
                    else:
                        print(f"[Thread {thread_id}] ❌ ไม่เจอ")

                    delay(0.5)

                # จบ 8 รอบแล้ว ค่อยเอาจาก set ไปใส่ list หลัก
                matched_chars.extend(temp_set)
                print(matched_chars)
                delay(0.5)
                find_img_and_click(device=device, pic_local='image/random_again.png', threshold_set=0.7, timeout=3, loop_image_delay=4)
                delay(1)
                
            if (load_img(device=device, pic_local='image/check_ticket.png', threshold_set=0.7, timeout=8, loop_image_delay=4)):
                find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
            else:
                break
        
        click(device=device, local=[400,350])
        delay(3)
        find_img_and_click(device=device, pic_local='image/ok_button.png', threshold_set=0.7, timeout=15, loop_image_delay=4)
        delay(3)
        click(device=device, local=[50,50])
        delay(3)
        click(device=device, local=[850,520])
        delay(3)
        click(device=device, local=[700,100])
        delay(3)
        click(device=device, local=[730,280])
        delay(1)
        
        with clipboard_lock:
            max_retries = 2
            id = None
            
            for attempt in range(max_retries):
                temp_id = pyperclip.paste()
                
                if temp_id and len(temp_id) > 3:
                    id = temp_id
                    print(f"[Thread {thread_id}] ✅ ID: {id}")
                    break
                
                if attempt < max_retries - 1:
                    delay(0.5)
            
            if not id:
                id = f"unknown_{thread_id}_"
                print(f"[Thread {thread_id}] ⚠️ ใช้ ID สำรอง: {id}")

        if matched_chars:
            namefile = f"{'_'.join(matched_chars)}_{id}_LINE_COCOS_PREF_KEY.xml"
        else:
            namefile = f"{id}_LINE_COCOS_PREF_KEY.xml"
        

        output_path = os.path.join('output', 'reid', namefile)
        os.makedirs('output/reid', exist_ok=True)

        delay(1)


        command = [
            r'tools\adb.exe',
            '-s', device_serial,
            'pull',
            '/data/data/com.linecorp.LGRGS/shared_prefs/_LINE_COCOS_PREF_KEY.xml',
            output_path
        ]

        res = subprocess.run(command, capture_output=True, text=True)

        if res.returncode == 0:
            print('เซฟไฟล์เกมสำเร็จ !')

        delay(1)
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
            print('ปิดเกม สำเร็จ :')


        return {'success': True, 'message': 'Workflow Reid สำเร็จ'}
    except Exception as e:
        print(f'Error: {str(e)}')
        delay(5)
        return {'success': False, 'message': f'Error: {str(e)}'}
