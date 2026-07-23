class DeviceError(Exception):
    """Base class for all device-layer errors."""


class DeviceNotFoundError(DeviceError):
    """No USB device with the given identifier is connected."""


class NotPairedError(DeviceError):
    """Device requires the on-device Trust dialog to be accepted."""


class DeveloperModeError(DeviceError):
    """Developer Mode is off, or needs the on-device confirmation flow."""


class AppNotFoundError(DeviceError):
    """Stardew Valley is not installed on the target device."""


class HouseArrestError(DeviceError):
    """Could not open the app's Documents sandbox via house_arrest."""


class SaveNotFoundError(DeviceError):
    """The requested save folder does not exist on the device."""
