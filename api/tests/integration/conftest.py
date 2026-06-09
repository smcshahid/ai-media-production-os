"""Integration-test fixtures.

On Windows the default ``ProactorEventLoop`` is incompatible with ``psycopg``'s
async mode, so select the ``SelectorEventLoop`` policy before pytest-asyncio
creates the loop. No-op on Linux/CI, where these tests normally run.
"""

from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
