"""
Wikipedia ZIM Reader Package
A modular interface for reading Wikipedia ZIM files offline
"""

from .zim_reader import WikiZimReader
from .console_interface import WikiConsoleInterface
from .config import load_config, validate_zim_files, display_zim_menu, create_example_config

__version__ = "1.1.0"
__author__ = "VA2GWM"

__all__ = [
    'WikiZimReader',
    'WikiConsoleInterface', 
    'load_config',
    'validate_zim_files',
    'display_zim_menu',
    'create_example_config'
]
