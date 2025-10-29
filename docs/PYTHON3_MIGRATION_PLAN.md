# Python 2 to Python 3 Migration Plan for OpenNetworkLinux

**Date:** 2025-10-28
**Status:** CRITICAL PATH - Required for Debian 12 builds
**Estimated Effort:** 2-3 weeks
**Priority:** P0 (Blocker for all Phase 2+ work)

---

## Executive Summary

Debian 12 (Bookworm) **does not include Python 2** at all. All Python 2 code must be migrated to Python 3 before any ONL builds will function in the builder12 container.

**Impact:** This migration blocks all Debian 12 development work until complete.

---

## Assessment Summary

### Files Requiring Migration

**Total Python files with shebangs:** 62 files
**Files with Python 2 shebangs:** 15+ critical build scripts

### Critical Path Scripts (Must Fix First)

These scripts are called during the build process and will fail immediately:

1. **tools/make-versions.py** - Version generation (called by setup.env)
2. **tools/submodules.py** - Submodule management (called by setup.env)
3. **tools/onlrfs.py** - Root filesystem creation
4. **tools/mkinstaller.py** - Installer image creation
5. **tools/onlpm.py** - Package management
6. **tools/onl-init-pkgs.py** - Package initialization
7. **tools/onl-platform-pkgs.py** - Platform package management
8. **tools/filenamer.py** - Filename generation
9. **tools/flat-image-tree.py** - Flattened image tree creation
10. **tools/onl-nos-create.py** - NOS creation
11. **tools/switool.py** - SWI tool
12. **tools/onlu.py** - ONL utility
13. **tools/newmodule.py** - Module creation
14. **tools/onlyaml.py** - YAML processing
15. **tools/onlplatform.py** - Platform tools
16. **tools/cpiomod.py** - CPIO modification
17. **tools/sjson.py** - JSON processing

### Python 2 Incompatibilities Found

1. **Shebang lines:** `#!/usr/bin/python2` (15 files)
2. **Print statements:** Old-style `print "text"` (10+ occurrences)
3. **Dictionary iterators:** `.iteritems()` (5+ occurrences)
4. **String/bytes handling:** Likely issues with subprocess output
5. **Exception syntax:** May have old `except Exception, e:` syntax

---

## Migration Strategy

### Phase 1: Assessment and Setup (Week 1, Days 1-2)

#### Day 1: Inventory and Analysis

1. **Create comprehensive file inventory:**
```bash
cd /home/ubuntu/ONL12
find . -type f -name "*.py" -exec grep -l "#!/usr/bin/python" {} \; > /tmp/python_files.txt
```

2. **Analyze each critical script:**
   - Check for Python 2-specific syntax
   - Identify library dependencies
   - Document external dependencies (yaml, subprocess, etc.)

3. **Set up testing framework:**
   - Create test cases for each critical script
   - Document expected inputs/outputs
   - Prepare test data

#### Day 2: Automated Analysis

1. **Run 2to3 analysis (dry run):**
```bash
cd /home/ubuntu/ONL12/tools
for script in *.py; do
    echo "=== $script ==="
    2to3 -n "$script" > "/tmp/2to3_analysis_$script.txt" 2>&1
done
```

2. **Categorize changes needed:**
   - Automatic (can use 2to3)
   - Semi-automatic (need manual review)
   - Manual (require code redesign)

3. **Create migration checklist** (see below)

---

### Phase 2: Core Script Migration (Week 1, Days 3-5)

#### Priority Order (Do in Sequence)

**Tier 1: Environment Setup (Day 3)**
1. `tools/submodules.py` - Required for setup.env
2. `tools/make-versions.py` - Required for setup.env

**Tier 2: Build Utilities (Day 4)**
3. `tools/onlyaml.py` - YAML parsing (used by many scripts)
4. `tools/sjson.py` - JSON parsing
5. `tools/filenamer.py` - Filename generation

**Tier 3: Package Management (Day 5)**
6. `tools/onlpm.py` - Package manager
7. `tools/onl-init-pkgs.py` - Package initialization
8. `tools/onl-platform-pkgs.py` - Platform packages

#### Migration Process for Each Script

1. **Backup original:**
```bash
cp script.py script.py.python2.bak
```

2. **Update shebang:**
```python
#!/usr/bin/python3
```

3. **Apply 2to3 automatic fixes:**
```bash
2to3 -w -n script.py
```

4. **Manual fixes:**
   - Review all changes
   - Fix string/bytes issues
   - Update exception handling
   - Fix imports (if needed)

5. **Test in builder12 container:**
```bash
docker run --rm -v /home/ubuntu/ONL12:/mnt/onl -w /mnt/onl opennetworklinux/builder12:1.0 \
    python3 tools/script.py --help
```

6. **Commit individually:**
```bash
git add tools/script.py
git commit -m "Migrate tools/script.py to Python 3"
```

---

### Phase 3: Image Creation Scripts (Week 2, Days 1-3)

**Tier 4: Rootfs and Installer (Days 1-2)**
8. `tools/onlrfs.py` - Root filesystem creation
9. `tools/mkinstaller.py` - Installer creation
10. `tools/flat-image-tree.py` - Flattened image tree

**Tier 5: NOS and Platform (Day 3)**
11. `tools/onl-nos-create.py` - NOS creation
12. `tools/onlplatform.py` - Platform tools
13. `tools/switool.py` - SWI tool
14. `tools/onlu.py` - ONL utilities

---

### Phase 4: Remaining Scripts (Week 2, Days 4-5)

**Tier 6: Additional Utilities**
15. `tools/newmodule.py` - Module creation
16. `tools/cpiomod.py` - CPIO modification
17. `tools/onlvi.py` - ONL VI tool

**Tier 7: Package Scripts**
- `packages/base/any/onlp/src/onlpdump.py`
- `packages/base/all/initrds/loader-initrd-files/src/bin/swicache.py`
- Any other Python scripts in packages/

---

### Phase 5: Testing and Validation (Week 3)

#### Day 1-2: Individual Script Testing

For each migrated script:

1. **Unit testing:**
```bash
# Test in builder12 container
docker run --rm -v /home/ubuntu/ONL12:/mnt/onl -w /mnt/onl opennetworklinux/builder12:1.0 bash -c "
    cd /mnt/onl
    python3 tools/make-versions.py --help
    python3 tools/submodules.py --help
    # etc.
"
```

2. **Functional testing:**
   - Run with real inputs
   - Compare outputs to Python 2 versions
   - Verify error handling

#### Day 3-4: Integration Testing

1. **Test setup.env:**
```bash
docker run --rm -v /home/ubuntu/ONL12:/mnt/onl -w /mnt/onl opennetworklinux/builder12:1.0 bash -c "
    cd /mnt/onl
    source setup.env
    echo 'Setup successful!'
"
```

2. **Test build preparation:**
```bash
# Try to prepare build environment
export ONL_DEBIAN_SUITE=bookworm
# Test various build scripts
```

3. **Test package operations:**
   - Package listing
   - Dependency resolution
   - Configuration parsing

#### Day 5: Documentation and Cleanup

1. **Document all changes:**
   - Update this migration plan with actual results
   - Create troubleshooting guide
   - Document any workarounds needed

2. **Clean up:**
   - Remove .python2.bak files (after verification)
   - Update any build documentation
   - Update CONTRIBUTING.md if needed

---

## Detailed Migration Checklist

### Common Python 2→3 Changes Needed

#### 1. Shebang Lines
```python
# Before:
#!/usr/bin/python2
#!/usr/bin/python

# After:
#!/usr/bin/python3
```

#### 2. Print Statements → Print Functions
```python
# Before:
print "Hello World"
print "Value:", value

# After:
print("Hello World")
print("Value:", value)
```

#### 3. Dictionary Iterators
```python
# Before:
for key, value in dict.iteritems():
for key in dict.iterkeys():
for value in dict.itervalues():

# After:
for key, value in dict.items():
for key in dict.keys():
for value in dict.values():
```

#### 4. Exception Handling
```python
# Before:
except Exception, e:

# After:
except Exception as e:
```

#### 5. String/Bytes Handling (subprocess)
```python
# Before:
output = subprocess.check_output(cmd).strip()

# After:
output = subprocess.check_output(cmd).decode('utf-8').strip()
# OR
output = subprocess.check_output(cmd, universal_newlines=True).strip()
```

#### 6. Integer Division
```python
# Before:
result = 5 / 2  # Returns 2 in Python 2

# After:
result = 5 // 2  # Integer division
result = 5 / 2   # Returns 2.5 in Python 3
```

#### 7. Input Function
```python
# Before:
value = raw_input("Prompt: ")

# After:
value = input("Prompt: ")
```

#### 8. Range vs xrange
```python
# Before:
for i in xrange(100):

# After:
for i in range(100):  # range() now returns iterator
```

#### 9. Unicode Strings
```python
# Before:
text = u"Unicode text"

# After:
text = "Unicode text"  # All strings are Unicode by default
```

#### 10. Import Changes
```python
# Before:
import ConfigParser

# After:
import configparser  # Note lowercase
```

---

## Automated Tools to Use

### 1. 2to3 Tool

**Primary conversion tool:**
```bash
# Analyze (dry run):
2to3 -n script.py

# Convert in place:
2to3 -w -n script.py

# Convert with specific fixers:
2to3 -w -f print -f except script.py
```

### 2. Python Compatibility Checker

Install and use `pylint` with Python 3:
```bash
pip3 install pylint
pylint --py3k script.py
```

### 3. Futurize (Alternative to 2to3)

For more conservative migration:
```bash
pip3 install future
futurize -w script.py
```

---

## Testing Strategy

### Unit Testing

For each script, create test cases:

```bash
# Example: tools/make-versions.py testing
docker run --rm -v /home/ubuntu/ONL12:/mnt/onl -w /mnt/onl opennetworklinux/builder12:1.0 bash -c "
    cd /mnt/onl

    # Test 1: Help output
    python3 tools/make-versions.py --help

    # Test 2: Run with minimal args (if applicable)
    # Add specific test cases based on script functionality
"
```

### Integration Testing

Test complete workflow:

```bash
# Test full environment setup
docker run --rm -it -v /home/ubuntu/ONL12:/mnt/onl -w /mnt/onl opennetworklinux/builder12:1.0 bash

# Inside container:
cd /mnt/onl
source setup.env
export ONL_DEBIAN_SUITE=bookworm

# Verify environment variables are set
echo $ONL_DEBIAN_SUITE
echo $ONL_VERSION

# Test build preparation (won't complete full build yet)
# But should get past Python script execution
```

### Regression Testing

After migration, verify:
1. All scripts execute without errors
2. Output matches expected format
3. File operations work correctly
4. Error handling still functional

---

## Risk Mitigation

### Risks

1. **Breaking existing Buster builds:** Python 3 changes might break Debian 10
2. **Subtle behavioral changes:** Python 3 may handle edge cases differently
3. **External dependencies:** Some Python libraries may not be compatible
4. **Time overrun:** Migration may take longer than estimated

### Mitigation Strategies

1. **Keep Python 2 compatibility initially:**
   - Use `#!/usr/bin/env python3` but make code compatible with both
   - Use `six` library for compatibility if needed
   - OR maintain separate scripts until Debian 12 is stable

2. **Comprehensive testing:**
   - Test every script individually
   - Create automated test suite
   - Test in both Python 2 (Buster) and Python 3 (Bookworm)

3. **Phased rollout:**
   - Migrate one script at a time
   - Test thoroughly before moving to next
   - Keep backups of Python 2 versions

4. **Backwards compatibility option:**
   - Consider maintaining ONL12 as separate branch
   - Don't merge to main ONL until fully validated
   - Keep Buster build capability in main branch

---

## Implementation Commands

### Quick Start Migration Script

```bash
#!/bin/bash
# Migrate a single Python script to Python 3

SCRIPT=$1

if [ -z "$SCRIPT" ]; then
    echo "Usage: $0 <script.py>"
    exit 1
fi

echo "Migrating $SCRIPT to Python 3..."

# Backup
cp "$SCRIPT" "$SCRIPT.python2.bak"
echo "✓ Created backup: $SCRIPT.python2.bak"

# Update shebang
sed -i '1s|#!/usr/bin/python2|#!/usr/bin/python3|' "$SCRIPT"
sed -i '1s|#!/usr/bin/python$|#!/usr/bin/python3|' "$SCRIPT"
echo "✓ Updated shebang"

# Apply 2to3
2to3 -w -n "$SCRIPT"
echo "✓ Applied 2to3 fixes"

# Test syntax
python3 -m py_compile "$SCRIPT"
if [ $? -eq 0 ]; then
    echo "✓ Python 3 syntax check passed"
else
    echo "✗ Python 3 syntax check FAILED"
    echo "Restoring backup..."
    cp "$SCRIPT.python2.bak" "$SCRIPT"
    exit 1
fi

echo ""
echo "Migration complete! Please test functionality:"
echo "  python3 $SCRIPT --help"
```

### Batch Migration Commands

```bash
cd /home/ubuntu/ONL12

# Migrate all critical tools scripts
for script in tools/make-versions.py tools/submodules.py tools/onlyaml.py \
              tools/sjson.py tools/filenamer.py tools/onlpm.py \
              tools/onl-init-pkgs.py tools/onl-platform-pkgs.py; do
    echo "=== Migrating $script ==="
    ./migrate_script.sh "$script"
    echo ""
done
```

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All 62 Python files identified and categorized
- [ ] 2to3 analysis completed for all files
- [ ] Test framework created
- [ ] Migration checklist finalized

### Phase 2 Complete When:
- [ ] All Tier 1-3 scripts migrated to Python 3
- [ ] All migrated scripts pass syntax check
- [ ] Individual script tests pass
- [ ] Git commits created for each script

### Phase 3 Complete When:
- [ ] All Tier 4-5 scripts migrated
- [ ] Image creation workflow tested
- [ ] No Python 2 dependencies remain in critical path

### Phase 4 Complete When:
- [ ] All remaining Python scripts migrated
- [ ] All Python 2 shebangs removed
- [ ] Complete file inventory verified

### Phase 5 Complete When:
- [ ] `source setup.env` works in builder12
- [ ] All build preparation scripts functional
- [ ] Integration tests pass
- [ ] Documentation updated
- [ ] Ready for Phase 2 (Kernel builds)

---

## Next Steps After Migration

Once Python 3 migration is complete:

1. **Proceed with Phase 2: Kernel Build Support**
   - Create kernel build directories for bookworm
   - Test kernel compilation with GCC 12
   - Fix GCC 12 warnings/errors

2. **Platform Module Testing**
   - Build AS7712-32X platform modules
   - Validate ONLP implementations
   - Fix hardware driver compatibility

3. **Full Build Attempt**
   - `make amd64` with `ONL_DEBIAN_SUITE=bookworm`
   - Document all remaining issues
   - Create comprehensive issue tracker

---

## Resources

### Documentation
- [Python 2 to 3 Porting Guide](https://docs.python.org/3/howto/pyporting.html)
- [2to3 Documentation](https://docs.python.org/3/library/2to3.html)
- [What's New in Python 3](https://docs.python.org/3/whatsnew/3.0.html)

### Tools
- `2to3` - Automated conversion tool
- `pylint --py3k` - Python 3 compatibility checker
- `futurize` - Alternative migration tool
- `six` - Python 2/3 compatibility library

### Testing
- Docker builder12 container for Python 3 testing
- Keep builder10 container for Python 2 regression testing

---

## Contacts and Support

For questions or issues during migration:
- ONL Mailing List: opennetworklinux@lists.opennetlinux.org
- GitHub Issues: https://github.com/opencomputeproject/OpenNetworkLinux/issues

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-28 | 1.0 | Initial migration plan created |

---

## Appendix: Complete File List

### Critical Build Scripts (Priority Order)

**Tier 1: Environment (CRITICAL)**
1. tools/submodules.py
2. tools/make-versions.py

**Tier 2: Core Utilities**
3. tools/onlyaml.py
4. tools/sjson.py
5. tools/filenamer.py

**Tier 3: Package Management**
6. tools/onlpm.py
7. tools/onl-init-pkgs.py
8. tools/onl-platform-pkgs.py

**Tier 4: Image Creation**
9. tools/onlrfs.py
10. tools/mkinstaller.py
11. tools/flat-image-tree.py

**Tier 5: Platform Tools**
12. tools/onl-nos-create.py
13. tools/onlplatform.py
14. tools/switool.py
15. tools/onlu.py

**Tier 6: Additional Utilities**
16. tools/newmodule.py
17. tools/cpiomod.py
18. tools/onlvi.py

### Package Python Scripts

- packages/base/any/onlp/src/onlpdump.py
- packages/base/any/onlp/src/onlp/module/python/onlp/onlp/enums.py
- packages/base/all/initrds/loader-initrd-files/src/bin/swicache.py
- packages/base/all/vendor-config-onl/src/python/onl/mounts/__init__.py
- [Full inventory to be created in Phase 1]

---

**STATUS:** Plan created and ready for implementation
**NEXT ACTION:** Begin Phase 1, Day 1 - Create comprehensive file inventory
