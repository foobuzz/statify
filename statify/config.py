import os
from pathlib import Path

VERSION = '1.2.0'

STATIFY_PATH = Path(os.environ.get('STATIFY_DATA',
                    Path.home() / '.data' / 'statify'))

CONFIG_PATH = Path(os.environ.get('STATIFY_CONFIG',
                   Path.home() / '.config' / 'statify.yaml'))
