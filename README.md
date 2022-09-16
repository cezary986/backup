# Backup

Pakiet do automatycznych backupów

## Konfiguracja

W katalogu gdzie wywoływane są komendy powinien znajdować się plik
z konfiguracją o nazwie `.backup.config.py` która zawiera zmianną `config`. 

Przykładowy plik konfiguracyjny:
```python
from backup.manager import BackupConfiguration
from backup.mega_backend import MegaBackupBackend
import os

config = BackupConfiguration(
    # użycie chmury mega.nz do przechowywania backupów
    backend=MegaBackupBackend(login='cezary.maszczyk@gmail.com'),
    # scieżki z "paths_to_backup" względne względem root_dir
    root_dir=os.path.dirname(os.path.realpath(__file__)),
    root_cloud_dir='/experiments/tests',
    # które pliki i foldery mają się backup-ować
    paths_to_backup=[
        './to_backup/test.txt',
        './to_backup/results',
    ]
)
```

## Możliwości użycia


### 1. Wykonanie ręcznego backupu

```bash
python -m backup backup
```

### 2. Automatyczne backupy co określony interwał godzinowy

Backup co 3 godziny
```bash
python -m backup auto-backups --every 3h
```

> Jeżeli backup nie powiedzie się to próba zostanie ponowiona po 10 minutach

> Backup automatycznie kończy się niepowodzeniem jeżeli którakolwiek ze scieżek skonfigurowanych do backupu przestanie istnień na dysku lokalnym (pliki zostały potencjalnie utracone).

### 3. Przywracanie plików

```bash
python -m backup restore
```

Komenda przywróci wszystkie foldery i pliki na podstawie backupu.