"""
Multi-Emulator Bot - Refactored Version
ปรับปรุงโครงสร้าง ลดความซ้ำซ้อน และเพิ่มประสิทธิภาพ
"""

import subprocess
import threading
import queue
import traceback
import time
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any, List
from enum import Enum

from ppadb.client import Client as AdbClient

# Import workflows (import ครั้งเดียว)
from workflow import (
    workflow_reid_char,
    workflow_reid_gear,
    workflow_autologin,
    workflow_test,
    reset_device_setup,
    reset_file_usage,
    get_moved_count,
    reset_moved_count,
)
from utils import delay  # import เฉพาะที่ใช้แทน import *


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class WorkflowConfig:
    """Configuration สำหรับแต่ละ workflow"""
    function: Callable
    timeout_minutes: int
    modes: Dict[int, str] = None  # {mode_number: description}

    def __post_init__(self):
        if self.modes is None:
            self.modes = {1: "default"}

    @property
    def timeout_seconds(self) -> int:
        return self.timeout_minutes * 60


class WorkflowRegistry:
    """Registry สำหรับจัดการ workflows ทั้งหมด"""

    _workflows: Dict[str, WorkflowConfig] = {
        'reid_char': WorkflowConfig(workflow_reid_char, 20, {
            1: "gacha 1",
            2: "gacha 2",
            3: "gacha 3",
        }),
        'reid_gear': WorkflowConfig(workflow_reid_gear, 20, {
            1: "normal reid",
            2: "reid + 7days",
            3: "reid + event shop",
            4: "reid + 7days + event shop",
        }),
        'autologin': WorkflowConfig(workflow_autologin, 6, {
            1: "normal",
            2: "7days",
            3: "take all gift",
            4: "event",
        }),
        'test': WorkflowConfig(workflow_test, 8, {
            1: "normal test",
            2: "test + 7days",
            3: "test + event",
            4: "test + 7days + event",
        }),
    }
    
    @classmethod
    def get(cls, name: str) -> Optional[WorkflowConfig]:
        return cls._workflows.get(name.lower())
    
    @classmethod
    def list_all(cls) -> List[str]:
        return list(cls._workflows.keys())
    
    @classmethod
    def register(cls, name: str, func: Callable, timeout: int):
        """เพิ่ม workflow ใหม่"""
        cls._workflows[name.lower()] = WorkflowConfig(func, timeout)


# =============================================================================
# ADB Manager (Singleton Pattern)
# =============================================================================

class ADBManager:
    """จัดการ ADB connection แบบ Singleton"""
    
    _instance: Optional['ADBManager'] = None
    _client: Optional[AdbClient] = None
    
    # ตรวจจับ OS และใช้ path ที่ถูกต้อง
    ADB_PATH = 'tools/adb' if os.name != 'nt' else r'tools\adb.exe'
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def client(self) -> AdbClient:
        if self._client is None:
            self._client = AdbClient(host="127.0.0.1", port=5037)
        return self._client
    
    def run_command(self, args: List[str], description: str = "", timeout: int = 10) -> tuple[bool, str]:
        """รัน ADB command พร้อม error handling"""
        command = [self.ADB_PATH] + args
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            output = result.stdout + result.stderr
            success = result.returncode == 0
            
            if description:
                status = "สำเร็จ" if success else "ล้มเหลว"
                print(f'{description} {status}: {output.strip()}')
            
            return success, output
        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout: {description}")
            return False, "Timeout"
        except Exception as e:
            print(f"❌ Error: {e}")
            return False, str(e)
    
    def start_server(self) -> bool:
        return self.run_command(['start-server'], 'ADB Server')[0]
    
    def kill_server(self) -> bool:
        return self.run_command(['kill-server'], 'Kill ADB Server')[0]
    
    def get_devices(self) -> list:
        return self.client.devices()
    
    def root_device(self, serial: str) -> bool:
        """Root device เดี่ยว"""
        success, output = self.run_command(['-s', serial, 'root'], f'Root [{serial}]')
        
        output_lower = output.lower()
        if 'already running as root' in output_lower:
            print(f"[{serial}] ✓ เป็น root อยู่แล้ว")
            return True
        elif 'restarting adbd as root' in output_lower:
            print(f"[{serial}] ✓ Root สำเร็จ")
            return True
        elif 'cannot run as root' in output_lower:
            print(f"[{serial}] ⚠️ ไม่สามารถ root ได้ (production build)")
            return False
        
        return success
    
    def root_all_devices(self) -> bool:
        """Root ทุก devices"""
        print("\n" + "=" * 60)
        print("🔓 กำลัง Root ทุก Devices...")
        print("=" * 60)
        
        devices = self.get_devices()
        if not devices:
            print("❌ ไม่พบ device ที่เชื่อมต่อ")
            return False
        
        for device in devices:
            self.root_device(device.serial)
        
        print("\n⏳ รอ devices reconnect...")
        time.sleep(3)
        
        devices = self.get_devices()
        print(f"✓ พบ {len(devices)} devices หลัง root")
        return True


# =============================================================================
# Logger
# =============================================================================

class Logger:
    """จัดการ logging"""
    
    LOG_FILE = "log.txt"
    
    @classmethod
    def write(cls, workflow_name: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] - {workflow_name}\n"
        
        try:
            with open(cls.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_message)
        except Exception as e:
            print(f"⚠️ ไม่สามารถเขียน log ได้: {e}")


# =============================================================================
# Bot Thread Runner
# =============================================================================

@dataclass
class ThreadResult:
    """ผลลัพธ์จากแต่ละ thread"""
    thread_id: int
    serial: str
    workflow: str
    loop: int
    success: bool
    error: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.thread_id,
            'serial': self.serial,
            'workflow': self.workflow,
            'loop': self.loop,
            'success': self.success,
            'error': self.error,
            'result': self.result
        }


class BotRunner:
    """รัน bot บน device"""
    
    def __init__(self, device_serial: str, thread_id: int, workflow_name: str,
                 result_queue: queue.Queue, stop_event: threading.Event = None,
                 showdb: bool = False, mode: int = 1):
        self.device_serial = device_serial
        self.thread_id = thread_id
        self.workflow_name = workflow_name
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.showdb = showdb
        self.mode = mode
        self.adb = ADBManager()
        self.loop_count = 0

        # ดึง workflow config
        self.workflow_config = WorkflowRegistry.get(workflow_name)
    
    def log(self, message: str, emoji: str = ""):
        """Print log พร้อม thread ID"""
        print(f"[Thread {self.thread_id}] {emoji} {message}".strip())
    
    def put_result(self, success: bool, error: str = None, result: dict = None):
        """ส่งผลลัพธ์ไป queue"""
        self.result_queue.put(ThreadResult(
            thread_id=self.thread_id,
            serial=self.device_serial,
            workflow=self.workflow_name,
            loop=self.loop_count,
            success=success,
            error=error,
            result=result
        ).to_dict())
    
    def get_device(self):
        """หา device จาก serial"""
        for d in self.adb.get_devices():
            if d.serial == self.device_serial:
                return d
        return None
    
    def run_workflow_with_timeout(self, device) -> tuple[bool, Optional[dict], Optional[str]]:
        """รัน workflow พร้อม timeout"""
        workflow_queue = queue.Queue()
        workflow_done = threading.Event()
        timeout_seconds = self.workflow_config.timeout_seconds
        
        def workflow_wrapper():
            try:
                result = self.workflow_config.function(device, self.thread_id, showdb=self.showdb, mode=self.mode)
                workflow_queue.put(('success', result))
            except Exception as e:
                workflow_queue.put(('error', str(e)))
            finally:
                workflow_done.set()
        
        # Start workflow thread
        thread = threading.Thread(target=workflow_wrapper, daemon=True)
        thread.start()
        
        # Monitor progress
        start_time = time.time()
        last_status = 0
        
        while not workflow_done.is_set():
            elapsed = time.time() - start_time
            
            # Check timeout
            if elapsed > timeout_seconds:
                self.log(f"Timeout! ทำงานเกิน {self.workflow_config.timeout_minutes} นาที", "⏰")
                return False, None, f'Timeout: ทำงานเกิน {self.workflow_config.timeout_minutes} นาที'
            
            # Progress update ทุก 5 นาที
            if elapsed - last_status >= 300:
                remaining = (timeout_seconds - elapsed) / 60
                self.log(f"ทำงานมาแล้ว {int(elapsed/60)} นาที (เหลือ {int(remaining)} นาที)", "⏱️")
                last_status = elapsed
            
            workflow_done.wait(timeout=min(5.0, timeout_seconds - elapsed))
        
        # Get result
        if not workflow_queue.empty():
            status, data = workflow_queue.get_nowait()
            if status == 'success':
                return True, data, None
            else:
                return False, None, data
        
        return False, None, "Unknown error"
    
    def run(self):
        """Main loop"""
        if not self.workflow_config:
            self.log(f"ไม่พบ workflow: {self.workflow_name}", "❌")
            self.put_result(False, f"ไม่พบ workflow: {self.workflow_name}")
            return
        
        while True:
            if self.stop_event and self.stop_event.is_set():
                self.log("ได้รับคำสั่งหยุด", "🛑")
                break
            
            try:
                self.loop_count += 1
                self.log(f"รอบที่ {self.loop_count} - Device: {self.device_serial}", "🔄")
                
                # Get device
                device = self.get_device()
                if not device:
                    self.log(f"ไม่พบ device: {self.device_serial}", "❌")
                    self.put_result(False, f"ไม่พบ device: {self.device_serial}")
                    time.sleep(5)
                    continue
                
                self.log("เชื่อมต่อ device สำเร็จ", "✓")
                
                # Run workflow
                start_time = time.time()
                success, result, error = self.run_workflow_with_timeout(device)
                elapsed = time.time() - start_time
                
                if success:
                    self.put_result(True, result=result)
                    self.log(f"รอบที่ {self.loop_count} เสร็จ ({int(elapsed/60)}m {int(elapsed%60)}s)", "✅")

                    # หยุดถ้า workflow ส่ง stop flag (เช่น autologin ใช้ไฟล์หมดแล้ว)
                    if isinstance(result, dict) and result.get('stop'):
                        self.log(result.get('message', 'เสร็จสิ้น'), "🏁")
                        break
                else:
                    self.put_result(False, error=error)

                    # ไม่ reset_device_setup เมื่อ timeout เพราะ daemon thread ยังรันอยู่บนเครื่อง
                    # การ reset จะทำให้ loop ถัดไป force-stop app และลบ prefs ขณะที่ daemon thread
                    # กำลังใช้งาน prefs นั้นอยู่ ทำให้ชนกัน

                time.sleep(5)
                
            except Exception as e:
                self.log(f"Error: {e}", "❌")
                traceback.print_exc()
                self.put_result(False, error=str(e))
                time.sleep(5)


# =============================================================================
# Multi-Emulator Controller
# =============================================================================

class MultiEmulatorController:
    """ควบคุมการรัน bot บนหลาย emulators"""
    
    def __init__(self, workflow_name: str, showdb: bool = False, mode: int = 1):
        self.workflow_name = workflow_name
        self.showdb = showdb
        self.mode = mode
        self.adb = ADBManager()
        self.result_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.threads: List[threading.Thread] = []
    
    def print_header(self):
        config = WorkflowRegistry.get(self.workflow_name)
        timeout = config.timeout_minutes if config else 'N/A'
        mode_desc = config.modes.get(self.mode, "unknown") if config else 'N/A'

        print("=" * 60)
        print(f"🎮 Multi-Emulator Bot (Refactored)")
        print(f"📋 Workflow: {self.workflow_name}")
        print(f"⚙️  Mode: {self.mode} - {mode_desc}")
        print(f"⏰ Timeout: {timeout} นาที")
        print("=" * 60)
    
    def print_results(self, total_devices: int):
        results = []
        while not self.result_queue.empty():
            try:
                results.append(self.result_queue.get_nowait())
            except queue.Empty:
                break

        print("\n" + "=" * 60)
        print("📊 ผลลัพธ์:")
        print("=" * 60)

        # สำหรับ autologin ใช้ moved_count ที่นับจาก shutil.move จริง
        # (แทนการนับจาก result queue ซึ่งจะนับพลาดถ้า thread timeout แต่ daemon ยังย้ายไฟล์ต่อได้)
        if 'autologin' in self.workflow_name.lower():
            file_count = get_moved_count()
            print(f"\n📁 ใส่ไฟล์ไปทั้งหมด {file_count} ไฟล์")
        else:
            success_count = sum(1 for r in results if r['success'])
            fail_count = len(results) - success_count

            for result in sorted(results, key=lambda x: x['id']):
                status = "✅" if result['success'] else "❌"
                print(f"\n{status} Thread {result['id']} ({result['serial']})")
                print(f"   Workflow: {result['workflow']}, รอบ: {result.get('loop', 'N/A')}")
                if result.get('error'):
                    print(f"   Error: {result['error']}")

            print(f"\n📈 สรุป: ✅ {success_count} / ❌ {fail_count} จากทั้งหมด {total_devices} devices")

        print("=" * 60)

        return results
    
    def run(self) -> list:
        self.print_header()
        
        # Validate workflow
        if not WorkflowRegistry.get(self.workflow_name):
            print(f"\n❌ ไม่พบ workflow: {self.workflow_name}")
            print(f"📋 Workflows ที่มี: {WorkflowRegistry.list_all()}")
            return []
        
        # Root devices
        self.adb.root_all_devices()
        
        # Get devices
        devices = self.adb.get_devices()
        if not devices:
            print("❌ ไม่พบ device ที่เชื่อมต่อ")
            return []
        
        print(f"\n✓ พบ {len(devices)} devices:")
        for i, device in enumerate(devices, 1):
            print(f"  {i}. {device.serial}")
        
        try:
            # Start threads
            for i, device in enumerate(devices, 1):
                runner = BotRunner(
                    device.serial, i, self.workflow_name,
                    self.result_queue, self.stop_event, self.showdb, self.mode
                )
                thread = threading.Thread(target=runner.run, daemon=True)
                self.threads.append(thread)
                thread.start()
                print(f"\n✓ เริ่ม Thread {i} สำหรับ device: {device.serial}")
                
                if i < len(devices):
                    time.sleep(0.5)
            
            print("\n" + "=" * 60)
            print("⏳ กำลังรอให้ทุก Thread ทำงานเสร็จ...")
            print("(กด Ctrl+C เพื่อหยุด)")
            print("=" * 60)
            
            for thread in self.threads:
                thread.join()
        
        except KeyboardInterrupt:
            print("\n\n⚠️ ได้รับคำสั่งหยุด (Ctrl+C)")
            self.stop_event.set()
            print("⏳ กำลังหยุด threads...")
            time.sleep(2)
        
        finally:
            results = self.print_results(len(devices))
            self.threads.clear()
            return results


# =============================================================================
# Main Entry Point
# =============================================================================

def clear_screen():
    """ล้างหน้าจอ CLI (รองรับทั้ง Windows และ Unix)"""
    os.system('cls' if os.name == 'nt' else 'clear')


def wait_for_keypress(message="👉 กดปุ่มใดก็ได้เพื่อดำเนินการต่อ..."):
    """รอ user กดปุ่มใดก็ได้ (รองรับทั้ง Windows และ Unix)"""
    print(message)
    if os.name == 'nt':
        import msvcrt
        msvcrt.getch()
    else:
        input()


def clear_module_cache():
    """ล้าง module cache (สำหรับ development)"""
    import sys
    modules_to_clear = [
        'workflow', 'workflow.workflow_reid_char',
        'workflow.workflow_reid_gear', 'workflow.workflow_autologin', 'utils'
    ]
    for module in modules_to_clear:
        if module in sys.modules:
            del sys.modules[module]
            print(f"Cleared: {module}")
    print("✓ Module cache cleared!")


def display_menu() -> tuple[Optional[str], int]:
    """แสดง interactive menu และให้เลือก workflow + mode
    - เคลียร์หน้าจอทุกครั้งที่รับ input
    - สามารถย้อนกลับจากหน้า mode ไปหน้า workflow ได้ (กด 0)

    Returns:
        tuple: (workflow_name, mode) หรือ (None, 0) ถ้าออก
    """
    workflows = WorkflowRegistry.list_all()

    while True:
        # ===== ขั้นตอนที่ 1: เลือก Workflow =====
        clear_screen()
        print("\n" + "=" * 70)
        print("🤖  MULTI-EMULATOR BOT - WORKFLOW SELECTOR".center(70))
        print("=" * 70)

        print("\n📋 เลือก Workflow ที่ต้องการรัน:\n")
        for i, name in enumerate(workflows, 1):
            config = WorkflowRegistry.get(name)
            timeout_info = f"⏰ {config.timeout_minutes} นาที"
            print(f"   [{i}]  {name:<20} {timeout_info}")

        print(f"\n   [0]  ❌ ออกจากโปรแกรม")
        print("\n" + "-" * 70)

        selected = None
        while True:
            try:
                choice = input("\n👉 เลือกหมายเลข (0-{}): ".format(len(workflows)))
                choice_num = int(choice)

                if choice_num == 0:
                    print("\n👋 ออกจากโปรแกรม...")
                    return None, 0

                if 1 <= choice_num <= len(workflows):
                    selected = workflows[choice_num - 1]
                    break
                else:
                    print(f"❌ กรุณาเลือกหมายเลข 0-{len(workflows)}")

            except ValueError:
                print("❌ กรุณาใส่ตัวเลขเท่านั้น")
            except KeyboardInterrupt:
                print("\n\n👋 ออกจากโปรแกรม...")
                return None, 0

        # ===== ขั้นตอนที่ 2: เลือก Mode =====
        config = WorkflowRegistry.get(selected)
        modes = config.modes
        mode_keys = list(modes.keys())

        clear_screen()
        print("\n" + "=" * 70)
        print(f"⚙️  เลือก Mode สำหรับ [{selected}]".center(70))
        print("=" * 70)

        print(f"\n📋 Workflow: {selected}  |  ⏰ Timeout: {config.timeout_minutes} นาที\n")
        for mode_num, mode_desc in modes.items():
            print(f"   [{mode_num}]  {mode_num}: {mode_desc}")

        print(f"\n   [0]  ⬅️  ย้อนกลับเลือก Workflow")
        print("\n" + "-" * 70)

        go_back = False
        while True:
            try:
                mode_input = input(f"\n👉 เลือก Mode ({mode_keys[0]}-{mode_keys[-1]}) [default={mode_keys[0]}]: ").strip()

                if mode_input == "0":
                    go_back = True
                    break

                if mode_input == "":
                    mode = mode_keys[0]
                else:
                    mode = int(mode_input)

                if mode in modes:
                    print(f"✅ Mode: {mode} - {modes[mode]}")
                    return selected, mode
                else:
                    print(f"❌ กรุณาเลือก Mode {mode_keys[0]}-{mode_keys[-1]} หรือ 0 เพื่อย้อนกลับ")
            except ValueError:
                print("❌ กรุณาใส่ตัวเลขเท่านั้น")
            except KeyboardInterrupt:
                print("\n\n👋 ออกจากโปรแกรม...")
                return None, 0

        if go_back:
            continue  # วนกลับไปเลือก workflow ใหม่


def main():
    # Optional: Clear module cache for development
    clear_module_cache()

    # Initialize ADB
    print("\n⚙️  กำลังเตรียมระบบ...\n")
    adb = ADBManager()
    adb.kill_server()
    adb.start_server()

    print(f'✓ ADB Version: {adb.client.version()}')

    # Show devices
    devices = adb.get_devices()
    print(f'✓ พบ Device: {len(devices)} เครื่อง')
    for device in devices:
        print(f'  - {device.serial}')

    print("\n⏳ กำลังโหลด workflows...")
    time.sleep(1)

    while True:
        # Clear screen before showing menu
        clear_screen()

        # Show menu and get workflow + mode selection
        WORKFLOW_TO_RUN, MODE = display_menu()

        # Exit if user chose to quit
        if WORKFLOW_TO_RUN is None:
            return []

        # Clear screen before running
        print("\n⏳ กำลังเริ่มต้น...")
        time.sleep(1)
        clear_screen()

        # Log and run
        Logger.write(f"{WORKFLOW_TO_RUN} (mode={MODE})")

        controller = MultiEmulatorController(WORKFLOW_TO_RUN, showdb=False, mode=MODE)
        results = controller.run()

        # แสดงข้อความเสร็จสิ้นและรอ user กดปุ่มเพื่อกลับไปเลือก workflow
        print("\n" + "=" * 60)
        print("🏁 เสร็จสิ้นการทำงาน".center(60))
        print("=" * 60)
        wait_for_keypress("\n👉 กดปุ่มใดก็ได้เพื่อกลับไปหน้าเลือก Workflow...")

        # Reset autologin state เมื่อกลับไปเลือก workflow ใหม่
        if 'autologin' in WORKFLOW_TO_RUN.lower():
            reset_device_setup()
            reset_file_usage()
            reset_moved_count()


if __name__ == "__main__":
    main()