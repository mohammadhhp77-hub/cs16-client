#!/usr/bin/env python3
"""ASiA-GaME: add only missing stock touchscreen assets; never alter native/menu sources."""
import argparse
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from hashlib import sha256

BUNDLE_SHA256 = "3f4ee86b7fa9a1057003c42f1cc0de8dfb825e33e3a9a9091050328c3077b36f"
ASSET_COUNT = 133
REQUIRED_ICONS = ("attack", "duck", "jump", "reload", "buy", "drop", "walk")


def validate_bundle(bundle):
    assert bundle.is_file(), f"Missing touch bundle: {bundle}"
    data = bundle.read_bytes()
    assert sha256(data).hexdigest() == BUNDLE_SHA256, "Touch bundle SHA256 mismatch: no files changed"
    with ZipFile(bundle) as z:
        assert z.testzip() is None, "Touch bundle ZIP corruption"
        names = z.namelist()
        assert len(names) == ASSET_COUNT and len(set(names)) == ASSET_COUNT, "Unexpected touch bundle entries"
        for name in names:
            p = PurePosixPath(name)
            assert name == "assets/touch.cfg" or p.parts[:2] == ("assets", "touch") or name.startswith("assets/touch_default/") or name.startswith("assets/touch_presets/"), name
            assert not p.is_absolute() and ".." not in p.parts and not name.endswith("/"), name
        for icon in REQUIRED_ICONS:
            assert f"assets/touch/gfx/{icon}.png" in names, f"Missing icon: {icon}"
        assert "assets/touch.cfg" in names
        return {name:z.read(name) for name in names}


def stage(root, files):
    base=root/"android/app/src/main/assets"
    assert (root/"android/app/build.gradle").is_file(), "Expected CS16Client Android root not found"
    collision=[]
    additions=[]
    for name, b in files.items():
        target=base/name.removeprefix("assets/")
        if target.exists():
            if target.is_file() and target.read_bytes()==b:
                continue
            collision.append(str(target))
        else:
            additions.append((target,b))
    if collision:
        raise SystemExit("ABORT: existing asset files differ; refusing overwrite:\n"+"\n".join(collision))
    return additions


def verify_apk(apk,files):
    assert apk.is_file(), f"Missing APK: {apk}"
    with ZipFile(apk) as z:
        assert z.testzip() is None, "Broken APK archive"
        present=set(z.namelist())
        missing=sorted(set(files)-present)
        if missing:
            raise SystemExit(f"APK missing {len(missing)} touchscreen resources, e.g. {missing[:5]}")
        corrupted=[name for name,data in files.items() if sha256(z.read(name)).digest()!=sha256(data).digest()]
        if corrupted:
            raise SystemExit(f"APK has {len(corrupted)} modified touchscreen resources: {corrupted[:5]}")
        print(f"PASS: all {len(files)} original touchscreen resources packaged byte-for-byte")
        print("PASS: required buttons", ", ".join(REQUIRED_ICONS))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("root",type=Path,help="CS16Client repository root")
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true",help="Read-only preflight")
    group.add_argument("--apply",action="store_true",help="Copy only missing assets")
    group.add_argument("--verify-apk",type=Path,help="Read-only verify final built APK")
    args=parser.parse_args()
    root=args.root.resolve()
    bundle=root/"asiagame_patch/assets/original_touch_bundle.zip"
    files=validate_bundle(bundle)
    if args.verify_apk:
        verify_apk(args.verify_apk.resolve(),files)
        return
    additions=stage(root,files)
    if args.check:
        print(f"PASS: bundle validated; {len(files)} resources; {len(additions)} new files; 0 files will be overwritten")
        return
    for target,data in additions:
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
    assert not stage(root,files), "Post-write verification failed"
    print(f"PASS: added {len(additions)} stock touch resources; no existing file modified")

if __name__=="__main__":
    main()
