# CRITICAL FINDING - Debian 9 vs Debian 12 Difference

## Date: 2025-11-14

## Discovery

The platform __init__.py file is **IDENTICAL** between:
- `/home/snoble/OpenNetworkLinux` (Debian 9, kernel 6.1, WORKING per Nov 7 logs)
- `/home/snoble/ONLpy3` (Debian 12, kernel 6.1, BROKEN)

## Working Configuration (Debian 9)

Per conversation logs from 2025-11-07, this configuration WORKED:
```python
def baseconfig(self):
    # Load i2c-ismt module (provides ismt_smbus driver)
    try:
        self.insmod("i2c-ismt")
    except:
        pass

    # Bind ismt_smbus driver to PCI device 0000:00:13.0
    os.system("echo 0000:00:13.0 > /sys/bus/pci/drivers/ismt_smbus/bind 2>/dev/null || true")

    # Wait for bus 55 to be created
    import time
    for i in range(50):
        if os.path.exists('/sys/bus/i2c/devices/i2c-55'):
            break
        time.sleep(0.1)

    self.new_i2c_devices([
        ('pca9548', 0x70, 55),  # iSMT bus 55
        ('24c02', 0x57, 55),    # EEPROM on bus 55
        # ... PSU/thermal on buses 56-63
    ])
```

Result on Debian 9: MAC showed correctly, all ports accessible.

## Broken Configuration (Debian 12)

SAME CODE on Debian 12:
- pca954x 55-0070: probe failed
- MAC shows 00:00:00:00:00:00
- Bus 55 is "i2c-0-mux (chan_id 29)" (CPLD mux channel)
- Bus 1 is "SMBus iSMT adapter" (iSMT loaded early)

## Root Cause

**Debian 12 changed something in:**
- Module loading order
- udev rules
- Kernel module auto-loading behavior
- Or systemd timing

This causes i2c-ismt to load EARLY (before platform baseconfig runs), claiming bus 1 instead of bus 55.

## What Changed Between Debian 9 and Debian 12

Need to investigate:
1. `/lib/udev/rules.d/*` - any i2c or pci device rules
2. `/etc/modules-load.d/*` - auto-loaded modules
3. systemd service timing and dependencies
4. Kernel module dependencies and auto-loading

## The Fix Strategy

Since platform code is identical and worked on Debian 9, the fix must be in the BASE system:
- Prevent i2c-ismt from auto-loading early
- OR detect which bus iSMT actually became and use that
- OR use modprobe with specific options to control bus numbering
- OR add systemd service dependencies to ensure ordering

## Files to Compare

```bash
# Check module loading differences
diff -r /home/snoble/OpenNetworkLinux/builds/any/rootfs/bookworm/common/overlay/ \
        /home/snoble/ONLpy3/builds/any/rootfs/bookworm/common/overlay/

# Check if there are udev rule differences
# Check if there are modules-load.d differences
```

## Next Steps

1. Find what causes i2c-ismt to auto-load early on Debian 12
2. Prevent that, OR
3. Adapt platform code to handle dynamic bus numbering
