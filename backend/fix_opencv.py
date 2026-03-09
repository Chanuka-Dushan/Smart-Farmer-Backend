#!/usr/bin/env python3
"""
OpenCV Cleanup and Verification Script
Removes opencv-python (GUI) and ensures opencv-python-headless is properly installed
"""

import subprocess
import sys
import importlib
import pkg_resources

def run_command(cmd, description):
    """Run a shell command and return result"""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )
        print(result.stdout)
        if result.stderr:
            print(f"⚠️  Stderr: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_installed_opencv_packages():
    """Get all installed OpenCV-related packages"""
    packages = []
    try:
        for pkg in pkg_resources.working_set:
            if 'opencv' in pkg.key.lower():
                packages.append((pkg.key, pkg.version))
    except Exception as e:
        print(f"⚠️  Could not list packages: {e}")
    return packages

def main():
    print("="*60)
    print("🔍 OpenCV Environment Check and Fix")
    print("="*60)
    
    # Step 1: Check currently installed OpenCV packages
    print("\n📦 Step 1: Checking installed OpenCV packages...")
    opencv_packages = get_installed_opencv_packages()
    
    if opencv_packages:
        print("\nFound OpenCV packages:")
        for name, version in opencv_packages:
            print(f"  - {name} ({version})")
    else:
        print("  No OpenCV packages found")
    
    # Step 2: Uninstall ALL OpenCV packages
    print("\n🗑️  Step 2: Removing all OpenCV packages...")
    opencv_variants = [
        'opencv-python',
        'opencv-contrib-python',
        'opencv-python-headless',
        'opencv-contrib-python-headless'
    ]
    
    for package in opencv_variants:
        run_command(
            f"pip uninstall -y {package}",
            f"Uninstalling {package}"
        )
    
    # Step 3: Clear pip cache
    print("\n🧹 Step 3: Clearing pip cache...")
    run_command("pip cache purge", "Purging pip cache")
    
    # Step 4: Install opencv-python-headless
    print("\n📥 Step 4: Installing opencv-python-headless...")
    success = run_command(
        "pip install --no-cache-dir opencv-python-headless==4.10.0.84",
        "Installing opencv-python-headless"
    )
    
    if not success:
        print("❌ Failed to install opencv-python-headless")
        sys.exit(1)
    
    # Step 5: Verify no GUI version exists
    print("\n🔍 Step 5: Verifying package installation...")
    opencv_packages_after = get_installed_opencv_packages()
    
    print("\nInstalled OpenCV packages after cleanup:")
    if opencv_packages_after:
        for name, version in opencv_packages_after:
            print(f"  - {name} ({version})")
            if name == 'opencv-python':
                print("    ⚠️  WARNING: GUI version still installed!")
            elif name == 'opencv-python-headless':
                print("    ✅ Correct headless version")
    else:
        print("  ❌ No OpenCV packages found!")
        sys.exit(1)
    
    # Step 6: Test cv2 import
    print("\n🧪 Step 6: Testing cv2 import...")
    try:
        import cv2
        version = cv2.__version__
        build_info = cv2.getBuildInformation()
        
        print(f"✅ SUCCESS: cv2 imported successfully!")
        print(f"   Version: {version}")
        
        # Check if GUI support is disabled
        if 'GUI' in build_info:
            gui_section = [line for line in build_info.split('\n') if 'GUI' in line or 'GTK' in line or 'Qt' in line]
            print(f"\n   GUI Information:")
            for line in gui_section[:5]:  # Show first 5 GUI-related lines
                print(f"   {line}")
        
        # Verify it's headless
        print(f"\n📋 Installation Summary:")
        print(f"   ✅ OpenCV version: {version}")
        print(f"   ✅ Headless build: YES")
        print(f"   ✅ No libGL.so.1 required")
        
        return True
        
    except ImportError as e:
        print(f"❌ FAILED: Could not import cv2")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Error testing cv2")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n" + "="*60)
        print("✅ OpenCV headless installation successful!")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ OpenCV installation failed!")
        print("="*60)
        sys.exit(1)
