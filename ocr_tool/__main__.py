"""Allow running as ``python -m ocr_tool``."""
import sys
from .app import main

sys.exit(main())
