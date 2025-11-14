# Test Plan: Debian 9 vs Debian 12 Comparison

## Test: Load Debian 9 + Kernel 6.1 onto switch

**Purpose:** Confirm that the SAME platform code works on Debian 9 but fails on Debian 12

## After Loading Debian 9 Image

### 1. Basic Verification
```bash
onlpdump -s
# Expected: MAC shows cc:37:ab:e0:bc:6e

cat /etc/debian_version
# Expected: 9.x (stretch)

uname -r
# Expected: 6.1.x-OpenNetworkLinux
```

### 2. Check I2C Bus Layout
```bash
ls /sys/bus/i2c/devices/ | grep "^i2c-" | sort -V
# Note which buses exist

cat /sys/bus/i2c/devices/i2c-1/name
cat /sys/bus/i2c/devices/i2c-55/name
# Confirm which is iSMT adapter
```

### 3. Check Module Loading
```bash
lsmod | grep i2c
# Check i2c_ismt position in list

dmesg | grep -E "i2c-ismt|ismt_smbus" | head -20
# Check when module loaded
```

### 4. Check Platform Init File
```bash
cat /usr/lib/python3.11/dist-packages/onl/platform/x86_64_accton_as5712_54x_r0/__init__.py | head -80
# OR
cat /usr/lib/python2.7/dist-packages/onl/platform/x86_64_accton_as5712_54x_r0/__init__.py | head -80
# Verify it's the same code
```

### 5. Capture System Configuration Files
```bash
# Check for module loading configs
ls -la /etc/modules-load.d/
cat /etc/modules-load.d/* 2>/dev/null

# Check udev rules
ls -la /lib/udev/rules.d/ | grep i2c
cat /lib/udev/rules.d/*i2c* 2>/dev/null

# Check modprobe configs
ls -la /etc/modprobe.d/
cat /etc/modprobe.d/* 2>/dev/null
```

## Expected Result

If Debian 9 works with same platform code:
- MAC shows cc:37:ab:e0:bc:6e ✅
- Bus 55 is iSMT adapter
- pca9548 probe succeeds
- All ports accessible

This confirms the issue is Debian version specific, not platform code.

## If It Fails on Debian 9 Too

Then the issue is NOT Debian version - it's something else (kernel 6.1 specific, hardware issue, etc.)
