import click
import os
import sys
import importlib
import logging
from .manager import BackupManager, BackupConfiguration


def read_configuration() -> BackupConfiguration:
    config_file_path: str = os.path.join(os.curdir, '.backup.config.py')
    if not os.path.exists(config_file_path):
        raise Exception(
            'Backup configuration file does not exist. It shoud be named ".backup.config.py" and placed in current working directory')
    spec = importlib.util.spec_from_file_location(
        "backup_config", config_file_path)
    backup_config = importlib.util.module_from_spec(spec)
    sys.modules["module.name"] = backup_config
    spec.loader.exec_module(backup_config)
    config: BackupConfiguration = backup_config.config
    return config


class CLIContext(object):

    def __init__(self, verbose: bool) -> None:
        self.verbose: bool = verbose


@click.group()
@click.option('--verbose', default=True,
              envvar='VERBOSE')
@click.pass_context
def cli(ctx: click.Context, verbose: bool):
    """Backup package CLI"""
    ctx.obj = CLIContext(
        verbose=verbose
    )


@cli.command()
@click.pass_obj
def backup(ctx: CLIContext):
    """Perform backup"""
    logger = logging.getLogger('Backup')
    manager = BackupManager(config=read_configuration())
    logging.basicConfig(level=logging.INFO)
    logger.info('Starting backup...')
    if not ctx.verbose:
        manager.logger.setLevel(logging.ERROR)
        manager.backend.logger.setLevel(logging.ERROR)
    manager.backup()


@cli.command()
@click.pass_obj
def restore(ctx: CLIContext):
    """Restores files from backup"""
    logger = logging.getLogger('Restore')
    manager = BackupManager(config=read_configuration())
    logging.basicConfig(level=logging.INFO)
    logger.info('Restoring files from backup...')
    if not ctx.verbose:
        manager.logger.setLevel(logging.ERROR)
        manager.backend.logger.setLevel(logging.ERROR)
    try:
        manager.restore()
    except Exception:
        logger.error(click.style(
            f'''Failed to restore file from cloud backup. Whats now?
            
            Go to you cloud provider (depending on used backend) and check if path "{manager.config.root_cloud_dir}" exist in your backup cloud.

                Yes: Download file backup.zip from that location and restore manually from it.
                No: Everything is lost, no hope is left
            ''',
            fg='red'))