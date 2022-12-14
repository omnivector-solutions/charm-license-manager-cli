#!/usr/bin/env python3
"""License Manager CLI Charm."""
import logging
from pathlib import Path

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import ActiveStatus, BlockedStatus

from license_manager_cli_ops import LicenseManagerCliOps

logger = logging.getLogger()


class LicenseManagerCliCharm(CharmBase):
    """Facilitate License Manager CLI lifecycle."""

    _stored = StoredState()

    def __init__(self, *args):
        """Initialize and observe."""
        super().__init__(*args)

        self._stored.set_default(
            installed=False,
            init_started=False,
        )

        self._license_manager_cli_ops = LicenseManagerCliOps(self)

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.config_changed: self._on_config_changed,
            self.on.remove: self._on_remove,
            self.on.upgrade_action: self._on_upgrade_action,
            self.on.show_version_action: self._on_show_version_action,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    def _on_install(self, event):
        """Install license-manager-cli."""
        self.unit.set_workload_version(Path("version").read_text().strip())
        try:
            self._license_manager_cli_ops.install()
        except Exception as e:
            logger.error(f"Error installing license-manager-cli: {e}")
            self.unit.status = BlockedStatus("Installation error")
            event.defer()
            raise

        self.unit.set_workload_version(Path("version").read_text().strip())

        # Log and set status
        logger.debug("license-manager-cli installed")
        self.unit.status = ActiveStatus("license-manager-cli installed")
        self._stored.installed = True

    def _on_upgrade(self, event):
        """Perform upgrade operations."""
        self.unit.set_workload_version(Path("version").read_text().strip())

    def _on_show_version_action(self, event):
        """Show the info and version of license-manager-cli."""
        info = self._license_manager_cli_ops.get_version_info()
        event.set_results({"license-manager-cli": info})

    def _on_config_changed(self, event):
        """Configure license-manager-cli with charm config."""
        # Write out the /etc/default/lm-cli config
        self._license_manager_cli_ops.configure_etc_default()

    def _on_remove(self, event):
        """Remove directories and files created by license-manager-cli charm."""
        self._license_manager_cli_ops.remove_license_manager_cli()

    def _on_upgrade_action(self, event):
        """Upgrade the license-manager-cli package."""
        version = event.params["version"]
        try:
            self._license_manager_cli_ops.upgrade(version)
            event.set_results({"upgrade": "success"})
            self.unit.status = ActiveStatus(f"Updated to version {version}")
        except Exception:
            self.unit.status = BlockedStatus(f"Error updating to version {version}")
            event.fail()


if __name__ == "__main__":
    main(LicenseManagerCliCharm)
