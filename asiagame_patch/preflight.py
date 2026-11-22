#!/usr/bin/env python3
"""Read-only original APK / source preflight. Does not modify either."""
import argparse
import subprocess
import sys
import zipfile
from pathlib import Path
from hashlib import sha256
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--apk',type=Path)
p.add_argument('--source',type=Path)
a=p.parse_args()
failed=False
if a.apk:
    if not a.apk.is_file():
        print('ERROR: original APK does not exist:',a.apk);failed=True
    else:
        names = {
            'lib/arm64-v8a/libmenu_android_arm64.so',
            'lib/armeabi-v7a/libmenu_android_armv7l.so',
            'lib/x86/libmenu_android_i386.so',
        }
        with zipfile.ZipFile(a.apk) as z:
            missing=names-set(z.namelist())
            corrupted=z.testzip()
            if corrupted or missing:
                failed=True
                print('ERROR: original APK damaged or missing libraries:',corrupted, sorted(missing))
            else:
                print('PASS: original APK ZIP and all three native menu libraries')
        print('APK SHA256:', sha256(a.apk.read_bytes()).hexdigest())
if a.source:
    patch=Path(__file__).resolve().parent/'apply_source_patch.py'
    result=subprocess.run([sys.executable,str(patch),str(a.source)],text=True)
    failed=failed or result.returncode!=0
if not a.apk and not a.source:
    p.print_help()
sys.exit(1 if failed else 0)
