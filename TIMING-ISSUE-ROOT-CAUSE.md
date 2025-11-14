# ROOT CAUSE: Timing Issue with i2c-ismt Module Loading

## Date: 2025-11-14

## Problem Statement

EEPROM is not accessible on first boot (MAC shows 00:00:00:00:00:00), but works after manually running `/etc/boot.d/boot` a second time.

This affects BOTH Debian 9 and Debian 12 with kernel 6.1.

## Root Cause Analysis

### The Code Path

1. Boot process calls `/etc/boot.d/boot`
2. Which calls `/etc/boot.d/51.onl-platform-baseconf`
3. Which imports `from onl.platform.baseconfig import baseconfig` and calls `baseconfig()`
4. Which calls the platform-specific `__init__.py` `baseconfig()` method
5. Platform baseconfig tries to load i2c-ismt:

```python
try:
    self.insmod("i2c-ismt")
except:
    pass
```

### What `self.insmod()` Does

From `/home/snoble/ONLpy3/packages/base/all/vendor-config-onl/src/python/onl/platform/base.py:195-242`:

```python
def insmod(self, module, required=True, params={}):
    # Searches for module in multiple directories
    searchdirs = [ ... ]

    for d in searchdirs:
        for e in [ ".ko", "" ]:
            path = os.path.join(d, "%s%s" % (module, e))
            if os.path.exists(path):
                cmd = "insmod %s %s" % (path, ...)
                subprocess.check_call(cmd, shell=True)  # <-- Throws exception on failure
                return True

    if required:
        raise RuntimeError("kernel module %s could not be found...")
    else:
        return False
```

The problem:
1. `subprocess.check_call()` throws an exception if the command fails
2. The platform code wraps `self.insmod("i2c-ismt")` in try/except that SILENTLY SWALLOWS errors
3. If module loading fails for ANY reason, execution continues WITHOUT the module

### Why It Fails on First Boot

During first boot, `self.insmod("i2c-ismt")` likely:

**Option A:** Finds the .ko file but `insmod` command fails because:
- Module not ready yet (filesystem caching, module signing verification, etc.)
- Or some transient condition that resolves after system settles

**Option B:** Doesn't find the .ko file because:
- Search path timing issue
- Or `i2c-ismt.ko` is NOT in the ONL-specific directories - it's in kernel core drivers

Most likely: **i2c-ismt.ko is in `/lib/modules/6.1.107-OpenNetworkLinux/kernel/drivers/i2c/busses/` which is searched LAST**, and something about the search fails transiently.

### Evidence from Switch Testing

**First boot (timestamp ~20 seconds):**
- Last device created: bus 54 (QSFP port)
- NO messages about i2c-ismt in dmesg
- NO bus 55 created
- NO devices on bus 55

**Manual run (timestamp ~400 seconds):**
- i2c-ismt loads successfully
- Bus 55 appears
- All devices created on bus 55
- EEPROM readable

Between timestamp 20 and 400 seconds, the system "settled" and whatever prevented the first load no longer applies.

## The Fix: Use `modprobe` Instead of `insmod`

### Why modprobe Works Better

1. **modprobe** handles dependencies automatically
2. **modprobe** searches standard kernel module paths
3. **modprobe** is more robust for core kernel drivers like i2c-ismt
4. **modprobe** doesn't fail if module is already loaded (idempotent)

### Pattern from Accton PR #1018

Other platforms migrated to kernel 6.1 use this pattern:

```python
def baseconfig(self):
    os.system("modprobe i2c-ismt")  # First line, no try/except
    # ... rest of initialization
```

This approach:
- Runs before ANY other module loading
- Uses `os.system()` which returns exit code but doesn't throw exceptions
- Doesn't wrap in try/except that swallows errors
- Works reliably

## Recommended Solution

Replace:
```python
try:
    self.insmod("i2c-ismt")
except:
    pass
```

With:
```python
os.system("modprobe i2c-ismt")
```

And move it to the FIRST line of `baseconfig()`, matching the PR #1018 pattern.

## Alternative: Add Retry Logic

If we keep the current approach, add retry with delay:

```python
import time
for attempt in range(5):
    try:
        self.insmod("i2c-ismt")
        break
    except:
        if attempt < 4:
            time.sleep(1)
        else:
            raise RuntimeError("Failed to load i2c-ismt after 5 attempts")
```

But this is less elegant than just using modprobe.
