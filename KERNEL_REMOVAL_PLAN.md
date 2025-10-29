# ONL12 Kernel Removal Plan: Removing 3.x and 4.x Kernels

## Executive Summary

This document outlines the plan to remove all Linux kernel versions 3.x and 4.x from the ONL12 (OpenNetworkLinux Debian 12) codebase, retaining only 5.x and 6.x kernels. This change is motivated by:

1. **Build System Compatibility**: Modern Debian 12 toolchains (GCC 11+, binutils 2.38+) have difficulty building older kernels
2. **Maintenance Burden**: Backporting fixes and patches for ancient kernels (some over 10 years old)
3. **Security**: Older kernels lack modern security features and require extensive patching
4. **Hardware Support**: Modern network switch hardware requires newer kernel features

## Rationale

### Current Build Issues with Old Kernels

#### GCC 10+ Multiple Definition Errors
- **Issue**: GCC 10+ changed default from `-fcommon` to `-fno-common`
- **Impact**: Breaks kernel build tools in kernels 3.2, 3.16, 4.9, 4.14, 4.19
- **Current Fix**: Applied patch `9999-gcc10-fix-relocs-multiple-definition.patch`

#### GCC 12+ Use-After-Free Warnings
- **Issue**: New warning flags legitimate realloc patterns as unsafe
- **Impact**: Breaks tools build in kernel 4.14
- **Current Fix**: Applied patch `9998-gcc12-fix-tools-use-after-free.patch`

#### Binutils 2.38+ Objtool Errors
- **Issue**: Newer binutils cause "missing symbol table" errors in objtool
- **Impact**: Currently blocking kernel 4.14 build (Build v25 failure)
- **Status**: NOT YET FIXED

### Future Compatibility Issues
As Debian evolves, more incompatibilities will emerge:
- GCC 13+ will likely introduce new warnings/errors
- Binutils changes may break more kernel build tools
- Python 3.12+ may break kernel build scripts
- Each issue requires research, patch development, and testing across all kernel versions

## Impact Analysis

### Architectures Affected

#### amd64 (x86_64)
- **Kernels to Remove**: 3.2-lts, 3.16-lts, 4.9-lts, 4.14-lts, 4.19-lts
- **Kernels to Keep**: 5.4-lts, 6.1-lts
- **Impact**: Medium - Most modern x86_64 platforms use 4.14+ or newer

#### ARM-based Systems
- **armel**: kernel-4.14-lts-armel-iproc-all, kernel-3.2-lts-arm-iproc-all
- **armhf**: kernel-4.14-lts-armhf-iproc-all
- **arm64**: kernel-4.9-lts-arm64-all
- **Impact**: HIGH - Need to identify replacement kernels for ARM platforms

#### PowerPC
- **Kernels**: kernel-3.16-lts-powerpc-e500v-all, kernel-3.8.13-powerpc-e500mc, kernel-3.9.6-powerpc-e500v
- **Impact**: CRITICAL - No newer kernels exist for PowerPC in ONL12
- **Decision Required**: Drop PowerPC support or maintain these kernels

### Platform Impact Assessment

Need to audit which platforms in `packages/platforms/` rely on old kernels:
- Accton platforms (large variety, many models)
- Inventec platforms
- Delta platforms
- Quanta platforms
- Others

Most modern platforms (2018+) should support kernel 5.4 or newer, but legacy hardware may require kernel 4.x.

## Removal Strategy

### Phase 1: Analysis and Preparation (Pre-Removal)

#### Step 1.1: Platform Dependency Audit
```bash
# Find all platform configurations
find packages/platforms/ -name "*.yml" -o -name "platform-config"

# Check platform kernel requirements
grep -r "kernel.*3\.\|kernel.*4\." packages/platforms/
```

**Deliverable**: List of platforms that explicitly require 3.x or 4.x kernels

#### Step 1.2: Bootloader Configuration Audit
```bash
# Check GRUB configurations
grep -r "kernel-3\.\|kernel-4\." packages/base/all/vendor-config-onl/
```

**Deliverable**: Updated default kernel selections

#### Step 1.3: Rootfs Dependency Audit
```bash
# Check rootfs package lists
grep -r "kernel.*3\.\|kernel.*4\." builds/any/rootfs/bookworm/
```

**Deliverable**: List of rootfs configurations requiring updates

### Phase 2: x86_64 (amd64) Kernel Removal

#### Step 2.1: Update Configuration Defaults
**File**: `/home/ubuntu/ONL12/packages/base/all/vendor-config-onl/src/lib/platform-config-defaults-x86-64.yml`

**Changes Required**:
1. Remove kernel definitions for 3.2, 3.16, 4.9, 4.14, 4.19
2. Update default kernel from `*kernel-3-16` to `*kernel-5-4`
3. Keep 5.4 and add 6.1 definitions

**Before**:
```yaml
kernel:
  <<: *kernel-3-16
```

**After**:
```yaml
kernel:
  <<: *kernel-5-4
```

#### Step 2.2: Remove Kernel Source Directories
```bash
cd /home/ubuntu/ONL12/packages/base/any/kernels
rm -rf 3.2-lts 3.16-lts 4.9-lts 4.14-lts 4.19-lts
```

**Directories to Remove**:
- `/home/ubuntu/ONL12/packages/base/any/kernels/3.2-lts`
- `/home/ubuntu/ONL12/packages/base/any/kernels/3.16-lts`
- `/home/ubuntu/ONL12/packages/base/any/kernels/4.9-lts`
- `/home/ubuntu/ONL12/packages/base/any/kernels/4.14-lts`
- `/home/ubuntu/ONL12/packages/base/any/kernels/4.19-lts`

#### Step 2.3: Remove Kernel Build Packages (amd64)
```bash
cd /home/ubuntu/ONL12/packages/base/amd64/kernels
rm -rf kernel-3.2-lts-x86-64-all
rm -rf kernel-3.16-lts-x86-64-all
rm -rf kernel-4.9-lts-x86-64-all
rm -rf kernel-4.14-lts-x86-64-all
rm -rf kernel-4.19-lts-x86-64-all
```

**Directories to Remove**:
- `/home/ubuntu/ONL12/packages/base/amd64/kernels/kernel-3.2-lts-x86-64-all`
- `/home/ubuntu/ONL12/packages/base/amd64/kernels/kernel-3.16-lts-x86-64-all`
- `/home/ubuntu/ONL12/packages/base/amd64/kernels/kernel-4.9-lts-x86-64-all`
- `/home/ubuntu/ONL12/packages/base/amd64/kernels/kernel-4.14-lts-x86-64-all`
- `/home/ubuntu/ONL12/packages/base/amd64/kernels/kernel-4.19-lts-x86-64-all`

### Phase 3: ARM Architecture Decision

**DECISION POINT**: ARM platforms currently depend on 4.x kernels

**Option A: Upgrade ARM to 5.4-lts**
- Create kernel-5.4-lts-arm64-all
- Create kernel-5.4-lts-armhf-iproc-all
- Create kernel-5.4-lts-armel-iproc-all
- Test on representative ARM hardware
- **Effort**: HIGH (requires testing on physical hardware)
- **Risk**: MEDIUM (kernel may need ARM-specific patches)

**Option B: Remove ARM Support Temporarily**
- Remove ARM kernel packages and platforms
- Document that ARM support requires further work
- **Effort**: LOW
- **Risk**: HIGH (breaks existing ARM deployments)

**Option C: Keep ARM 4.14-lts Only**
- Retain kernel 4.14-lts for ARM only (not amd64)
- Apply additional patches to fix binutils/objtool issues
- **Effort**: MEDIUM (need to fix current build errors)
- **Risk**: MEDIUM (ongoing maintenance burden)

**RECOMMENDATION**: Option C initially, with Option A as follow-up work

### Phase 4: PowerPC Architecture Decision

**DECISION POINT**: PowerPC uses ancient 3.x kernels (3.8.13, 3.9.6, 3.16)

**Option A: Drop PowerPC Support**
- Remove all PowerPC kernel packages
- Remove PowerPC platforms from build
- Document removal in BREAKING CHANGES
- **Effort**: LOW
- **Risk**: HIGH if PowerPC users exist

**Option B: Maintain PowerPC 3.16-lts**
- Keep only kernel-3.16-lts-powerpc-e500v-all
- Apply necessary patches for Debian 12 compatibility
- **Effort**: HIGH (more patches needed)
- **Risk**: HIGH (unmaintained kernel)

**RECOMMENDATION**: Option A (drop PowerPC) - these are very old embedded systems (2010-2014 era)

### Phase 5: Platform-Specific Updates

After kernel removal, update platform configurations that reference old kernels:

#### Step 5.1: Find Platform References
```bash
grep -r "kernel-3\|kernel-4" packages/platforms/ --include="*.yml"
grep -r "kernel.*3\.\|kernel.*4\." packages/platforms/ --include="platform-config"
```

#### Step 5.2: Update or Remove Platforms
For each platform found:
1. Check if platform hardware can support 5.4 or 6.1 kernel
2. If yes: Update platform configuration to use newer kernel
3. If no: Remove platform or document as unsupported

### Phase 6: Testing and Validation

#### Step 6.1: Build System Test
```bash
cd /home/ubuntu/ONL12
source setup.env
make amd64
```

**Expected Result**: Build completes without kernel-related errors

#### Step 6.2: Verify Kernel Packages
```bash
find builds/amd64/REPO -name "onl-kernel-*.deb"
```

**Expected Packages**:
- onl-kernel-5.4-lts-x86-64-all
- onl-kernel-6.1-lts-x86-64-all
- (Optional) onl-kernel-4.14-lts-armhf-iproc-all if ARM retained

#### Step 6.3: Installer Image Test
Build ONIE installer and verify:
1. Installer contains correct kernel version
2. Default kernel selection works
3. GRUB menu shows only 5.4 and 6.1 options

## Implementation Timeline

### Immediate (Day 1)
1. Stop current build v25 (failing due to objtool errors)
2. Back up current state: `git stash push -m "Pre kernel removal backup"`
3. Create feature branch: `git checkout -b remove-old-kernels`

### Phase 1 (Day 1-2): Analysis
- Complete platform dependency audit
- Document all impacts
- Make final decision on ARM and PowerPC

### Phase 2 (Day 2-3): amd64 Removal
- Execute all Step 2.x items
- Update configuration files
- Remove directories
- Test build

### Phase 3 (Day 3-4): ARM/PowerPC
- Implement chosen options
- Update or remove affected platforms

### Phase 4 (Day 4-5): Testing
- Full build test
- Create test installer images
- Document changes

### Phase 5 (Day 5+): Documentation and Merge
- Update README.md
- Create BREAKING_CHANGES.md
- Update platform support matrix
- Merge to master after review

## Rollback Plan

If issues are encountered:

1. **Before Commit**:
   ```bash
   git stash pop  # Restore pre-removal state
   ```

2. **After Commit**:
   ```bash
   git revert <commit-hash>  # Revert removal commit
   ```

3. **Keep Backup Branch**:
   - Keep `remove-old-kernels` branch as reference
   - Can cherry-pick specific fixes if partial revert needed

## Files to Modify

### Configuration Files
- `/home/ubuntu/ONL12/packages/base/all/vendor-config-onl/src/lib/platform-config-defaults-x86-64.yml`
- `/home/ubuntu/ONL12/packages/base/all/vendor-config-onl/src/lib/platform-config-defaults-uboot.yml` (if ARM changes)
- `/home/ubuntu/ONL12/builds/any/rootfs/bookworm/common/armhf-base-packages.yml` (remove kernel-4.14 reference)
- `/home/ubuntu/ONL12/builds/any/rootfs/bookworm/common/armel-base-packages.yml` (remove kernel-4.14 reference)

### Directories to Remove (Confirmed)
```
packages/base/any/kernels/3.2-lts/
packages/base/any/kernels/3.16-lts/
packages/base/any/kernels/4.9-lts/
packages/base/any/kernels/4.14-lts/
packages/base/any/kernels/4.19-lts/
packages/base/amd64/kernels/kernel-3.2-lts-x86-64-all/
packages/base/amd64/kernels/kernel-3.16-lts-x86-64-all/
packages/base/amd64/kernels/kernel-4.9-lts-x86-64-all/
packages/base/amd64/kernels/kernel-4.14-lts-x86-64-all/
packages/base/amd64/kernels/kernel-4.19-lts-x86-64-all/
```

### Directories to Remove (ARM - If Option A or B)
```
packages/base/arm64/kernels/kernel-4.9-lts-arm64-all/
packages/base/armhf/kernels/kernel-4.14-lts-armhf-iproc-all/
packages/base/armel/kernels/kernel-4.14-lts-armel-iproc-all/
packages/base/armel/kernels/kernel-3.2-lts-arm-iproc-all/
```

### Directories to Remove (PowerPC - If Option A)
```
packages/base/powerpc/kernels/legacy/kernel-3.8.13-powerpc-e500mc/
packages/base/powerpc/kernels/legacy/kernel-3.9.6-powerpc-e500v/
packages/base/powerpc/kernels/kernel-3.16-lts-powerpc-e500v-all/
```

## Success Criteria

1. ✅ amd64 build completes successfully with only 5.4 and 6.1 kernels
2. ✅ No references to removed kernels in configuration files
3. ✅ Generated installer images boot correctly
4. ✅ GRUB menu shows only supported kernels
5. ✅ All tests pass (if test suite exists)
6. ✅ Documentation updated
7. ✅ Breaking changes clearly communicated

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Platform incompatibility | MEDIUM | HIGH | Audit platforms before removal |
| ARM hardware breaks | MEDIUM | MEDIUM | Keep 4.14 for ARM initially |
| PowerPC users impacted | LOW | MEDIUM | Document removal, provide warning |
| Build system errors | LOW | LOW | Test thoroughly before commit |
| Installer boot failure | LOW | HIGH | Test on real hardware if possible |

## Next Steps (Immediate Actions)

1. **STOP** current failing build (v25)
2. **BACKUP** current git state
3. **AUDIT** platform dependencies (run Phase 1 analysis)
4. **DECIDE** on ARM and PowerPC options
5. **EXECUTE** amd64 kernel removal (Phase 2)
6. **TEST** build with only 5.4 and 6.1 kernels
7. **ITERATE** on any issues found

## Questions to Resolve Before Proceeding

1. ❓ **ARM Support**: Keep 4.14 or upgrade to 5.4?
2. ❓ **PowerPC Support**: Drop entirely or maintain 3.16?
3. ❓ **Platform Testing**: Can we test on real hardware, or rely on build-only validation?
4. ❓ **Upgrade Path**: Should we provide migration guide for existing ONL installations?
5. ❓ **Version Naming**: Does this constitute ONL 2.0, or minor version bump?

## Conclusion

Removing 3.x and 4.x kernels will significantly simplify ONL12 maintenance and improve build system reliability. The main challenges are:

1. **ARM platforms** - need decision on kernel version
2. **PowerPC platforms** - likely obsolete, can be dropped
3. **Platform audit** - ensuring modern platforms support newer kernels

**Estimated Effort**: 3-5 days for initial implementation + testing
**Recommended Approach**: Start with amd64 only, address ARM/PowerPC in follow-up

---

**Document Version**: 1.0
**Date**: 2025-10-29
**Author**: Claude Code (Automated Analysis)
