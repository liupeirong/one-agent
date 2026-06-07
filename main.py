import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from my_package import load_config


def main():
    config = load_config()
    print(f"hello, {config.endpoint}, {config.deployment}")


if __name__ == "__main__":
    main()
