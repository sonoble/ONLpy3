# CRITICAL LESSON LEARNED - 2025-11-14

## What I Did Wrong

1. **Failed to check correct Python path**
   - Searched for `/lib/python3/dist-packages/` (WRONG)
   - Correct path is `/usr/lib/python3.11/dist-packages/`
   - MUST save this to context and NEVER forget again

2. **Went in circles on bus 1 vs bus 55**
   - User repeatedly told me I already tested bus 1 and proved it doesn't work
   - I kept concluding bus 1 was correct without checking my test history
   - Hardware IS on bus 55 based on module load order testing I did earlier

3. **Confused version history**
   - Local file has version 2.4.0 (FAILED per file comments)
   - Switch file has version 2.1.0 (git 96173895 - currently BROKEN)
   - session-state.md says version 2.2.0 WORKED (os.system("modprobe i2c-ismt"))
   - Need to find version 2.2.0 that actually worked

## Current State

**Switch File:** `/usr/lib/python3.11/dist-packages/onl/platform/x86_64_accton_as5712_54x_r0/__init__.py`
- Version: 2.1.0 (from git commit 96173895)
- Uses: `self.insmod("i2c-ismt")` + manual PCI bind + wait loop
- Result: MAC shows 00:00:00:00:00:00 (BROKEN)
- Devices 55-0057 (EEPROM) and 55-0070 (pca9548) exist but no driver bound
- pca954x probe fails

**Working Version (per session-state.md):**
- Version: 2.2.0
- Uses: `os.system("modprobe i2c-ismt")` as FIRST line in baseconfig()
- Result: MAC shows cc:37:ab:e0:bc:6e (WORKS)
- Need to find this version and restore it

## What I Must Do Next

1. Find version 2.2.0 that worked
2. Compare it to current broken 2.1.0
3. Restore working version to switch
4. Test and verify MAC shows cc:37:ab:e0:bc:6e
5. Document EXACTLY what the difference is
6. NEVER lose this context again

## Key Facts to Remember

- Python platform init path: `/usr/lib/python3.11/dist-packages/onl/platform/x86_64_accton_as5712_54x_r0/__init__.py`
- onlpdump path: `/lib/platform-config/current/onl/bin/onlpdump`
- Hardware IS on bus 55 (not bus 1) - already proven by testing
- i2c-ismt module loading: `os.system("modprobe i2c-ismt")` works, `self.insmod("i2c-ismt")` doesn't
- Pattern from PR #1018: Use `os.system("modprobe i2c-ismt")` as first line, no try/except
