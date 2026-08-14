#!/usr/bin/env python3
"""
Waydroid Epic Seven TensorFlow Lite Crash Fixer
================================================
Fixes the SIGSEGV / Null Pointer Dereference crash in libtensorflowlite.so
occurring during chest opening, summoning, or drop animations in Waydroid (Houdini ARM64 translation).

Author: sr00t3d (ai powered)
License: Apache 2
"""

import os
import glob
import shutil
import subprocess
import sys
import argparse

# Signature of the crashing instruction sequence in tflite::CpuBackendContext::RuyHasAvxOrAbove
# 2e9204: fc1b0fe8 (str d8, [sp, #-0x50]!) -> patched to: d65f03c0 (ret)
TARGET_OFFSET = 0x2e9204
PATCH_BYTES = b"\xc0\x03\x5f\xd6"  # ret in AArch64 little-endian
ORIG_BYTES_CHECK = b"\xe8\x0f\x1b\xfc"  # str d8, [sp, #-0x50]!

POSSIBLE_APP_PATHS = [
    os.path.expanduser("~/.local/share/waydroid/data/app/~~*==/com.stove.epic7.google-*/lib/arm64/libtensorflowlite.so"),
    "/var/lib/waydroid/data/app/~~*==/com.stove.epic7.google-*/lib/arm64/libtensorflowlite.so",
]


def find_target_lib():
    for pattern in POSSIBLE_APP_PATHS:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None


def patch_file(file_path):
    print(f"[+] Target found: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"[!] Error: File {file_path} does not exist.")
        return False

    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    if len(data) <= TARGET_OFFSET + 4:
        print("[!] Error: File size is smaller than patch offset.")
        return False

    current_bytes = bytes(data[TARGET_OFFSET:TARGET_OFFSET+4])
    
    if current_bytes == PATCH_BYTES:
        print("[✓] Patch is already applied to this file!")
        return True

    # Create backup
    backup_path = file_path + ".orig"
    if not os.path.exists(backup_path):
        print(f"[+] Creating original backup at: {backup_path}")
        shutil.copy2(file_path, backup_path)
    else:
        print(f"[i] Existing backup found at: {backup_path}")

    # Apply patch
    data[TARGET_OFFSET:TARGET_OFFSET+4] = PATCH_BYTES

    with open(file_path, "wb") as f:
        f.write(data)

    try:
        os.chmod(file_path, 0o755)
    except Exception as e:
        print(f"[!] Warning updating permissions: {e}")

    print("[✓] Binary patch applied successfully!")
    return True


def restore_file(file_path):
    backup_path = file_path + ".orig"
    if not os.path.exists(backup_path):
        print(f"[!] Backup not found at {backup_path}")
        return False

    print(f"[+] Restoring backup from {backup_path} to {file_path}...")
    shutil.copy2(backup_path, file_path)
    os.chmod(file_path, 0o755)
    print("[✓] File restored to original state.")
    return True


def recompile_android_app():
    print("[+] Recompiling Android package cache via Waydroid...")
    try:
        subprocess.run(["sudo", "waydroid", "shell", "--", "am", "force-stop", "com.stove.epic7.google"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
        res = subprocess.run(["sudo", "waydroid", "shell", "--", "cmd", "package", "compile", "-m", "speed", "-f", "com.stove.epic7.google"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
        if res.returncode == 0:
            print("[✓] Epic Seven package recompiled successfully!")
        else:
            print("[i] Waydroid container is not running (compilation will happen at next launch).")
    except Exception:
        print("[i] Could not reach Waydroid shell.")


def main():
    parser = argparse.ArgumentParser(description="Fix Epic Seven TensorFlow Lite crash in Waydroid (ARM64 translation)")
    parser.add_argument("-p", "--path", help="Manual path to libtensorflowlite.so", default=None)
    parser.add_argument("-r", "--restore", action="store_true", help="Restore original file from .orig backup")
    args = parser.parse_args()

    target_path = args.path if args.path else find_target_lib()

    if not target_path:
        print("[!] Could not automatically find libtensorflowlite.so for Epic Seven.")
        print("[!] Specify the path manually using: -p /path/to/libtensorflowlite.so")
        sys.exit(1)

    if args.restore:
        success = restore_file(target_path)
    else:
        success = patch_file(target_path)

    if success:
        recompile_android_app()
        print("\n🎉 Done! You can now open Epic Seven in Waydroid without crashes.")


if __name__ == "__main__":
    main()
