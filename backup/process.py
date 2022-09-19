from .manager import BackupManager
from .cli import cli, CLIContext, read_configuration
from time import time
from datetime import datetime, timedelta
import logging
import time
import click


HOUR_TO_SECONDS: int = 60 * 60
RETRY_IN_MINUTES: int = 10


def parse_time_string(time_string: str) -> int:
    if 'h' not in time_string:
        raise ValueError('Time string should contain "h" sufix')
    time_string = time_string.replace('h', '')
    try:
        time_value: int = int(time_string)
    except:
        raise ValueError(
            'Time string should be integer with "h" sufix specifying how often backups should be made')
    return time_value


def get_next_planned_backup_communicate(wait_hours: int = 0, wait_minutes: int = 0) -> str:
    next_backup_time = datetime.now() + timedelta(hours=wait_hours, minutes=wait_minutes)
    return f'Next planned backup on: {next_backup_time.strftime("%d.%m.%Y %H:%M:%S")}'


@cli.command()
@click.option('--every', type=str, default='6h', help='String containing time interval, with format "{integer}h", specifying how often backup should be done.')
@click.pass_obj
def auto_backups(ctx: CLIContext, every: str):
    """Starts backup process performing backups every time interval"""
    every_hours: int = parse_time_string(every)
    manager = BackupManager(config=read_configuration())
    logging.basicConfig(level=logging.INFO)
    if not ctx.verbose:
        manager.logger.setLevel(logging.ERROR)
        manager.backend.logger.setLevel(logging.ERROR)
    logger = logging.getLogger('Backup process')
    fh = logging.FileHandler(f'./backups.log')
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.info(f'Starting backup process (time interval: {every})')
    logger.info(get_next_planned_backup_communicate(wait_hours=every_hours))
    hours_conter: int = every_hours
    backup_failed: bool = False
    while True:
        if hours_conter == every_hours:
            try:
                print('Starting backup...')
                manager.backup()
                logger.info(click.style(
                    'Successfully performed backup', fg='green'))
                logger.info(get_next_planned_backup_communicate(
                    wait_hours=every_hours))
                backup_failed = False
            except Exception as error:
                logger.error(error)
                logger.error(
                    click.style(
                        f'Failed to perform backup - retry in {RETRY_IN_MINUTES} minutes', fg='red')
                )
                logger.info(get_next_planned_backup_communicate(
                    wait_minutes=RETRY_IN_MINUTES))
                backup_failed = True
        if backup_failed:
            time.sleep(RETRY_IN_MINUTES * 60)
        else:
            time.sleep(HOUR_TO_SECONDS)
            hours_conter += 1
