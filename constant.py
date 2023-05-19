import sys
from pathlib import Path

BASE_PATH = Path(sys.argv[0]).parent.resolve()

__all__ = ['BASE_PATH']

if __name__ == "__main__":
    for k, v in locals().copy().items():
        if not k.startswith("__"):
            print(f"{k}: {v}")
