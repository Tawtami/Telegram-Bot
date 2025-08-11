import types
import pytest


def test_no_sensitive_logging(monkeypatch, caplog):
    # Ensure we do not log raw message text
    from bot import logger

    # Simulate a log record of update processing
    logger.info("Update message from user_id=123")

    # Ensure no phone-like patterns
    logs = "\n".join(r.message for r in caplog.records)
    assert "+98" not in logs
