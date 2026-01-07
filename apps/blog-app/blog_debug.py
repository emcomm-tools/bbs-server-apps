#!/usr/bin/env python3
"""
Debug wrapper for blog.py - shows what's happening when run from BBS
"""

import sys
import os

print("=" * 70)
print("BLOG DEBUG INFO")
print("=" * 70)
print()
print(f"Current working directory: {os.getcwd()}")
print(f"__file__ value: {__file__}")
print(f"Absolute __file__: {os.path.abspath(__file__)}")
print(f"Script directory: {os.path.dirname(os.path.abspath(__file__))}")
print()
print(f"sys.path:")
for i, p in enumerate(sys.path):
    print(f"  [{i}] {p}")
print()
print(f"Does lib/ exist in cwd? {os.path.exists('lib')}")
print(f"Does lib/ exist in script dir? {os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib'))}")
print()

# Try to change to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
print(f"Changing to: {script_dir}")
os.chdir(script_dir)
print(f"New working directory: {os.getcwd()}")
print(f"Does lib/ exist now? {os.path.exists('lib')}")
print()

# Check what's in lib if it exists
if os.path.exists('lib'):
    print("Contents of lib/:")
    for item in os.listdir('lib'):
        print(f"  • {item}")
    print()
else:
    print("ERROR: lib/ directory not found!")
    print()

print("Attempting import...")
sys.path.insert(0, script_dir)

try:
    from lib.database import BlogDatabase
    print("✓ Import successful!")
except Exception as e:
    print(f"✗ Import failed: {e}")
    print()
    print("Python is looking in these locations:")
    import importlib.util
    for path in sys.path:
        lib_path = os.path.join(path, 'lib')
        print(f"  {lib_path} - Exists: {os.path.exists(lib_path)}")

print()
print("=" * 70)
