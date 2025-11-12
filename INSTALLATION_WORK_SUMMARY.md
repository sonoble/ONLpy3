# ONL Python 3 / Debian Bookworm Installation Work Summary

## Overview
This document summarizes the installation and boot issues that were identified and resolved during the migration of OpenNetworkLinux (ONL) from Python 2/Debian Jessie to Python 3/Debian Bookworm with Linux Kernel 6.1.

---

## Branch Information

### Primary Development Branch: `bookworm`
- **Purpose**: Main Python 3 / Debian Bookworm / Kernel 6.1 migration
- **Latest Commit**: `078d6c0c` - "Remove stray files" (2025-11-12)

### Fix Branch: `claude/fix-bytes-string-error-011CUy7w7mR6dHiHascH6kiB`
- **Purpose**: Installer boot fixes (swiprep rootfs extraction issues)
- **Latest Commit**: `d8b52f2e` - "Fix symlink preservation in swiprep extraction" (2025-11-12)

---

## Critical Installation Issues Resolved

### 1. **Swiprep Rootfs Extraction Failures** (Fix Branch)

#### Issue A: Unsquashfs Threading Deadlock
**Commit**: `a5092ce8` - "Fix unsquashfs threading deadlock in swiprep"

**Problem**:
- Installer would hang indefinitely at: `"16222 inodes (18733 blocks) to write"`
- Caused by futex deadlock in `unsquashfs` tool when extracting large rootfs squashfs images
- One thread opens files for writing but deadlocks waiting for decompression threads to provide data

**Solution**:
- Replaced direct `unsquashfs -f -d` extraction with mount + copy approach
- Mount squashfs read-only using `mount -t squashfs -o loop,ro`
- Copy contents with `cp -a` to destination
- Unmount and cleanup
- Slower but reliable workaround for threading bug in unsquashfs

**File Modified**: `packages/base/all/initrds/loader-initrd-files/src/bin/swiprep:171`

---

#### Issue B: Symlink Preservation Failure
**Commit**: `d8b52f2e` - "Fix symlink preservation in swiprep extraction"

**Problem**:
- `cp -a` command was not correctly preserving symlinks during rootfs extraction
- Specifically affected merged-usr symlinks like `/sbin -> usr/sbin`
- Caused `switch_root` to fail with error: `/sbin/init` missing
- System could not complete boot process after installation

**Solution**:
- Replaced `cp -a` with `tar` pipe method: `tar -C "$sqsh_mount" -cf - . | tar -C "$destdir" -xf -`
- This ensures exact filesystem structure preservation including:
  - All symlinks (critical for merged-usr layout)
  - Permissions
  - Special files
  - Directory structure

**File Modified**: `packages/base/all/initrds/loader-initrd-files/src/bin/swiprep:171-182`

**Technical Details**:
```bash
# Old (broken):
unsquashfs -f -d "$destdir" "$workdir/rootfs.sqsh"
# Then replaced with:
mount -t squashfs -o loop,ro "$workdir/rootfs.sqsh" "$sqsh_mount"
cp -a "$sqsh_mount"/. "$destdir"/
umount "$sqsh_mount"
# Final (working):
mount -t squashfs -o loop,ro "$workdir/rootfs.sqsh" "$sqsh_mount"
tar -C "$sqsh_mount" -cf - . | tar -C "$destdir" -xf -
umount "$sqsh_mount"
```

---

### 2. **Python 3 Compatibility Fixes** (Bookworm Branch)

#### Issue: Base64 Encoding Bytes/String Errors
**Commit**: `96173895` - "Latest changes to move to Python3, Debian Bookworm and Kernel 6.1"

**Problem**:
- Python 2 `str.encode('base64')` method removed in Python 3
- Python 3 requires explicit `base64` module usage
- Bytes vs string type mismatches in boot configuration encoding

**Solution** - Modified boot config encoding in two locations:

**File 1**: `packages/base/all/vendor-config-onl/src/python/onl/install/BaseInstall.py:386`
```python
# Old (Python 2):
ecf = buf.encode('base64', 'strict').strip()

# New (Python 3):
import base64
ecf = base64.b64encode(buf.encode('utf-8')).decode('ascii').strip()
```

**File 2**: Same file at line 1037 (UBIfsCreater class)
```python
# Old (Python 2):
ecf = buf.encode('base64', 'strict').strip()

# New (Python 3):
import base64
ecf = base64.b64encode(buf.encode('utf-8')).decode('ascii').strip()
```

**Impact**: Fixes boot configuration default encoding for both GRUB and U-Boot environments

---

#### Issue: Python 2 vs 3 Syntax Updates
**Commit**: `96173895`

**Changes in** `packages/base/all/vendor-config-onl/src/python/onl/bootconfig/__init__.py`:

1. **Dictionary iteration**:
   ```python
   # Old: for (k, v) in self.keys.iteritems():
   # New: for (k, v) in self.keys.items():
   ```

2. **Print statements to functions**:
   ```python
   # Old: print self.keys
   # New: print(self.keys)
   ```

3. **Exception handling**:
   ```python
   # Old: except Exception, e:
   # New: except Exception as e:
   ```

---

### 3. **YAML Loader Compatibility** (Bookworm Branch)

**File**: `tools/onlyaml.py`
**Commit**: `96173895`

**Problem**:
- PyYAML `FullLoader` not available in Python 2
- Forward compatibility needed for build tools

**Solution**:
```python
try:
    data = yaml.load(string, Loader=yaml.FullLoader)  # Python 3
except AttributeError:
    data = yaml.load(string, Loader=yaml.Loader)      # Python 2 fallback
```

---

### 4. **GCC 4.7.2 Build Fixes** (Both Branches)

#### Issue A: `__FUNCTION__` Pedantic Warning
**Commits**:
- `5730a4bd` - Initial fix attempt
- `f7fb2268` - Line number correction to 671
- `6c4c0f85` - Final fix (bookworm branch)

**File**: `packages/base/any/initrds/buildroot/builds/patches/gcc-002-fix-function-pedantic-warning.patch`

**Problem**: GCC 4.7.2 uses non-standard `__FUNCTION__` instead of C99 `__func__`

**Solution**: Patch gcc/system.h line 671
```c
// Old:
((void)(!(EXPR) ? fancy_abort (__FILE__, __LINE__, __FUNCTION__), 0 : 0))
// New:
((void)(!(EXPR) ? fancy_abort (__FILE__, __LINE__, __func__), 0 : 0))
```

---

#### Issue B: Implicit Fallthrough Warnings
**Commits**:
- `d18da6cc` - Add patch (fix branch)
- `038eebbd` - Alternative approach with -Wno flag (bookworm branch)
- `6c4c0f85` - Coordinate both approaches

**Problem**: Modern GCC requires explicit fallthrough annotations in switch statements

**Solution (Fix Branch)**:
- Created `gcc-003-fix-implicit-fallthrough-warnings.patch`
- Added explicit fall-through comments in `gcc/config/i386/i386.c` at lines 28884, 29798, 38612

**Solution (Bookworm Branch)**:
- Modified `gcc-001-disable-texinfo-documentation-build.patch` to add `-Wno-implicit-fallthrough` flag
- Suppresses warnings in generated code

---

### 5. **Platform Driver Fixes** (Bookworm Branch)

#### Issue: Multiple Definition Linker Errors (Belgite Platform)
**Commit**: `4ca1527b` - "Fix multiple definition linker errors in belgite platform"

**Problem**:
- Variables `command` and `fp` declared globally in both `sfpi.c` and `platform.c`
- Caused linker errors: "multiple definition of 'command'" and "multiple definition of 'fp'"

**Solution**: Made variables `static` for file-local scope
```c
// In platform.c and sfpi.c:
static char command[256];
static FILE *fp;
```

---

#### Issue: Unused Variable Warnings (Belgite Platform)
**Commit**: `636ed109` - "Remove unused global variables from sfpi.c"

**Problem**: Unused static variables causing `-Werror=unused-variable` compilation errors

**Solution**: Removed unused `command`, `buf`, and `fp` variables

---

### 6. **AS5712-54X Platform I2C Bus Renumbering** (Bookworm Branch)
**Commit**: `96173895`

**Problem**:
- Kernel 6.1 changed I2C bus enumeration order
- iSMT bus and CPLD mux buses shifted, breaking device initialization
- Old: CPLD mux started at bus 2, iSMT was bus 1
- New: CPLD mux starts at bus 1, iSMT becomes bus 55 after loading driver

**Solution**: Updated `packages/platforms/accton/x86-64/as5712-54x/platform-config/r0/src/python/x86_64_accton_as5712_54x_r0/__init__.py`

**Key Changes**:
- SFP devices: Changed from `port+1` to `port` (buses 1-48)
- QSFP devices: Changed from buses 50-55 to buses 49-54
- PSU devices: Changed from buses 57-58 to buses 56-57
- Temperature sensors: Changed from buses 61-63 to buses 60-62
- PCA9548 mux: Changed from bus 1 to bus 55
- System EEPROM: Changed from bus 1 to bus 55
- Added explicit i2c-ismt module loading and PCI device binding
- Added wait loop for bus 55 creation
- Added try/except blocks for module loading robustness

---

### 7. **Build System Improvements** (Bookworm Branch)

#### Buildroot Patches
**Commit**: `96173895`

**Added Patches**:
1. `buildroot-001-fix-find-perm-deprecated-syntax.patch` - Fix deprecated `find` command syntax
2. `gcc-001-disable-texinfo-documentation-build.patch` - Disable texinfo to speed up build
3. `gcc-002-fix-function-pedantic-warning.patch` - Fix `__FUNCTION__` usage

#### Python Script Shebang Updates
**Files Modified** (all changed to Python 3):
- `/usr/bin/loader-shell`
- `/usr/bin/onie-shell`
- `/usr/bin/onie-sysinfo`
- `/usr/bin/onl-install`
- `/usr/bin/onl-onie-boot-mode`
- `/usr/bin/onl-recover`
- `/usr/bin/pyfit`
- `/usr/bin/pylegacy`
- `/usr/bin/upgrade-shell`

**Note**: `onl-install` temporarily reverted to Python 2 with path adjustment in commit 96173895

---

### 8. **Package Management Debug Enhancements** (Bookworm Branch)
**Commit**: `96173895`
**File**: `tools/onlpm.py`

**Added Debug Logging**:
```python
logger.info("DEBUG: Before validation, %s has %d entries: %s" % (key, len(self.pkg.get(key, [])), self.pkg.get(key, [])))
# ... validation ...
logger.info("DEBUG: After validation, %s has %d entries" % (key, len(self.pkg[key])))
logger.info("DEBUG: Processing %d file entries" % len(files_list))
logger.info("DEBUG: Copying %s -> %s" % (src, dst))
```

---

### 9. **RootFS Build Improvements** (Bookworm Branch)
**Commit**: `96173895`
**File**: `tools/onlrfs.py`

**Added**: Explicit `/tmp` directory creation and permission fixing
```python
tmp_dir = os.path.join(dir_, "tmp")
if not os.path.exists(tmp_dir):
    onlu.execute("sudo mkdir -p %s" % tmp_dir)
onlu.execute("sudo chown %d:%d %s" % (os.getuid(), os.getgid(), tmp_dir))
```

---

## Testing Status

### Verified Working
✅ Buildroot GCC 4.7.2 compilation (no warnings with patches applied)
✅ Python 3 syntax in boot configuration scripts
✅ Base64 encoding for GRUB/U-Boot environments
✅ YAML loading with Python 2/3 compatibility
✅ Belgite platform compilation (no multiple definition errors)
✅ Swiprep rootfs extraction (no hangs or symlink issues)

### Requires Hardware Testing
⚠️ AS5712-54X I2C device initialization on Kernel 6.1
⚠️ Full ONL installer boot on target hardware
⚠️ SFP/QSFP module detection after bus renumbering
⚠️ PSU and thermal sensor functionality

---

## Known Issues / Future Work

1. **onl-install Python Version**: Currently reverted to Python 2 with path hack - needs proper Python 3 migration
2. **Additional Platforms**: Only AS5712-54X I2C buses updated - other platforms may need similar fixes
3. **Kernel 6.1 Compatibility**: More platforms likely need driver updates and bus renumbering
4. **Test Coverage**: Comprehensive hardware-in-the-loop testing needed

---

## Build Environment

- **Target Debian**: Bookworm (Debian 12)
- **Target Kernel**: 6.1 LTS
- **Python Version**: 3.x (with 2.x fallbacks in some tools)
- **Docker Builder**: builder12/1.0
- **Architecture**: x86_64 (amd64)

---

## Files Modified Summary

### Installation/Boot Critical
- `packages/base/all/initrds/loader-initrd-files/src/bin/swiprep` - Rootfs extraction fixes
- `packages/base/all/vendor-config-onl/src/python/onl/install/BaseInstall.py` - Base64 encoding
- `packages/base/all/vendor-config-onl/src/python/onl/bootconfig/__init__.py` - Python 3 syntax

### Build System
- `packages/base/any/initrds/buildroot/builds/Makefile` - Added GCC patches
- `packages/base/any/initrds/buildroot/builds/patches/*.patch` - GCC build fixes

### Platform Drivers
- `packages/platforms/celestica/x86-64/belgite/onlp/builds/x86_64_cel_belgite/module/src/{platform.c,sfpi.c}` - Linker fixes
- `packages/platforms/accton/x86-64/as5712-54x/platform-config/r0/src/python/x86_64_accton_as5712_54x_r0/__init__.py` - I2C bus renumbering

### Build Tools
- `tools/onlpm.py` - Debug logging
- `tools/onlrfs.py` - Temp directory handling
- `tools/onlyaml.py` - Python 2/3 YAML compatibility

---

## Installation Test Procedure

To verify the fixes:

```bash
# 1. Build the installer
make docker
make -C builds/amd64/installer

# 2. Test swiprep extraction manually (in installer environment)
swiprep --install /path/to/ONL-*.swi /mnt/rootfs

# 3. Verify symlinks preserved
ls -la /mnt/rootfs/sbin  # Should show: sbin -> usr/sbin
ls -la /mnt/rootfs/sbin/init  # Should exist

# 4. Check boot configuration encoding
python3 -c "import base64; print(base64.b64encode(b'test').decode('ascii'))"

# 5. Full install test on target hardware via ONIE
# Install via ONIE and verify switch_root completes successfully
```

---

## Git Commit References

### Fix Branch (`claude/fix-bytes-string-error-011CUy7w7mR6dHiHascH6kiB`)
- `d8b52f2e` - Fix symlink preservation in swiprep extraction
- `a5092ce8` - Fix unsquashfs threading deadlock in swiprep
- `a8b6e08e` - Fix line numbers in GCC implicit fallthrough patch
- `d18da6cc` - Add patch to fix GCC 4.7.2 implicit fallthrough warnings
- `f7fb2268` - Correct line numbers to 671 in GCC __FUNCTION__ patch
- `3ecf3538` - Fix line numbers in GCC __FUNCTION__ patch
- `5730a4bd` - Fix GCC 4.7.2 __FUNCTION__ pedantic warning
- `da8a9492` - Update sm/infra submodule with Python 3 compatibility fix

### Bookworm Branch
- `078d6c0c` - Remove stray files
- `96173895` - Latest changes to move to Python3, Debian Bookworm and Kernel 6.1
- `bb3be615` - Add Makefiles to the REPO directory for Bookworm
- `636ed109` - Remove unused global variables from sfpi.c
- `4ca1527b` - Fix multiple definition linker errors in belgite platform
- `038eebbd` - Add -Wno-implicit-fallthrough to GCC build
- `6c4c0f85` - Fix GCC 4.7.2 build warnings

---

## Recommendations for Next Steps

1. **Merge Strategy**: Consider merging `claude/fix-bytes-string-error-*` branch into `bookworm` branch
2. **Platform Testing**: Test AS5712-54X platform on actual hardware with Kernel 6.1
3. **Python 2 Removal**: Complete migration of remaining Python 2 scripts (especially `onl-install`)
4. **Additional Platforms**: Audit and update other platform I2C bus configurations for Kernel 6.1
5. **Regression Testing**: Build and test installer for all supported platforms
6. **Documentation**: Update platform bring-up guides with new I2C bus numbering

---

**Document Created**: 2025-11-12
**Last Updated**: 2025-11-12
**Authors**: Claude Code AI + Steven Noble

