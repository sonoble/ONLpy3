# Python 3 subprocess.check_output() Bytes Handling Fixes

## Issue Summary

In Python 3, `subprocess.check_output()` returns bytes instead of strings (as it did in Python 2). This caused `TypeError: a bytes-like object is required, not 'str'` when calling string methods like `.split()` or `.strip()` on the returned bytes object.

## Files Fixed

### 1. submodules.py (lines 33-42)
**Fix**: Updated the `check_output()` wrapper function to automatically decode bytes to UTF-8 strings.

```python
def check_output(cmd, *args, **kwargs):
    if type(cmd) == str:
        logger.debug("+ " + cmd)
    else:
        logger.debug("+ " + " ".join(cmd))
    # In Python 3, subprocess.check_output returns bytes, so decode to string
    output = subprocess.check_output(cmd, *args, **kwargs)
    if isinstance(output, bytes):
        return output.decode('utf-8')
    return output
```

**Impact**: Fixes all 4 uses of check_output() in this file automatically.

### 2. make-versions.py (line 29)
**Fix**: Added `.decode('utf-8')` before `.strip()`

```python
# Before:
self.build_sha1 = subprocess.check_output(cmd).strip()

# After:
self.build_sha1 = subprocess.check_output(cmd).decode('utf-8').strip()
```

### 3. mkinstaller.py (lines 70, 79, 84, 97)
**Fix**: Added `.decode('utf-8')` before string operations

```python
# Line 70:
return subprocess.check_output(...).decode('utf-8').strip()

# Line 79:
for platform in subprocess.check_output(...).decode('utf-8').split():

# Line 84:
kernel = subprocess.check_output([...]).decode('utf-8').strip()

# Line 97:
offsets = subprocess.check_output(...).decode('utf-8').split()
```

### 4. onlvi.py (line 20)
**Fix**: Added `.decode('utf-8')` before `.strip()`

```python
# Before:
branch = subprocess.check_output(cmd).strip()

# After:
branch = subprocess.check_output(cmd).decode('utf-8').strip()
```

### 5. onlpm.py (line 1003)
**Fix**: Added `.decode('utf-8')` before `.split()`

```python
# Before:
arches = arches + subprocess.check_output(['dpkg', '--print-foreign-architectures']).split()

# After:
arches = arches + subprocess.check_output(['dpkg', '--print-foreign-architectures']).decode('utf-8').split()
```

### 6. onl-nos-create.py (line 508)
**Fix**: Added `.decode('utf-8')` before `.strip()`

```python
# Before:
branch = subprocess.check_output(cmd).strip()

# After:
branch = subprocess.check_output(cmd).decode('utf-8').strip()
```

## Additional Syntax Fixes

While fixing subprocess issues, we also corrected:

### Print Statement Fixes
- **onlpm.py**: Fixed 8+ print statements to use Python 3 function syntax
- **onl-nos-create.py**: Fixed 1 print statement

### Logger Format String Fixes
- **mkinstaller.py**: Fixed 4 instances of misplaced parentheses in `logger.info()` calls
  - Pattern: `logger.info("text")%` → `logger.info("text" %`

## Testing

All files pass Python 3 syntax validation:
```bash
python3 -m py_compile <filename>
```

## Total Changes

- **6 files** fixed for subprocess bytes handling
- **12 subprocess.check_output()** calls updated with `.decode('utf-8')`
- **1 wrapper function** created to handle decoding automatically
- **9+ print statements** converted to Python 3 syntax
- **4 logger.info()** calls fixed for proper formatting

## Date
2025-10-29

## Status
✅ All fixes applied and validated
