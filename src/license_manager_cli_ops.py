"""LicenseManagerCliOps."""
import os
import logging
import subprocess
from pathlib import Path
from shutil import rmtree, chown

from jinja2 import Environment, FileSystemLoader


logger = logging.getLogger()


class LicenseManagerCliOps:
    """Track and perform license-manager-cli ops."""

    _PYTHON_BIN = Path("/usr/bin/python3.6")
    _PACKAGE_NAME = "license-manager-cli"
    _LOG_DIR = Path("/var/log/license-manager-cli")
    _CACHE_DIR = Path("/var/cache/license-manager-cli")
    _ETC_DEFAULT = Path("/etc/default/lm-cli")
    _BIN_SCRIPT = Path("/usr/local/bin/lm-cli")
    _VENV_DIR = Path("/srv/license-manager-cli-venv")
    _VENV_PYTHON = _VENV_DIR.joinpath("bin", "python").as_posix()
    _SLURM_USER = "slurm"
    _SLURM_GROUP = "slurm"

    def __init__(self, charm):
        """Initialize license-manager-cli-ops."""
        self._charm = charm

    def install(self):
        """Install license-manager-cli and setup ops."""

        # Setup log dir
        self.setup_log_dir()

        # Setup cache dir
        self.setup_cache_dir()
        
        # Create the virtualenv
        create_venv_cmd = [
            self._PYTHON_BIN.as_posix(),
            "-m",
            "venv",
            self._VENV_DIR.as_posix(),
        ]
        subprocess.call(create_venv_cmd)
        logger.debug("license-manager-cli virtualenv created")

        # Ensure pip
        ensure_pip_cmd = [
            self._VENV_PYTHON,
            "-m",
            "ensurepip",
        ]
        subprocess.call(ensure_pip_cmd)
        logger.debug("pip ensured")

        # Ensure we have the latest pip
        upgrade_pip_cmd = [
            self._VENV_PYTHON,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "pip",
        ]
        subprocess.call(upgrade_pip_cmd)

        # Install license-manager-cli package
        pip_install_cmd = [
            self._VENV_PYTHON,
            "-m",
            "pip",
            "install",
            self._PACKAGE_NAME,
        ]
        logger.debug(f"## Running: {pip_install_cmd}")
        try:
            out = subprocess.check_output(pip_install_cmd, env={}).decode().strip()
            logger.debug("license-manager-cli installed")
            logger.debug(f"## pip install output: {out}")
        except Exception as e:
            logger.error(f"Error installing license-manager-cli: {e}")
            raise Exception("license-manager-cli not installed.")

        # Create the lm-cli script file
        self.configure_bin_script()

        # Create the etc/default/lm-cli file
        self.configure_etc_default()


    def setup_cache_dir(self):
        """Set up cache dir."""

        # Delete cache dir if it already exists
        if self._CACHE_DIR.exists():
            rmtree(self._CACHE_DIR, ignore_errors=True)
        # Create a clean cache dir
        self._CACHE_DIR.mkdir(parents=True)
        chown(self._CACHE_DIR.as_posix(), self._SLURM_USER, self._SLURM_GROUP)
        self._CACHE_DIR.chmod(0o700)


    def setup_log_dir(self):
        """Set up log dir."""

        # Create log dir
        if not self._LOG_DIR.exists():
            self._LOG_DIR.mkdir(parents=True)
        chown(self._LOG_DIR.as_posix(), self._SLURM_USER, self._SLURM_GROUP)
        self._LOG_DIR.chmod(0o700)


    def upgrade(self, version: str):
        """Upgrade license-manager-cli package to specified version."""

        pip_install_cmd = [
            self._VENV_PYTHON,
            "-m",
            "pip",
            "--upgrade",
            f"{self._PACKAGE_NAME}=={version}",
        ]

        out = subprocess.check_output(pip_install_cmd).decode().strip()
        if "Successfully installed" not in out:
            logger.error("Trouble upgrading license-manager-cli, please debug")
            raise Exception("license-manager-cli not upgraded.")
        else:
            logger.debug("license-manager-cli upgraded")

        # Clear cache dir after upgrade to avoid stale data
        self.setup_cache_dir()


    def configure_etc_default(self):
        """Create the default env file with the charm's configurations."""
        charm_config = self._charm.model.config

        # Get the values from the charm's configurations
        ctx = {k.replace("-", "_"): v for k, v in charm_config.items()}

        template_dir = Path("./src/templates/")
        template_file = "license-manager-cli.defaults.template"
        environment = Environment(loader=FileSystemLoader(template_dir))
        template = environment.get_template(template_file)

        rendered_template = template.render(ctx)

        if self._ETC_DEFAULT.exists():
            self._ETC_DEFAULT.unlink()

        self._ETC_DEFAULT.write_text(rendered_template)


    def configure_bin_script(self):
        """Create the lm-cli executable script."""
        template_dir = Path("./src/templates/")
        template_file = "license-manager-cli.script.template"
        environment = Environment(loader=FileSystemLoader(template_dir))
        template = environment.get_template(template_file)

        rendered_template = template.render(lm_cli_venv_path=self._VENV_DIR.as_posix())

        if self._BIN_SCRIPT.exists():
            self._BIN_SCRIPT.unlink()

        self._BIN_SCRIPT.write_text(rendered_template)
        self._BIN_SCRIPT.chmod(0o755)


    def remove_license_manager_cli(self):
        """Remove the things we have created."""
        
        # Remove the defaut env file
        if self._ETC_DEFAULT.exists():
            self._ETC_DEFAULT.unlink()

        # Remove the lm-cli script
        if self._BIN_SCRIPT.exists():
            self._BIN_SCRIPT.unlink()
        
        # Delete the directories created
        rmtree(self._LOG_DIR.as_posix(), ignore_errors=True)
        rmtree(self._CACHE_DIR.as_posix(), ignore_errors=True)
        rmtree(self._VENV_DIR.as_posix(), ignore_errors=True)
