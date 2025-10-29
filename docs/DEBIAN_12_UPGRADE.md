# OpenNetworkLinux Debian 12 (Bookworm) Upgrade Guide

## Overview

This document describes the implementation of Debian 12 (Bookworm) support for OpenNetworkLinux. The upgrade from Debian 10 (Buster) is a major milestone that brings modern toolchains, updated security, and long-term support.

**Status:** EXPERIMENTAL - Phase 1 implementation complete
**Date Created:** 2025-10-28
**Debian Version:** 12 (Bookworm)
**Builder Version:** 1.0

---

## What Has Been Implemented

### Phase 1: Foundation (COMPLETED)

1. **Docker Builder Container**
   - Location: `docker/images/builder12/1.0/`
   - Base image: `debian:12`
   - All build dependencies updated for Bookworm
   - Cross-compilation support for arm64, armel, armhf
   - Updated toolchains: GCC 12, binutils, etc.

2. **Rootfs Configuration**
   - Location: `builds/any/rootfs/bookworm/`
   - Package lists updated for Debian 12
   - Key changes:
     - `ntp` → `ntpsec` (time synchronization)
     - Added `usrmerge` (merged /usr filesystem)
     - Added `libcrypt1` (cryptography library)
     - Updated to `non-free-firmware` component
     - Retained `rsyslog` for logging compatibility

3. **Build System Integration**
   - Updated `docker/tools/onlbuilder` to support builder12
   - Command: `./docker/tools/onlbuilder --12` or `./docker/tools/onlbuilder --bookworm`

---

## Quick Start

### Building the Builder12 Docker Image

```bash
cd docker/images/builder12/1.0
make build
```

This will create the Docker image: `opennetworklinux/builder12:1.0`

### Using the Builder12 Container

```bash
# Start a builder12 shell
./docker/tools/onlbuilder --12

# Inside the container:
cd /home/ubuntu/OpenNetworkLinux
source setup.env
export ONL_DEBIAN_SUITE=bookworm

# Test build (requires further setup - see below)
make amd64
```

---

## Next Steps Required

### Phase 2: Kernel and Platform Support (NOT YET IMPLEMENTED)

The following steps are required before Bookworm builds will work:

1. **Kernel Build Support**
   - Create `packages/base/amd64/kernels/kernel-*/builds/bookworm/` directories
   - Copy kernel sources or create symlinks from buster builds
   - Test compilation with GCC 12 (expect warnings/errors to fix)
   - Update kernel configs if needed

2. **Platform Module Building**
   - Test platform-specific kernel modules under Bookworm
   - Fix compilation errors (GCC 12 is stricter)
   - Validate I2C, SPI, GPIO drivers

3. **Package Repository**
   - Create `REPO/bookworm/` directory structure
   - Build ONL-specific packages (onlp, onl-faultd, etc.) for Bookworm
   - Set up local APT repository

4. **Integration Testing**
   - Build complete installer image
   - Test in QEMU/VM
   - Test on physical hardware

---

## Key Differences from Debian 10 (Buster)

### Package Changes

| Debian 10 (Buster) | Debian 12 (Bookworm) | Notes |
|--------------------|----------------------|-------|
| `ntp` | `ntpsec` or `systemd-timesyncd` | NTP implementation replaced |
| N/A | `usrmerge` | Required for merged /usr layout |
| N/A | `libcrypt1` | Explicit cryptography library |
| `non-free` | `non-free` + `non-free-firmware` | Firmware separated |
| `python3.7` | `python3.11` | Major Python version bump |
| `gcc-8` | `gcc-12` | Stricter compiler warnings |
| `openssl-1.1` | `openssl-3.0` | API changes |

### Build System Changes

- **GCC 12**: More aggressive optimization, stricter warnings
- **Merged /usr**: `/bin`, `/sbin`, `/lib` are now symlinks
- **Python PEP-668**: System Python marked as externally-managed
- **rsyslog**: No longer installed by default (we explicitly include it)

---

## Testing Checklist

Before declaring Bookworm support stable, complete this checklist:

### Docker Builder
- [x] Dockerfile builds successfully
- [ ] All cross-compilation toolchains work
- [ ] Build tools (make, gcc, etc.) functional

### Rootfs
- [ ] Multistrap creates rootfs without errors
- [ ] All required packages install
- [ ] No dependency conflicts
- [ ] Rootfs boots in QEMU

### Kernels
- [ ] Kernel 5.4 compiles
- [ ] Kernel 4.19 compiles
- [ ] Kernel 4.14 compiles
- [ ] Kernel 4.9 compiles
- [ ] Kernel 3.16 compiles (or marked unsupported)

### Platform Modules
- [ ] Sample platform builds (e.g., AS7712-32X)
- [ ] Kernel modules load successfully
- [ ] Hardware detection works
- [ ] No runtime errors

### Complete Build
- [ ] `make amd64` completes without errors
- [ ] Installer image created
- [ ] SWI image created
- [ ] Images are bootable

### Hardware Testing
- [ ] Boots on physical switch
- [ ] Network interfaces detected
- [ ] SFP modules detected
- [ ] Fan control works
- [ ] Temperature monitoring works
- [ ] LED control works

---

## Known Issues and Limitations

### Current Limitations

1. **No kernel builds yet**: Kernel source directories for bookworm not created
2. **No platform testing**: Build system not yet validated end-to-end
3. **Experimental status**: Not recommended for production use

### Expected Issues (To Be Addressed)

1. **GCC 12 Warnings**: Older code may trigger new compiler warnings
   - `-Warray-bounds`
   - `-Wstringop-overflow`
   - `-Wformat-overflow`

2. **Kernel API Changes**: Older kernels (3.16) may have compatibility issues

3. **Module ABI**: All kernel modules must be recompiled

4. **OpenSSL 3.0**: Some crypto code may need updates

---

## Troubleshooting

### Builder Image Build Fails

**Issue**: `apt-get` fails to find packages

**Solution**: Check package names - some may have changed in Bookworm
```bash
# Search for package
docker run -it debian:12 bash
apt-cache search <package-name>
```

### Multistrap Fails

**Issue**: `multistrap` cannot find packages

**Solution**: Verify repository configuration in `standard.yml`
- Check `ONL_DEBIAN_SUITE=bookworm` is set
- Verify `non-free-firmware` component is included

### Kernel Build Fails

**Issue**: GCC 12 compilation errors

**Solution**: Add flags to relax warnings temporarily
```makefile
CFLAGS += -Wno-array-bounds -Wno-stringop-overflow
```

---

## Development Workflow

### Recommended Approach

1. **Start with Latest Kernel**: Begin with kernel 5.4 (most likely to work)
2. **Single Platform First**: Pick one well-supported platform (e.g., AS7712-32X)
3. **Incremental Testing**: Test each component before moving to next
4. **Document Issues**: Track all build errors and solutions

### Iteration Cycle

```bash
# 1. Enter builder12 container
./docker/tools/onlbuilder --12

# 2. Make changes to source code
vim packages/platforms/accton/x86-64/as7712-32x/...

# 3. Test build
source setup.env
export ONL_DEBIAN_SUITE=bookworm
make amd64

# 4. Debug and iterate
# Fix errors, repeat step 3

# 5. Exit container when done
exit
```

---

## References

### Debian Documentation
- [Debian 12 Release Notes](https://www.debian.org/releases/bookworm/releasenotes)
- [Debian 12 Installation Guide](https://www.debian.org/releases/bookworm/installmanual)
- [Upgrading to Bookworm](https://www.debian.org/releases/bookworm/amd64/release-notes/ch-upgrading.html)

### ONL Documentation
- [ONL Build System](../CONTRIBUTING.md)
- [Platform Porting Guide](PLATFORM_ARCHITECTURE.md)
- [ONL Code Quality Checklist](../ONL_PLATFORM_CODE_QUALITY_CHECKLIST.md)

---

## Contributing

If you encounter issues or have improvements:

1. **Document the Issue**: Create detailed bug reports
2. **Test Thoroughly**: Validate on multiple platforms if possible
3. **Submit Pull Requests**: Follow ONL contribution guidelines
4. **Update This Document**: Keep this guide current

---

## Support and Contact

- **ONL Mailing List**: opennetworklinux@lists.opennetlinux.org
- **GitHub Issues**: https://github.com/opencomputeproject/OpenNetworkLinux/issues
- **Slack**: #opennetworklinux (OCP Slack)

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-28 | ONL Team | Initial implementation - Phase 1 complete |

---

## License

This document and associated code are licensed under the Eclipse Public License 1.0.
See [LICENSE](../LICENSE) for details.
