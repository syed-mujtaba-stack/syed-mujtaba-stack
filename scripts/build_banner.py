"""Entry point: python scripts/build_banner.py [photo_path]."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from banner import build  # noqa: E402

if __name__ == "__main__":
    photo = sys.argv[1] if len(sys.argv) > 1 else "assets/photo/placeholder.jpg"
    build.main(photo)