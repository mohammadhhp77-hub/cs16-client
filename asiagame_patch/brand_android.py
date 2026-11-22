#!/usr/bin/env python3
"""ASiA-GaME: minimal, reversible Android app branding in a clean CS16Client checkout.
Only changes applicationId and application label; keeps Java namespace and other code.
"""
from pathlib import Path
import argparse
import re

parser=argparse.ArgumentParser()
parser.add_argument('source',type=Path)
args=parser.parse_args()
root=args.source.resolve()
gradle=root/'android/app/build.gradle'
manifest=root/'android/app/src/main/AndroidManifest.xml'
if not gradle.is_file() or not manifest.is_file():
    raise SystemExit('Missing Android Gradle or main manifest in upstream source')

g=gradle.read_text(encoding='utf-8')
needle='applicationId = "su.xash.cs16client"'
assert g.count(needle)==1, f'Unexpected applicationId location: {g.count(needle)} matches'
newid='applicationId = "org.asiagame.cs16mobile"'
if newid in g:
    raise SystemExit('APK project already branded; use clean checkout')

a=manifest.read_text(encoding='utf-8')
matches=list(re.finditer(r'<application\b[^>]*>',a, flags=re.S))
assert len(matches)==1, 'Cannot uniquely locate Android <application> tag'
app_tag=matches[0].group(0)
if 'android:label=' in app_tag:
    labeled, n=re.subn(r'android:label\s*=\s*"[^"]*"',
                       'android:label="ASiA-GaME CS Mobile"',app_tag,count=1)
    assert n==1
else:
    labeled=app_tag[:-1]+' android:label="ASiA-GaME CS Mobile">'
a2=a[:matches[0].start()]+labeled+a[matches[0].end():]

gradle.write_text(g.replace(needle,newid,1),encoding='utf-8')
manifest.write_text(a2,encoding='utf-8')
print('Branding applied: org.asiagame.cs16mobile (debug adds .test), ASiA-GaME CS Mobile')
