import os
import shutil
from pathlib import Path

def find_unique_files(folder1, folder2):
    """
    หาไฟล์ที่อยู่ใน folder1 แต่ไม่อยู่ใน folder2
    """
    # ดึงชื่อไฟล์ทั้งหมดจากแต่ละ folder
    files1 = set(os.listdir(folder1))
    files2 = set(os.listdir(folder2))
    
    # หาไฟล์ที่ไม่ซ้ำกัน
    unique_in_folder1 = files1 - files2
    unique_in_folder2 = files2 - files1
    
    return unique_in_folder1, unique_in_folder2

def copy_unique_files(source_folder, target_folder, output_folder):
    """
    คัดลอกไฟล์ที่ไม่ซ้ำไปยัง folder ปลายทาง
    """
    # สร้าง folder ปลายทางถ้ายังไม่มี
    os.makedirs(output_folder, exist_ok=True)
    
    unique_files, _ = find_unique_files(source_folder, target_folder)
    
    copied_count = 0
    for filename in unique_files:
        source_path = os.path.join(source_folder, filename)
        dest_path = os.path.join(output_folder, filename)
        
        # คัดลอกเฉพาะไฟล์ (ไม่ใช่ folder)
        if os.path.isfile(source_path):
            shutil.copy2(source_path, dest_path)
            copied_count += 1
            print(f"คัดลอก: {filename}")
    
    print(f"\nคัดลอกทั้งหมด {copied_count} ไฟล์")

# ตัวอย่างการใช้งาน
if __name__ == "__main__":
    folder2 = "output/autologin"
    folder1 = "input"
    output = "output\copyfile"
    
    # แสดงไฟล์ที่ไม่ซ้ำกัน
    unique1, unique2 = find_unique_files(folder1, folder2)
    
    print("ไฟล์ที่อยู่ใน folder1 แต่ไม่อยู่ใน folder2:")
    for file in unique1:
        print(f"  - {file}")
    
    print("\nไฟล์ที่อยู่ใน folder2 แต่ไม่อยู่ใน folder1:")
    for file in unique2:
        print(f"  - {file}")
    
    # คัดลอกไฟล์ที่ไม่ซ้ำ
    copy_unique_files(folder1, folder2, output)