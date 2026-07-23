from __future__ import annotations

from pymobiledevice3.exceptions import PairingDialogResponsePendingError, UserDeniedPairingError
from pymobiledevice3.lockdown import create_using_usbmux
from pymobiledevice3.services.amfi import AmfiService

from svse.device._util import run
from svse.device.errors import DeveloperModeError, NotPairedError
from svse.device.models import DevModeStatus, PairingStatus


async def _pairing_status_async(udid: str) -> PairingStatus:
    # create_using_usbmux() already calls validate_pairing() internally as
    # part of _handle_autopair(), regardless of autopair=True/False - calling
    # it again here would start a second session on top of an already-active
    # one and fail with LockdownError("SessionActive"). Just read the
    # resulting .paired flag instead.
    lockdown = await create_using_usbmux(serial=udid, autopair=False)
    return PairingStatus.PAIRED if lockdown.paired else PairingStatus.NOT_PAIRED


def pairing_status(udid: str) -> PairingStatus:
    return run(_pairing_status_async(udid))


async def _pair_async(udid: str, timeout: float | None) -> None:
    # autopair=True makes create_using_usbmux() do pair()+validate_pairing()
    # internally (via _handle_autopair) in one session - don't call
    # lockdown.pair() again ourselves afterward, see _pairing_status_async.
    try:
        await create_using_usbmux(serial=udid, autopair=True, pair_timeout=timeout)
    except PairingDialogResponsePendingError as exc:
        raise NotPairedError(
            "Accept the 'Trust This Computer?' prompt on the device, then try again."
        ) from exc
    except UserDeniedPairingError as exc:
        raise NotPairedError("Pairing was declined on the device.") from exc


def pair(udid: str, timeout: float | None = 30.0) -> None:
    """Trigger (or confirm) pairing. Raises NotPairedError with a
    user-facing message if the on-device Trust dialog hasn't been accepted
    yet - the GUI should catch this and show a "check your device" prompt."""
    run(_pair_async(udid, timeout))


async def _developer_mode_status_async(udid: str) -> DevModeStatus:
    lockdown = await create_using_usbmux(serial=udid, autopair=False)
    enabled = await lockdown.get_developer_mode_status()
    return DevModeStatus.ENABLED if enabled else DevModeStatus.DISABLED


def developer_mode_status(udid: str) -> DevModeStatus:
    return run(_developer_mode_status_async(udid))


async def _prompt_enable_developer_mode_async(udid: str) -> None:
    lockdown = await create_using_usbmux(serial=udid, autopair=False)
    amfi = AmfiService(lockdown)
    try:
        await amfi.enable_developer_mode()
    except Exception as exc:
        raise DeveloperModeError(
            "Couldn't enable Developer Mode automatically (often because the "
            "device has a passcode set). Enable it manually: Settings -> "
            "Privacy & Security -> Developer Mode -> On, then let the device "
            "restart and confirm 'Turn On' after reboot."
        ) from exc


def prompt_enable_developer_mode(udid: str) -> None:
    """Best-effort attempt to reveal/enable Developer Mode. On passcode-locked
    devices this will typically fail and the caller must fall back to guiding
    the user through the manual Settings toggle - the GUI's error dialog for
    DeveloperModeError should show those exact steps."""
    run(_prompt_enable_developer_mode_async(udid))
