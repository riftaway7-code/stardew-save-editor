from __future__ import annotations

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.usbmux import list_devices as _usbmux_list_devices

from svse.device._util import run
from svse.device.errors import DeviceNotFoundError
from svse.device.models import DeviceInfo


async def _list_devices_async() -> list[DeviceInfo]:
    connections = await _usbmux_list_devices()
    infos: list[DeviceInfo] = []
    for conn in connections:
        udid = getattr(conn, "serial", None) or getattr(conn, "udid", None)
        if not udid:
            continue
        try:
            lockdown = await create_using_usbmux(serial=udid, autopair=False)
        except Exception:
            # Device is visible on the USB bus but lockdownd isn't answering
            # yet (e.g. locked screen mid-handshake) - skip rather than crash
            # the whole listing.
            continue
        infos.append(
            DeviceInfo(
                udid=udid,
                name=lockdown.display_name,
                ios_version=lockdown.product_version,
                device_class=lockdown.device_class,
            )
        )
    return infos


def list_devices() -> list[DeviceInfo]:
    """Enumerate all iOS devices currently visible over USB."""
    return run(_list_devices_async())


def get_device(udid: str) -> DeviceInfo:
    for device in list_devices():
        if device.udid == udid:
            return device
    raise DeviceNotFoundError(f"No connected device with udid {udid!r}")
