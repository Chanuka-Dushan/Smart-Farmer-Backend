#!/usr/bin/env python3
"""
Pre-import script to fix OpenCV installation before any Python imports
Run this BEFORE importing any modules that use opencv
"""
import subprocess
import sys

def fix_opencv():
    """Remove opencv-python and ensure only opencv-python-headless is installed"""
    print("🔧 [PRELOAD] Checking OpenCV installation...", file=sys.stderr, flush=True)
    
    try:
        # Get list of installed packages
        result = subprocess.run(
            ['pip', 'list', '--format=freeze'],
            capture_output=True,
            text=True,
            check=True
        )
        
        packages = result.stdout.lower()
        has_opencv_gui = 'opencv-python==' in packages and 'opencv-python-headless' not in packages.replace('opencv-python==', '')
        has_opencv_headless = 'opencv-python-headless==' in packages
        
        print(f"🔍 [PRELOAD] OpenCV GUI: {has_opencv_gui}, Headless: {has_opencv_headless}", file=sys.stderr, flush=True)
        
        if has_opencv_gui:
            print("⚠️  [PRELOAD] Removing opencv-python (GUI version)...", file=sys.stderr, flush=True)
            subprocess.run(
                ['pip', 'uninstall', '-y', 'opencv-python', 'opencv-contrib-python'],
                capture_output=True,
                check=False
            )
            print("✅ [PRELOAD] opencv-python removed", file=sys.stderr, flush=True)
        
        if not has_opencv_headless:
            print("📦 [PRELOAD] Installing opencv-python-headless...", file=sys.stderr, flush=True)
            subprocess.run(
                ['pip', 'install', '--no-cache-dir', 'opencv-python-headless>=4.8.0'],
                capture_output=True,
                check=True
            )
            print("✅ [PRELOAD] opencv-python-headless installed", file=sys.stderr, flush=True)
        
        print("✅ [PRELOAD] OpenCV configuration verified", file=sys.stderr, flush=True)
        return True
        
    except Exception as e:
        print(f"❌ [PRELOAD] Failed to fix OpenCV: {e}", file=sys.stderr, flush=True)
        return False

if __name__ == '__main__':
    fix_opencv()
