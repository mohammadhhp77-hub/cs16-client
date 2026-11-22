#!/usr/bin/env python3
"""Read-only checks of a produced GitHub Actions preview APK."""
from pathlib import Path
import sys
import zipfile
from hashlib import sha256

if len(sys.argv)!=2:
    raise SystemExit('Usage: python verify_preview_apk.py <apk>')
path=Path(sys.argv[1]); assert path.is_file(), f'No APK: {path}'
expected={
 'lib/arm64-v8a/libmenu_android_arm64.so',
 'lib/armeabi-v7a/libmenu_android_armv7l.so',
 'lib/x86/libmenu_android_i386.so',
}
with zipfile.ZipFile(path) as z:
    corrupt=z.testzip()
    assert corrupt is None, f'Corrupt APK member: {corrupt}'
    names=set(z.namelist())
    missing=sorted(expected-names)
    assert not missing, f'Missing native menu libraries: {missing}'
    for name in expected:
        b=z.read(name)
        assert b'ASiA-GaME | Top Player' in b, f'Branding not in {name}'
        assert b'Servercs.ir:27015' in b, f'Server address not in {name}'
print('PASS: APK archive, 3 ABIs and embedded ASiA-GaME menu text')
print('SHA256:',sha256(path.read_bytes()).hexdigest())
