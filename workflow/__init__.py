"""
Workflow Package
================
Package สำหรับเก็บ workflows ทั้งหมด

Available workflows:
- workflow_reid: Reid workflow
- workflow_autologin: Auto Login workflow
"""

from .workflow_reid_char import workflow_reid_char
from .workflow_reid_gear import workflow_reid_gear
from .workflow_autologin import workflow_autologin, reset_file_usage, check_input_files, reset_device_setup, get_moved_count, reset_moved_count

from .workflow_test import workflow_test

__all__ = [
    'workflow_reid_char',
    'workflow_reid_gear',
    'workflow_autologin',
    'reset_file_usage',
    'check_input_files',
    'reset_device_setup',
    'get_moved_count',
    'reset_moved_count',
    'workflow_test',
]
