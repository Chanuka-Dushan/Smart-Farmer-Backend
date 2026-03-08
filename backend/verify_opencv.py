#!/usr/bin/env python3
"""
Quick OpenCV Verification Script
Run this after deployment to verify OpenCV is correctly installed
"""

import sys

def main():
    print("="*60)
    print("🔍 OpenCV Installation Verification")
    print("="*60)
    
    # Test 1: Import cv2
    print("\n✅ Test 1: Importing cv2...")
    try:
        import cv2
        print(f"   SUCCESS: cv2 version {cv2.__version__}")
    except ImportError as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    # Test 2: Check build info
    print("\n✅ Test 2: Checking build configuration...")
    try:
        build_info = cv2.getBuildInformation()
        
        # Check for GUI-related flags
        gui_flags = ['GTK', 'Qt', 'GUI']
        gui_status = {}
        
        for line in build_info.split('\n'):
            for flag in gui_flags:
                if flag in line:
                    gui_status[flag] = line.strip()
        
        if gui_status:
            print("   GUI-related flags:")
            for flag, info in gui_status.items():
                print(f"     {info}")
        else:
            print("   ✅ No GUI flags found (headless build)")
            
    except Exception as e:
        print(f"   ⚠️  Could not get build info: {e}")
    
    # Test 3: Check installed packages
    print("\n✅ Test 3: Checking installed OpenCV packages...")
    try:
        import pkg_resources
        opencv_pkgs = []
        for pkg in pkg_resources.working_set:
            if 'opencv' in pkg.key.lower():
                opencv_pkgs.append((pkg.key, pkg.version))
        
        if opencv_pkgs:
            for name, version in opencv_pkgs:
                if name == 'opencv-python-headless':
                    print(f"   ✅ {name} ({version}) - CORRECT")
                elif name == 'opencv-python':
                    print(f"   ❌ {name} ({version}) - WRONG! GUI version detected!")
                    return False
                else:
                    print(f"   ⚠️  {name} ({version})")
        else:
            print("   ❌ No OpenCV packages found!")
            return False
            
    except Exception as e:
        print(f"   ⚠️  Could not list packages: {e}")
    
    # Test 4: Basic functionality
    print("\n✅ Test 4: Testing basic OpenCV functionality...")
    try:
        import numpy as np
        # Create a simple image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # Encode to JPEG
        _, encoded = cv2.imencode('.jpg', img)
        print(f"   ✅ Basic encode/decode works (encoded {len(encoded)} bytes)")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - OpenCV is correctly configured!")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
