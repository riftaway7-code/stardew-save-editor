#!/usr/bin/env python3
"""Standalone, no-GUI smoke test for the device layer.

Reproduces the manual flow from tonight's live debugging session end to end:
list devices -> confirm pairing/dev mode -> find Stardew Valley -> list save
folders -> pull one save to a local scratch dir.

Run with the project venv active:
    python tools/smoke_test_device.py
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from svse import device


def _pick_target(requested_udid: str | None) -> device.DeviceInfo:
    """Pick the device to use: an explicit --udid if given, otherwise the
    first connected device that's paired, dev-mode-enabled, and actually has
    Stardew Valley installed (skipping others rather than failing on the
    first mismatch, since multiple iOS devices are commonly connected at
    once during development)."""
    devices = device.list_devices()
    if not devices:
        raise SystemExit("No devices found. Plug in and unlock the device, then retry.")
    for d in devices:
        print(f"  {d.name}  ({d.device_class}, iOS {d.ios_version})  udid={d.udid}")

    if requested_udid:
        for d in devices:
            if d.udid == requested_udid:
                return d
        raise SystemExit(f"No connected device with udid {requested_udid!r}")

    if len(devices) == 1:
        return devices[0]

    print("\nMultiple devices connected; checking each for Stardew Valley...")
    for d in devices:
        try:
            if device.pairing_status(d.udid) != device.PairingStatus.PAIRED:
                continue
            device.find_stardew_app(d.udid)
            print(f"  -> using {d.name} ({d.udid}), Stardew Valley found")
            return d
        except device.DeviceError:
            print(f"  -> skipping {d.name}: not paired or Stardew Valley not found")
            continue
    raise SystemExit("None of the connected devices are paired with Stardew Valley installed.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--udid", help="Target a specific device by udid")
    args = parser.parse_args()

    print("== Listing connected devices ==")
    target = _pick_target(args.udid)
    print(f"\nUsing device: {target.name} ({target.udid})")

    print("\n== Pairing status ==")
    status = device.pairing_status(target.udid)
    print(f"  {status.value}")
    if status != device.PairingStatus.PAIRED:
        print("  Not paired - attempting to pair (accept the Trust dialog on-device)...")
        try:
            device.pair(target.udid)
            print("  Paired.")
        except device.NotPairedError as exc:
            print(f"  FAILED: {exc}")
            return 1

    print("\n== Developer Mode status ==")
    dev_status = device.developer_mode_status(target.udid)
    print(f"  {dev_status.value}")
    if dev_status != device.DevModeStatus.ENABLED:
        print(
            "  Developer Mode is off. Enable it on-device: Settings -> "
            "Privacy & Security -> Developer Mode -> On (device will "
            "restart), then re-run this script."
        )
        return 1

    print("\n== Finding Stardew Valley ==")
    try:
        app_info = device.find_stardew_app(target.udid)
    except device.AppNotFoundError as exc:
        print(f"  FAILED: {exc}")
        return 1
    print(f"  Found: {app_info.get('CFBundleDisplayName', 'Stardew Valley')} "
          f"v{app_info.get('CFBundleShortVersionString', '?')}")

    print("\n== Listing save folders ==")
    folders = device.list_save_folders(target.udid)
    if not folders:
        print("  No save folders found.")
        return 1
    for f in folders:
        print(f"  {f.folder_name}  money={f.money}  days_played={f.days_played}")

    first = folders[0]
    print(f"\n== Pulling save: {first.folder_name} ==")
    pulled = device.pull_save(target.udid, first.folder_name)
    with tempfile.TemporaryDirectory(prefix="svse_smoketest_") as tmp:
        paths = device.saves.local_pulled_paths(pulled, Path(tmp), first.folder_name)
        for name, path in paths.items():
            print(f"  wrote {name} -> {path} ({path.stat().st_size} bytes)")

    print("\nAll smoke test steps passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
