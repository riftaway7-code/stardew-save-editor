from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PairingStatus(Enum):
    NOT_PAIRED = "not_paired"
    PAIRED = "paired"


class DevModeStatus(Enum):
    UNKNOWN = "unknown"
    DISABLED = "disabled"
    PENDING_REBOOT = "pending_reboot"
    ENABLED = "enabled"


@dataclass
class DeviceInfo:
    udid: str
    name: str
    ios_version: str
    device_class: str


@dataclass
class SaveFolderInfo:
    folder_name: str
    farm_name: str
    unique_id: str
    money: int | None
    days_played: int | None


STARDEW_BUNDLE_ID = "com.chucklefish.stardewvalley"
