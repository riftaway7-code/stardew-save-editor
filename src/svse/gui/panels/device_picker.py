from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from svse import device as device_layer
from svse.gui.workers.background_tasks import run_in_background


class DevicePickerBar(QWidget):
    """Top bar: pick a device, pick a save folder, pull it. Mirrors the
    manual flow from tonight's live debugging: detect -> pair/dev-mode gate
    -> find app -> list saves -> pull."""

    save_loaded = Signal(str, str)  # udid, folder_name
    status_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._devices: list[device_layer.DeviceInfo] = []
        self._saves: list[device_layer.SaveFolderInfo] = []
        self._worker = None  # keep a reference so Qt doesn't GC it mid-run

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        layout.addWidget(QLabel("Device:"))
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(220)
        layout.addWidget(self.device_combo)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_devices)
        layout.addWidget(self.refresh_button)

        layout.addWidget(QLabel("Save:"))
        self.save_combo = QComboBox()
        self.save_combo.setMinimumWidth(260)
        layout.addWidget(self.save_combo)

        self.load_button = QPushButton("Load Save")
        self.load_button.clicked.connect(self._on_load_clicked)
        self.load_button.setEnabled(False)
        layout.addWidget(self.load_button)

        layout.addStretch()

        self.status_label = QLabel("Not connected")
        layout.addWidget(self.status_label)

        self.device_combo.currentIndexChanged.connect(self._on_device_selected)
        # Deliberately not auto-scanning here - constructing this widget
        # must never have the side effect of touching real USB hardware
        # (breaks testability, and caused a hard crash under pytest-qt's
        # threading context when combined with a background QThread doing
        # asyncio.run() during widget construction). The app entry point
        # calls refresh_devices() explicitly after the window is shown.

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)
        self.status_changed.emit(text)

    # -- Device discovery -------------------------------------------------
    def refresh_devices(self) -> None:
        self._set_status("Scanning for devices...")
        self.device_combo.clear()
        self.save_combo.clear()
        self.load_button.setEnabled(False)
        self._worker = run_in_background(
            self,
            device_layer.list_devices,
            on_success=self._on_devices_found,
            on_error=lambda exc: self._set_status(f"Device scan failed: {exc}"),
        )

    def _on_devices_found(self, devices: list[device_layer.DeviceInfo]) -> None:
        self._devices = devices
        if not devices:
            self._set_status("No devices found. Plug in and unlock the device.")
            return
        for d in devices:
            self.device_combo.addItem(f"{d.name} (iOS {d.ios_version})", userData=d.udid)
        self._set_status(f"Found {len(devices)} device(s)")

    def _on_device_selected(self, index: int) -> None:
        if index < 0:
            return
        udid = self.device_combo.itemData(index)
        if not udid:
            return
        self._check_device_and_list_saves(udid)

    def _check_device_and_list_saves(self, udid: str) -> None:
        self._set_status("Checking pairing / Developer Mode...")
        self.save_combo.clear()
        self.load_button.setEnabled(False)
        self._worker = run_in_background(
            self,
            self._prepare_device,
            udid,
            on_success=self._on_saves_found,
            on_error=lambda exc: self._set_status(str(exc)),
        )

    @staticmethod
    def _prepare_device(udid: str) -> list[device_layer.SaveFolderInfo]:
        """Runs on the background thread: validates pairing/dev-mode/app
        presence, then lists save folders. Raises a device_layer error with
        a user-facing message on any failure - caller shows it as status
        text (a full guided-recovery modal is a later polish-phase item)."""
        status = device_layer.pairing_status(udid)
        if status != device_layer.PairingStatus.PAIRED:
            device_layer.pair(udid)
        dev_status = device_layer.developer_mode_status(udid)
        if dev_status != device_layer.DevModeStatus.ENABLED:
            raise device_layer.DeveloperModeError(
                "Developer Mode is off. Enable it on-device: Settings -> "
                "Privacy & Security -> Developer Mode -> On, then Refresh."
            )
        device_layer.find_stardew_app(udid)
        return device_layer.list_save_folders(udid)

    def _on_saves_found(self, saves: list[device_layer.SaveFolderInfo]) -> None:
        self._saves = saves
        if not saves:
            self._set_status("No Stardew Valley saves found on this device.")
            return
        for s in saves:
            money_text = f"{s.money:,}" if s.money is not None else "?"
            self.save_combo.addItem(f"{s.folder_name} ({money_text}g)", userData=s.folder_name)
        self.load_button.setEnabled(True)
        self._set_status(f"Found {len(saves)} save(s)")

    def _on_load_clicked(self) -> None:
        udid = self.device_combo.currentData()
        folder_name = self.save_combo.currentData()
        if not udid or not folder_name:
            return
        self._set_status(f"Pulling {folder_name}...")
        self.load_button.setEnabled(False)
        self._worker = run_in_background(
            self,
            lambda: (udid, folder_name),
            on_success=self._on_pull_ready,
            on_error=lambda exc: self._set_status(f"Failed to load save: {exc}"),
        )

    def _on_pull_ready(self, result: tuple[str, str]) -> None:
        udid, folder_name = result
        self._set_status(f"Loaded {folder_name}")
        self.load_button.setEnabled(True)
        self.save_loaded.emit(udid, folder_name)
