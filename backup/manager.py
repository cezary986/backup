import json
from datetime import datetime, timezone
from logging import Logger
import os
import click
import shutil
from typing import Dict, List, TypedDict
from zipfile import ZipFile
from .backend import *


class BackupConfiguration:
    """Class for configuring backups
    """

    def __init__(
        self,
        backend: BackupBackend,
        root_cloud_dir: str,
        paths_to_backup: List[str],
        tmp_dir_path: str = './tmp',
        root_dir: str = os.curdir,
    ) -> None:
        """
        Args:
            backend (BackupBackend): backup backend to use
            root_cloud_dir (str): root dictory in cloud where backups will be saved
            paths_to_backup (List[str]): paths which should be backup
            tmp_dir_path (str, optional): path to temporary folder used when making backups. Defaults to './tmp'.
            root_dir (str): root dictory containing files to be backed up, path_to_backup can be relative to this path. Default is current working dir
        """
        self.backend: BackupBackend = backend
        self.root_dir: str = root_dir
        self.root_cloud_dir: str = root_cloud_dir
        self.paths_to_backup: List[str] = paths_to_backup
        self.tmp_dir_path: str = tmp_dir_path


class BackupPathMetaData(TypedDict):
    path: str
    is_file: bool
    extract_path: str


class BackMetaData(TypedDict):
    creation_timestamp_utc: float
    paths_mapping: Dict[str, BackupPathMetaData]


class BackupManager:

    BACKUP_DEFAULT_FILENAME: str = 'backup'
    OLD_BACKUP_DEFAULT_FILENAME: str = '_old_backup'
    META_FILENAME: str = '__meta__.json'

    def __init__(
        self,
        config: BackupConfiguration
    ) -> None:
        self.config: BackupConfiguration = config
        self.backend: BackupBackend = config.backend
        self.logger: Logger = self.backend.logger
        self.logger.info(
            f'Initializing backup manager using backup backend: {self.backend.__class__.__name__}')

    def _write_meta_file(self, backup_tmp_dir: str):
        meta_file_content: BackMetaData = {
            'creation_timestamp_utc': datetime.now(tz=timezone.utc).timestamp(),
            'paths_mapping': {
                f'{i}.zip': {
                    'path': path,
                    'extract_path': path if os.path.isdir(path) else os.path.dirname(path)
                } for i, path in enumerate(self.config.paths_to_backup)
            }
        }

        with open(f'{backup_tmp_dir}/{BackupManager.META_FILENAME}', 'w+') as meta_file:
            json.dump(meta_file_content, meta_file)

    def _validate_before_backup(self) -> None:
        paths_not_existing: List[str] = []
        for path_to_backup in self.config.paths_to_backup:
            if not os.path.exists(path_to_backup):
                paths_not_existing.append(path_to_backup.replace('\\', '/'))
        if len(paths_not_existing) > 0:
            error = Exception(
                click.style(
                    'Some of the paths specified for backup does not exists. See logs for details', fg='red')
            )
            self.logger.error(error)
            self.logger.error(
                click.style(
                    f'Following paths specified for backup does not exist: [{f", ".join(paths_not_existing)}]', fg='red'))
            raise error

    def backup(self) -> None:
        """Backup paths specified in config using backup backend 
        """
        self._validate_before_backup()
        # clear tmp director if exist and recreate it
        if os.path.exists(self.config.tmp_dir_path):
            shutil.rmtree(self.config.tmp_dir_path, ignore_errors=True)
        backup_tmp_dir: str = os.path.join(self.config.tmp_dir_path, 'tmp')
        os.makedirs(backup_tmp_dir, exist_ok=True)

        # for every folder to backup zip it to tmp_folder
        for file_id, path_to_backup in enumerate(self.config.paths_to_backup):
            zile_file_path: str = os.path.join(
                backup_tmp_dir, f'{file_id}.zip')
            if os.path.isdir(path_to_backup):
                # use shutil to zip whole directory
                shutil.make_archive(zile_file_path.removesuffix(
                    '.zip'), 'zip', path_to_backup)
            else:
                # use zipfile to zip single file
                with ZipFile(zile_file_path, 'w') as zipf:
                    zipf.write(path_to_backup,
                               arcname=os.path.basename(path_to_backup))

        # create meta file to later easily retrieve directories structures
        self._write_meta_file(backup_tmp_dir)

        # zip everything (folders and meta file)
        backup_file_path: str = f'{self.config.tmp_dir_path}/{BackupManager.BACKUP_DEFAULT_FILENAME}'
        shutil.make_archive(backup_file_path, 'zip', backup_tmp_dir)
        shutil.rmtree(backup_tmp_dir)

        try:
            # create directory in cloud for backup (if not exist, otherwise do nothing)
            self.backend.create_folder_if_not_exists(self.config.root_cloud_dir)
            old_backup_file: BackupFile = self.backend.get_file_by_path(
                f'{self.config.root_cloud_dir}/{BackupManager.BACKUP_DEFAULT_FILENAME}.zip'
            )
            if old_backup_file is not None:
                self.backend.rename_file(
                    old_backup_file, f'{BackupManager.OLD_BACKUP_DEFAULT_FILENAME}.zip'
                )
            try:
                self.backend.upload_file(
                    f'{backup_file_path}.zip', self.config.root_cloud_dir)
            except Exception as e:
                # error uploading backup file - shit... - at least recover latest backup file name
                if old_backup_file is not None:
                    self.backend.rename_file(
                        old_backup_file, f'{BackupManager.BACKUP_DEFAULT_FILENAME}.zip'
                    )
                raise e
            finally:
                os.remove(f'{backup_file_path}.zip')
            # everything was ok - remove old backup file if exist
            if old_backup_file is not None:
                self.backend.remove_file(old_backup_file)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            self.logger.error(
                click.style(
                    f'Fail to backup files using using backup backend: {self.backend.__class__.__name__}', fg='red')
            )
            return  # fails silently
        self.logger.info(click.style(
            'Backup finished with success!', fg='green'))

    def restore(self) -> None:
        """Restores files from backup
        """
        os.makedirs(self.config.tmp_dir_path, exist_ok=True)
        backup_file_path: str = os.path.join(
            self.config.root_cloud_dir, f'{BackupManager.BACKUP_DEFAULT_FILENAME}.zip')
        backup_file: BackupFile = self.backend.get_file_by_path(
            backup_file_path)
        if backup_file is None:
            print(
                f'Fail to restore from backup - no backup.zip file exist in configured path: "{os.path.dirname(backup_file_path)}", there is no hope left :(')
            return
        else:
            self.backend.download_file(backup_file, self.config.tmp_dir_path)
            downloaded_file_path = os.path.join(
                self.config.tmp_dir_path, f'{BackupManager.BACKUP_DEFAULT_FILENAME}.zip')
            extracted_backup_path: str = os.path.join(
                self.config.tmp_dir_path, 'downloaded_backup')
            with ZipFile(downloaded_file_path, 'r') as zip_ref:
                zip_ref.extractall(extracted_backup_path)
            # read meta file
            with open(f'{extracted_backup_path}/{BackupManager.META_FILENAME}', 'r') as meta_file:
                meta_file_content: BackMetaData = json.load(meta_file)
            # recreate folder structure
            for zip_file_name, path_meta in meta_file_content['paths_mapping'].items():
                with ZipFile(os.path.join(extracted_backup_path, zip_file_name), 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(
                        self.config.root_dir, path_meta['extract_path']))
            backup_date: datetime = datetime.fromtimestamp(
                meta_file_content['creation_timestamp_utc'], tz=timezone.utc)
            backup_date = backup_date.astimezone(tz=None)  # to local timestamp
            print(click.style(
                f'Files restored successfully from cloud backup.', fg='green'))
            print(f'Backup date: {backup_date.strftime("%d.%m.%Y %H:%M:%S")}')
            print(f'Restored {len(meta_file_content["paths_mapping"])} paths:')
            for path_meta in meta_file_content['paths_mapping'].values():
                print(f'     * "{path_meta["path"]}"')
            shutil.rmtree(self.config.tmp_dir_path)
