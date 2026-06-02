"""Tiny indirection so token_logger / hallucination don't import the DB layer
directly (keeps agents unit-testable). The engine sets these at startup.

    from app.monitoring import persistence
    persistence.write_token_log = my_db_writer
"""
from typing import Callable, Optional

write_token_log: Optional[Callable] = None
write_hallucination_check: Optional[Callable] = None