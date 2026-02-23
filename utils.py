"""
game_utils.py
รวมฟังก์ชันทั้งหมดสำหรับควบคุม Android device และ OCR
"""

import time
import io
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pytesseract import Output
import configparser

import re

# ===============================
# ฟังก์ชันพื้นฐานควบคุม Device
# ===============================

def find_img_and_click(device=None, pic_local='', threshold_set=0.8, showimg=False, 
                       modecoler=False, showdb=False, timeout=0, mode_pic=1, 
                       mode_click=1, resize=1, region=None, lv_click=1, loop_image_delay=0.1):
    """ค้นหารูปภาพตำแหน่งเดียว และ คลิก"""
    result = find_img(device, pic_local, threshold_set, showimg, modecoler, showdb, 
                     timeout, region, mode_pic, resize, getcenter=True, 
                     return_img=False, loop_image_delay=loop_image_delay)
    
    if result:
        click(device, result, lv_click, mode_click, showdb)
        return True
    return False


def find_img(device=None, pic_local='', threshold_set=0.8, showimg=False, 
            modecoler=False, showdb=False, timeout=0, region=None, mode_pic=1, 
            resize=1, getcenter=True, return_img=True, loop_image_delay=0.1):
    """ค้นหารูปภาพตำแหน่งเดียว"""
    start_time = time.time()
    
    while True:
        # ดึงภาพหน้าจอจาก device
        screen = device.screencap()
        screen_img = Image.open(io.BytesIO(screen))
        screen_cv = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)
        
        # ใช้ region ถ้ามีกำหนด
        if region:
            x1, y1, x2, y2 = region
            screen_cv = screen_cv[y1:y2, x1:x2]
        
        # โหลดรูปภาพที่ต้องการค้นหา
        if mode_pic == 1:
            template = cv2.imread(pic_local)
        else:
            template = pic_local
        
        # ปรับขนาดถ้าต้องการ
        if resize != 1:
            template = cv2.resize(template, None, fx=resize, fy=resize)
        
        # เปลี่ยนเป็นสีเทาถ้า modecoler=False
        if not modecoler:
            screen_cv = cv2.cvtColor(screen_cv, cv2.COLOR_BGR2GRAY)
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # ค้นหารูปภาพ
        result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if showdb:
            print(f'ค่าความแม่นยำ: {max_val:.2f} / เกณฑ์: {threshold_set}')
        
        # ถ้าเจอรูปภาพที่ต้องการ
        if max_val >= threshold_set:
            h, w = template.shape[:2]
            
            # คำนวณตำแหน่งกลาง
            if getcenter:
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                # ปรับตำแหน่งถ้าใช้ region
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                position = [center_x, center_y]
            else:
                position = [max_loc[0], max_loc[1]]
            
            if showimg:
                # วาดกรอบบนภาพที่เจอ
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                cv2.rectangle(screen_cv, top_left, bottom_right, (0, 255, 0), 2)
                cv2.imshow('Found Image', screen_cv)
                cv2.waitKey(1000)
                cv2.destroyAllWindows()
            
            if showdb:
                print(f'เจอรูปภาพที่ตำแหน่ง: {position}')
            
            if return_img:
                return position, screen_cv
            return position
        
        # ตรวจสอบ timeout
        if timeout > 0 and (time.time() - start_time) >= timeout:
            if showdb:
                print('หมดเวลาค้นหารูปภาพ')
            return None
        
        time.sleep(loop_image_delay)


def load_img(device=None, pic_local='', threshold_set=0.8, timeout=0.5, 
            showimg=False, modecoler=False, showdb=False, region=None, 
            mode_pic=1, resize=1, loop_image_delay=0.1):
    """รอโหลดรูปภาพ"""
    if showdb:
        print(f'รอโหลดรูปภาพ: {pic_local}')
    
    result = find_img(device, pic_local, threshold_set, showimg, modecoler, showdb, 
                     timeout, region, mode_pic, resize, getcenter=True, 
                     return_img=False, loop_image_delay=loop_image_delay)
    
    if result:
        if showdb:
            print('โหลดรูปภาพสำเร็จ')
        return True
    
    if showdb:
        print('ไม่สามารถโหลดรูปภาพได้')
    return False


def click(device=None, local=[], lv_click=1, mode_click=1, showdb=False):
    """คลิกตำแหน่งที่ต้องการ"""
    if not local or len(local) < 2:
        if showdb:
            print('ตำแหน่งไม่ถูกต้อง')
        return False
    
    x, y = local[0], local[1]
    
    if showdb:
        print(f'คลิกที่ตำแหน่ง: ({x}, {y})')
    
    # คลิกตามจำนวนครั้งที่กำหนด
    for i in range(lv_click):
        if mode_click == 1:
            # ใช้ input tap
            device.shell(f'input tap {x} {y}')
        elif mode_click == 2:
            # ใช้ input touchscreen tap
            device.shell(f'input touchscreen tap {x} {y}')
            
        if lv_click > 1:
            time.sleep(0.1)
    
    return True


def swipe(device, start=[0, 0], end=[100, 100], duration=300, showdb=False):
    """
    Swipe จากจุดเริ่มต้นไปจุดสิ้นสุด
    
    Parameters:
    -----------
    device : ADB device object
        อุปกรณ์ที่เชื่อมต่อผ่าน ADB
    start : list [x, y]
        พิกัดเริ่มต้น
    end : list [x, y]
        พิกัดปลายทาง
    duration : int
        ระยะเวลาในการ swipe (มิลลิวินาที) ยิ่งน้อยยิ่งเร็ว
    showdb : bool
        แสดง debug message หรือไม่
        
    Returns:
    --------
    bool : True เมื่อทำสำเร็จ
    """
    x1, y1 = start[0], start[1]
    x2, y2 = end[0], end[1]
    
    if showdb:
        print(f'Swipe จาก ({x1}, {y1}) ไป ({x2}, {y2}) ใช้เวลา {duration}ms')
    
    device.shell(f'input swipe {x1} {y1} {x2} {y2} {duration}')
    
    return True


def delay(time_input=0.5, showdb=False):
    """พักการทำงาน"""
    if showdb:
        print(f'พักการทำงาน {time_input} วินาที')
    time.sleep(time_input)
    return True


# ===============================
# ฟังก์ชัน OCR และ Config
# ===============================

# ตั้งค่า Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'TesseractOCR\tesseract.exe'


def fast_preprocess(image):
    """Preprocessing แบบเร็วที่สุด"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # CLAHE + OTSU
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Scale 2x
    h, w = binary.shape
    resized = cv2.resize(binary, (w*2, h*2), interpolation=cv2.INTER_LINEAR)
    
    return resized


def fast_ocr(processed_img):
    """OCR แบบเร็ว"""
    config = '--psm 11 --oem 3'
    
    data = pytesseract.image_to_data(
        processed_img,
        lang='eng',
        config=config,
        output_type=Output.DICT
    )
    
    return data


def extract_text_from_device(device, region=None, min_confidence=40):
    """
    ดึง text จากหน้าจอ device ผ่าน ADB
    
    Parameters:
    -----------
    device : ADB device object
        อุปกรณ์ที่เชื่อมต่อผ่าน ADB
    region : list [x1, y1, x2, y2] หรือ None
        พื้นที่ที่ต้องการ OCR (None = ทั้งหน้าจอ)
    min_confidence : int
        ค่าความมั่นใจขั้นต่ำ (0-100)
        
    Returns:
    --------
    list : รายการ text ที่เจอทั้งหมด
    """
    # ดึงภาพหน้าจอ
    screen = device.screencap()
    screen_img = Image.open(io.BytesIO(screen))
    screen_cv = cv2.cvtColor(np.array(screen_img), cv2.COLOR_RGB2BGR)
    
    # ใช้ region ถ้ามี
    if region:
        x1, y1, x2, y2 = region
        screen_cv = screen_cv[y1:y2, x1:x2]
    
    # Preprocess
    processed = fast_preprocess(screen_cv)
    
    # OCR
    data = fast_ocr(processed)
    
    # Extract text
    texts = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        conf = int(data['conf'][i])
        text = data['text'][i].strip()
        
        if conf > min_confidence and text:
            texts.append(text)
    
    return list(set(texts))


def load_config(config_path='config.ini'):
    """
    โหลด config.ini
    
    รูปแบบ: keyword1+keyword2-keyword3=OutputName
    + หมายถึง ต้องมีคำนี้ (AND)
    - หมายถึง ห้ามมีคำนี้ (NOT)
    
    Returns:
    --------
    dict : {'herowant': {...}, 'gearwant': {...}}
    """
    config = configparser.ConfigParser()
    config.read(config_path, encoding='utf-8')
    
    result = {}
    
    for section in config.sections():
        result[section.lower()] = {}
        for key, value in config.items(section):
            parts = value.split('=')
            if len(parts) == 2:
                pattern = parts[0].strip()
                return_name = parts[1].strip()
                
                # ===== ส่วนที่แก้ไข =====
                # แยก must_have (+) และ must_not_have (-)
                tokens = re.split(r'(\+|-)', pattern)
                
                must_have = []
                must_not_have = []
                
                current_mode = '+'  # default คือ must_have
                for token in tokens:
                    token = token.strip()
                    if token == '+':
                        current_mode = '+'
                    elif token == '-':
                        current_mode = '-'
                    elif token:
                        if current_mode == '+':
                            must_have.append(token)
                        else:
                            must_not_have.append(token)
                
                result[section.lower()][key] = {
                    'keywords': must_have,
                    'exclude': must_not_have,  # เพิ่มใหม่
                    'return_name': return_name
                }
                # ===== จบส่วนที่แก้ไข =====
    
    return result


def check_match(found_texts, config_entry):
    """
    เช็คว่า text ที่เจอตรงกับ pattern หรือไม่
    """
    keywords = config_entry['keywords']
    exclude = config_entry.get('exclude', [])  # เพิ่มใหม่
    
    # เช็คว่าทุก keyword (must_have) อยู่ใน found_texts
    for keyword in keywords:
        found = False
        for text in found_texts:
            if keyword.lower() in text.lower():
                found = True
                break
        if not found:
            return False
    
    # ===== ส่วนที่เพิ่มใหม่ =====
    # เช็คว่าไม่มี exclude keyword อยู่ใน found_texts
    for keyword in exclude:
        for text in found_texts:
            if keyword.lower() in text.lower():
                return False  # เจอสิ่งที่ห้ามมี
    # ===== จบส่วนที่เพิ่ม =====
    
    return True


def extract_text_from_device_enhanced(device, region=None, min_confidence=40):
    """
    ดึง text จากหน้าจอด้วยวิธีการ filter สีขาว/เหลืองและ preprocessing ขั้นสูง
    
    Parameters:
    -----------
    device : ADB device object
    region : list [x1, y1, x2, y2] หรือ None
    min_confidence : int
        ค่าความมั่นใจขั้นต่ำ (0-100)
        
    Returns:
    --------
    set : ชุดของ text ที่เจอ (cleaned)
    """
    try:
        # Capture screenshot
        screenshot = device.screencap()
        image = cv2.imdecode(np.frombuffer(screenshot, np.uint8), cv2.IMREAD_COLOR)
        
        if image is None:
            return set()
        
        # ถ้ามี region ให้ crop
        if region:
            x1, y1, x2, y2 = region
            image = image[y1:y2, x1:x2]
        
        # Filter white and yellow text
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # White mask
        lower_white = np.array([0, 0, 180])
        upper_white = np.array([180, 30, 255])
        mask_white = cv2.inRange(hsv, lower_white, upper_white)
        
        # Yellow mask
        lower_yellow = np.array([15, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
        
        # Combine masks
        combined_mask = cv2.bitwise_or(mask_white, mask_yellow)
        filtered_img = cv2.bitwise_and(image, image, mask=combined_mask)
        
        # Convert to grayscale
        gray = cv2.cvtColor(filtered_img, cv2.COLOR_BGR2GRAY)
        
        # Enhanced preprocessing
        # Method 1: CLAHE + Adaptive Threshold
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        adaptive = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )
        adaptive = cv2.bitwise_and(adaptive, adaptive, mask=combined_mask)
        
        # Method 2: Bilateral Filter + OTSU
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        _, otsu = cv2.threshold(bilateral, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        otsu = cv2.bitwise_and(otsu, otsu, mask=combined_mask)
        
        # Method 3: Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        
        # Combine methods
        combined = cv2.addWeighted(adaptive, 0.4, morph, 0.6, 0)
        
        # Scale up 3x for better OCR
        h, w = combined.shape
        scaled = cv2.resize(combined, (w*3, h*3), interpolation=cv2.INTER_CUBIC)
        
        # Multi-config OCR
        all_texts = set()
        configs = [
            '--psm 6 --oem 3',   # Uniform block
            '--psm 7 --oem 3',   # Single line
            '--psm 11 --oem 3',  # Sparse text
        ]
        
        for config in configs:
            try:
                data = pytesseract.image_to_data(
                    scaled,
                    lang='eng',
                    config=config,
                    output_type=Output.DICT
                )
                
                n_boxes = len(data['text'])
                for i in range(n_boxes):
                    conf = int(data['conf'][i])
                    text = data['text'][i].strip()
                    
                    if conf > min_confidence and text:
                        # Clean text
                        text = ''.join(c for c in text if c.isalnum() or c in [' ', "'", '-'])
                        
                        if len(text) >= 3 and any(c.isalpha() for c in text):
                            # Skip noise words
                            noise_words = ['the', 'and', 'or', 'to', 'a', 'in', 'is', 'it', 'of']
                            if text.lower() not in noise_words:
                                all_texts.add(text)
            except:
                continue
        
        return all_texts
        
    except Exception as e:
        print(f"❌ Error in extract_text_from_device_enhanced: {e}")
        return set()


def checkwant_gear(device, config_path='config.ini', region=None,
                   min_confidence=40, scan_times=15, showdb=True):
    """
    เช็คว่าเจอ gear ที่ต้องการหรือไม่ (scan หลายรอบด้วย enhanced OCR)
    
    Parameters:
    -----------
    device : ADB device object
        อุปกรณ์ที่เชื่อมต่อผ่าน ADB
    config_path : str
        path ของ config.ini
    region : list [x1, y1, x2, y2] หรือ None
        พื้นที่ที่ต้องการ OCR
    min_confidence : int
        ค่าความมั่นใจขั้นต่ำของ OCR (0-100)
    scan_times : int
        จำนวนครั้งที่จะ scan (default=15)
    showdb : bool
        แสดง debug message
        
    Returns:
    --------
    str or None : ชื่อ gear ที่ return หรือ None ถ้าไม่เจอ
    
    Examples:
    ---------
    # scan 15 ครั้งด้วย enhanced OCR
    result = checkwant_gear(device, scan_times=15, showdb=True)
    
    # scan 10 ครั้ง พร้อม region และ confidence 50
    result = checkwant_gear(device, scan_times=10, region=[100, 100, 500, 300], 
                           min_confidence=50)
    """
    
    section = 'gearwant'
    type_name = 'Gear'
    
    # โหลด config
    config = load_config(config_path)
    
    if section not in config:
        if showdb:
            print(f"❌ ไม่พบ section [{section}] ใน config")
        return None
    
    # เก็บ text ที่เจอทั้งหมดใน set
    all_found_texts = set()
    
    if showdb:
        print(f"🔄 [{type_name}] เริ่ม enhanced scan {scan_times} ครั้ง...")
        print(f"   - กรองสีขาว/เหลือง")
        print(f"   - ใช้ CLAHE + Adaptive Threshold + OTSU")
        print(f"   - Scale 3x + Multi-config OCR")
    
    # scan หลายรอบ
    for i in range(scan_times):
        # ดึง text ด้วยวิธีการใหม่
        found_texts = extract_text_from_device_enhanced(device, region, min_confidence)
        
        # เพิ่มเข้า set
        before_count = len(all_found_texts)
        all_found_texts.update(found_texts)
        new_texts = len(all_found_texts) - before_count
        
        if showdb:
            print(f"   รอบที่ {i+1}: เจอ {len(found_texts)} text (+{new_texts} ใหม่) -> รวม {len(all_found_texts)} text")
        
        # หน่วงเวลาเล็กน้อยระหว่างรอบ
        delay(0.5)
    
    if showdb:
        print(f"🔍 [{type_name}] Text ทั้งหมดที่เจอ ({len(all_found_texts)}):")
        for text in sorted(all_found_texts):
            print(f"     - {text}")
    
    # แปลง set เป็น list เพื่อเช็ค
    all_texts_list = list(all_found_texts)
    
    # เช็คแต่ละ pattern ตามลำดับ
    section_data = config[section]
    
    for key in sorted(section_data.keys()):
        entry = section_data[key]
        
        if check_match(all_texts_list, entry):
            return_name = entry['return_name']
            
            if showdb:
                print(f"✅ [{type_name}] เจอ! Pattern: {entry['keywords']} -> Return: {return_name}")
            
            return return_name
    
    if showdb:
        print(f"❌ [{type_name}] ไม่เจอ pattern ที่ตรงกับ config")
    
    return None


# ปรับ checkwant เดิมให้รองรับ scan_times เฉพาะ gear
def checkwant(device, mode=1, config_path='config.ini', region=None, 
              min_confidence=40, scan_times=1, showdb=True):
    """
    เช็คว่าเจอสิ่งที่ต้องการหรือไม่ (รวม char และ gear)
    
    Parameters:
    -----------
    device : ADB device object
    mode : int
        1 = เช็ค character (herowant)
        2 = เช็ค gear (gearwant)
    config_path : str
    region : list [x1, y1, x2, y2] หรือ None
    min_confidence : int
    scan_times : int
        จำนวนครั้งที่จะ scan (ใช้กับ mode=2 เท่านั้น)
    showdb : bool
        
    Returns:
    --------
    str or None
    """
    # mode=1 (character) ใช้วิธีเดิม
    section = 'herowant'
    type_name = 'Character'
    
    config = load_config(config_path)
    
    if section not in config:
        if showdb:
            print(f"❌ ไม่พบ section [{section}] ใน config")
        return None
    
    found_texts = extract_text_from_device(device, region, min_confidence)
    
    if showdb:
        print(f"🔍 [{type_name}] Text ที่เจอ: {found_texts}")
    
    section_data = config[section]
    
    for key in sorted(section_data.keys()):
        entry = section_data[key]
        
        if check_match(found_texts, entry):
            return_name = entry['return_name']
            
            if showdb:
                print(f"✅ [{type_name}] เจอ! Pattern: {entry['keywords']} -> Return: {return_name}")
            
            return return_name
    
    if showdb:
        print(f"❌ [{type_name}] ไม่เจอ pattern ที่ตรงกับ config")
    
    return None

def while_with_timeout(timeout_seconds):
    """Helper function สำหรับสร้าง while loop ที่มี timeout"""
    start_time = time.time()
    def check_timeout():
        return time.time() - start_time > timeout_seconds
    return check_timeout