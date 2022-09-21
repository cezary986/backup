
from abc import ABC, abstractmethod
from logging import Logger, getLogger
from getpass import getpass


class BackupFolder:
    name: str
    path: str
    id: str

class BackupFile(BackupFolder):
    parent_dir: BackupFolder


class BackupBackend(ABC):

    def __init__(
        self,
        login: str = None,
        password: str = None
    ) -> None:
        self.logger: Logger = getLogger('Backup')
        
        while True:
            if login is None or password is None:
                print('Type in your backup backend credentials:')
            if login is None:
                login = input('login: ')
            if password is None:
                password = getpass('password: ')
            try:
                self._login(login, password)
                return
            except Exception:
                print('Login failed likely due to invalid credentials. Try again')
                login = None
                password = None

    @abstractmethod
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
        raise Exception('Not implemented exception')

    @abstractmethod
    def get_file_by_path(self, path: str) -> BackupFile:
        """Finds and returns file by its path 

        Args:
            path (str): path to file

        Returns:
            Union[BackupFile, BackupFolder]: file
        """
        raise Exception('Not implemented exception')

    @abstractmethod
    def create_folder_if_not_exists(self, path: str) -> BackupFolder:
        """Creates folder with given path, do nothing if folder already exists

        Args:
            path (str): folder path

        Returns:
            BackupFolder: created folder object
        """
        raise Exception('Not implemented exception')

    @abstractmethod
    def upload_file(self, file_path: str, directory_path: str) -> BackupFile:
        """Uploads file by local path to cloud directory.

        Args:
            file_path (str): local path for file to upload
            directory_path (str): path to directory in cloud where file should be uploaded

        Returns:
            BackupFile: uploaded file object
        """
        raise Exception('Not implemented exception')

    @abstractmethod
    def rename_file(self, file: BackupFile, new_name: str) -> None:
        """Renames file.

        Args:
            file (BackupFile): file to rename
            new_name (str)
        """
        raise Exception('Not implemented exception')

    @abstractmethod
    def remove_file(self, file: BackupFile) -> None:
        """Removes file (not reversable) from cloud directory

        Args:
            file (MegaBackupFile): file to remove
        """
        raise Exception('Not implemented exception')

    @abstractmethod
    def download_file(self, file: BackupFile, output_path: str) -> None:
        """Download file from backend

        Args:
            file (BackupFile): file
        """
        raise Exception('Not implemented exception')