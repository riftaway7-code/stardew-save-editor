"""App discovery for Stardew Valley on the device.

IMPORTANT - do not add a "container mode" AFC helper here. Tonight's manual
investigation confirmed, three separate times across two different
toolchains (libimobiledevice's afcclient and pymobiledevice3 itself), that
``VendContainer`` house_arrest requests are rejected by the device
(``InstallationLookupFailed``) even with Developer Mode enabled and a fresh
pairing. Only ``VendDocuments`` (documents-only) is actually granted, and
even that only works reliably via the CLI shell path - see
svse.device._shell and svse.device.saves for the actual file I/O, which goes
through that shell rather than the raw HouseArrestService API (the raw API's
listdir/exists/get_file_contents returned PERM_DENIED/OBJECT_NOT_FOUND for
paths the CLI shell handles fine; not worth reverse-engineering further
under time pressure - shell out to what's proven to work).
"""

from __future__ import annotations

from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from svse.device._util import run
from svse.device.errors import AppNotFoundError
from svse.device.models import STARDEW_BUNDLE_ID


async def _find_stardew_app_async(udid: str) -> dict:
    lockdown = await create_using_usbmux(serial=udid, autopair=False)
    proxy = InstallationProxyService(lockdown)
    apps = await proxy.get_apps(application_type="User", bundle_identifiers=[STARDEW_BUNDLE_ID])
    if STARDEW_BUNDLE_ID not in apps:
        raise AppNotFoundError(
            "Stardew Valley isn't installed on this device (or hasn't been "
            "opened yet since install)."
        )
    return apps[STARDEW_BUNDLE_ID]


def find_stardew_app(udid: str) -> dict:
    return run(_find_stardew_app_async(udid))
