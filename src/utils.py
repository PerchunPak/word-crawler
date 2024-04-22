import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
