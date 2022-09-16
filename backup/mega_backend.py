from __future__ import annotations
import os
from typing import List
from .backend import *
from .mega import Mega


class MegaBackupFolder:
    name: str
    path: str
    id: str


class MegaBackupFile(BackupFolder):
    parent_dir: MegaBackupFolder
    _response: dict

    @staticmethod
    def from_api_response(response: dict, parent_dir_path: str) -> MegaBackupFile:
        file = MegaBackupFile()
        file.id = response['h']
        file.name = response['a']['n']
        file.parent_dir = parent_dir_path
        file.path = f'{parent_dir_path}/{file.name}'
        file._response = response
        return file


class MegaBackupBackend(BackupBackend):
    """Backup backend using mega.nz cloud.
    You will need free mega account to use it
    """

    def __init__(
        self,
        login: str = None,
        password: str = None
    ) -> None:
        """
        Args:
            login (str, optional): if not specified it will be prompted
            password (str, optional): if not specified it will be prompted
        """
        self.m: Mega = None
        super().__init__(login, password)

    def _login(
            self,
            login: str,
            password: str
    ) -> None:
        """Authorizes backend using login and password. Method called
        in a constructor.

        Args:
            login (str): login
            password (str): password
        """
        self.m = Mega()
        try:
            self.m.login(
                login,
                password
            )
        except Exception as e:
            self.logger.error(e, exc_info=True)
            raise e


    def _get_folder_by_path(self, path: str) -> MegaBackupFolder:
        # Retreive file parent dir folder - it could not be root folder! never!
        try:
            folder_id: str = self.m.find(path)[0]
            folder: MegaBackupFolder = MegaBackupFolder()
            folder.id = folder_id
            folder.path = path
            folder.name = os.path.basename(path)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            e = Exception(
                f'Failed to find directory with path: "{path}" on your Mega cloud. Check if directory exist. See logs for more details')
            self.logger.error(e, exc_info=True)
            raise e
        return folder

    def get_file_by_path(self, path: str) -> MegaBackupFile:
        """Finds and returns file by its path 

        Args:
            path (str): path to file

        Returns:
            Union[BackupFile, BackupFolder]: file
        """
        # parent dir folder could not be root cloud folder! never!
        parent_folder: MegaBackupFolder = self._get_folder_by_path(
            os.path.dirname(path))
        response = self.m.get_files_in_node(parent_folder.id)
        files: List[MegaBackupFile] = [
            MegaBackupFile.from_api_response(e, parent_folder.path) for e in response.values()
        ]
        file: MegaBackupFile = None
        for file in files:
            if file.path == path:
                return file
        return file

    def create_folder(self, path: str) -> BackupFolder:
        """Creates folder with given path, do nothing if folder already exists

        Args:
            path (str): folder path

        Returns:
            BackupFolder: created folder object
        """
        dirs = self.m.create_folder(path)
        folder: MegaBackupFolder = MegaBackupFolder()

        folder_name: str = os.path.basename(path)
        folder.id = dirs[folder_name]
        folder.path = path
        folder.name = folder_name
        return folder

    def upload_file(self, file_path: str, directory_path: str) -> BackupFile:
        """Uploads file by local path to cloud directory.

        Args:
            file_path (str): local path for file to upload
            directory_path (str): path to directory in cloud where file should be uploaded

        Returns:
            BackupFile: uploaded file object
        """
        parent_dir: MegaBackupFolder = self._get_folder_by_path(directory_path)
        try:
            self.m.upload(file_path, parent_dir.id)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            e = Exception(
                f'Failed to upload local file "{file_path}" to backup Mega cloud folder: "{directory_path}". See logs to details')
            self.logger.error(e, exc_info=True)
            raise e

    def rename_file(self, file: MegaBackupFile, new_name: str) -> None:
        """Renames file.

        Args:
            file (BackupFile): file to rename
            new_name (str): new file name
        """
        try:
            self.m.rename([None, file._response], new_name)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            e = Exception(
                f'Failed to rename cloud file "{file.path}" to "{new_name}". See logs to details')
            self.logger.error(e, exc_info=True)
            raise e

    def remove_file(self, file: MegaBackupFile) -> None:
        """Removes file (not reversable) from cloud directory

        Args:
            file (MegaBackupFile): file to remove
        """
        try:
            self.m.destroy(file.id)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            e = Exception(
                f'Failed to delete cloud file "{file.path}" while replacing backup files. See logs to details')
            self.logger.error(e, exc_info=True)
            raise e

    def download_file(self, file: MegaBackupFile, output_path: str) -> None:
        """Download file from backend

        Args:
            file (MegaBackupFile): file
        """
        try:
            self.m.download([file.id, file._response], output_path)
        except Exception as e:
            self.logger.error(e, exc_info=True)
            e = Exception(
                f'Failed to download cloud file "{file.path}". See logs to details')
            self.logger.error(e, exc_info=True)
            raise e
