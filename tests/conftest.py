from __future__ import annotations

import os
import sys
from pathlib import Path

TEST_ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("USE_IN_MEMORY_DB", "1")
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from backend.app import database as _db_module  # noqa: E402
from backend.app.main import app as _app  # noqa: F401,E402


_db_module.init_db()
try:
    from backend.app.main import seed_default_users  # noqa: E402
    seed_default_users()
except Exception:
    pass
