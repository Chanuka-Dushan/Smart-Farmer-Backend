#!/usr/bin/env python3
"""
Pre-import script to fix OpenCV installation at runtime.
This is a 'nuclear' fix for headless environments like DigitalOcean Buildpacks.
"""
import subprocess
import sys
import os

def fix_opencv():
    print("🔧 [PRELOAD] Starting OpenCV environment repair...", file=sys.stderr, flush=True)
    
    # 1. Check if cv2 is already working
    try:
        import cv2
        print(f"✅ [PRELOAD] OpenCV is already working (v{cv2.__version__})", file=sys.stderr, flush=True)
        return True
    except ImportError as e:
        error_msg = str(e)
        print(f"⚠️  [PRELOAD] OpenCV import failed: {error_msg}", file=sys.stderr, flush=True)
        
        # If it's the libGL error, we must fix it
        if "libGL.so.1" in error_msg or "libgthread-2.0.so.0" in error_msg:
            print("🚨 [PRELOAD] libGL/GUI dependency detected. Reinstalling headless version...", file=sys.stderr, flush=True)
            
            try:
                # Uninstall ALL possible opencv versions
                print("🗑️  [PRELOAD] Uninstalling conflicting packages...", file=sys.stderr, flush=True)
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'uninstall', '-y', 'opencv-python', 'opencv-contrib-python', 'opencv-python-headless', 'opencv-contrib-python-headless'],
                    capture_output=True,
                    check=False
                )
                
                # Install ONLY headless
                print("📥 [PRELOAD] Installing opencv-python-headless...", file=sys.stderr, flush=True)
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'opencv-python-headless==4.10.0.84'],
                    capture_output=True,
                    check=True
                )
                
                # Verify again
                import cv2
                print(f"✅ [PRELOAD] Repair successful! OpenCV v{cv2.__version__} is now ready.", file=sys.stderr, flush=True)
                return True
            except Exception as repair_error:
                print(f"❌ [PRELOAD] Repair failed: {repair_error}", file=sys.stderr, flush=True)
                return False
        else:
            # Other import error, try to install headless anyway
            print("📦 [PRELOAD] Attempting fresh install of headless...", file=sys.stderr, flush=True)
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'opencv-python-headless'], capture_output=True)
                return True
            except:
                return False
    except Exception as e:
        print(f"❌ [PRELOAD] Unexpected error: {e}", file=sys.stderr, flush=True)
        return False

if __name__ == '__main__':
    fix_opencv()
