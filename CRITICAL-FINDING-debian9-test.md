# CRITICAL TEST RESULT - Debian 9 vs Debian 12

## Date: 2025-11-14

## System Info
- Debian: 9.13 (Stretch)
- Kernel: 6.1.107-OpenNetworkLinux
- Python: 2.7.13

## Bus Layout on Debian 9
- Bus 1: "i2c-0-mux (chan_id 0)" (CPLD mux channel)
- Bus 55: "SMBus iSMT adapter at dff87000" (iSMT adapter)

## Test Results

### First Boot
❌ EEPROM NOT accessible
- User had to manually run `/etc/boot.d/boot` again

### After Manual /etc/boot.d/boot
✅ EEPROM accessible
- onlpdump -s shows MAC: cc:37:ab:e0:bc:6e

## KEY FINDING

**Even on Debian 9, there is a TIMING ISSUE at boot time!**

The platform init runs during boot but something is not ready yet. Running the SAME boot script AGAIN makes it work.

## Comparison: Debian 9 vs Debian 12

| Aspect | Debian 9 | Debian 12 |
|--------|----------|-----------|
| **iSMT bus number** | Bus 55 | Bus 1 |
| **CPLD mux start** | Bus 1 | Bus 2 |
| **First boot works?** | ❌ NO | ❌ NO |
| **After manual run?** | ✅ YES | Need to test |

## This Changes Everything

The issue is NOT Debian 9 vs 12 difference in bus numbering!

The issue is TIMING - something is not ready when platform init runs at boot.

## What's Different Second Time?

When `/etc/boot.d/boot` runs the second time, what has changed?
1. More time has passed (hardware settled?)
2. Some other service started?
3. Module loading completed?
4. Driver binding completed?

## Next Investigation

Need to check Debian 12 - does running `/etc/boot.d/boot` AGAIN also fix it?

If yes, then the fix is to:
1. Add delay before platform init, OR
2. Change when platform init runs (later in boot), OR
3. Add proper dependencies/waits in platform init
