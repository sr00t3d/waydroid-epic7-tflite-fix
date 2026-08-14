# Waydroid Epic Seven TensorFlow Lite Crash Fix

A surgical binary patch that fixes the game-crashing **SIGSEGV / Null Pointer Dereference** in **Epic Seven** (`com.stove.epic7.google`) when running under **Waydroid** with ARM64 translation (`libhoudini`).

---

## 🔍 The Root Cause

When opening chests, summoning heroes, or processing drop tables, Epic Seven calls **TensorFlow Lite (`libtensorflowlite.so`)** via its internal neural network matrix acceleration library (*Ruy*).

On real physical ARM devices (Snapdragon, MediaTek), *Ruy* queries hardware microarchitecture registers. However, when running inside **Waydroid x86_64** under binary translators (like Intel **Houdini** or Box64/FEX), this query returns `NULL`.

Because the function lacks a null-check:
```arm64
0x2e92e4: bl  0x2e9e3c
0x2e92e8: ldr x9, [x0, #0x8]   <-- x0 is NULL -> Dereferences 0x8 -> SIGSEGV crash!
```
The Linux kernel instantly terminates the game with `SEGV_MAPERR`.

---

## ⚡ The Solution

This tool patches the hardware detection routine `tflite::CpuBackendContext::RuyHasAvxOrAbove` inside `libtensorflowlite.so` (`offset 0x2e9204`) with an immediate return instruction (`ret` / `0xd65f03c0`). 

This bypasses the faulty pointer dereference safely, allowing the game engine to render chest openings, summonings, and drops without crashing!

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/your-username/waydroid-epic7-tflite-fix.git
cd waydroid-epic7-tflite-fix
```

### 2. Run the Patcher
Make sure Waydroid is running (or has Epic Seven installed):
```bash
python3 patch_epic7.py
```
*The script will automatically locate your Waydroid app directory, back up the original library to `.orig`, apply the patch, and recompile the Android package cache.*

---

## 🔄 How to Restore (Undo Patch)

To revert the patch back to the original unmodified `.so` file:
```bash
python3 patch_epic7.py --restore
```

---

## 🛠️ Manual Patching (Alternative)

If you prefer patching manually using Python:
```python
path = "/path/to/com.stove.epic7.google/lib/arm64/libtensorflowlite.so"
with open(path, "rb") as f:
    data = bytearray(f.read())

# Patch offset 0x2e9204 with AArch64 'ret' (0xd65f03c0)
data[0x2e9204:0x2e9208] = b"\xc0\x03\x5f\xd6"

with open(path, "wb") as f:
    f.write(data)
```
