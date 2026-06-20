from datetime import UTC, datetime

from app.ratelimit.limiter import ATOMIC_DAILY_COUNTER_SCRIPT, seconds_until_next_utc_midnight


def test_rate_limit_script_sets_expiry_atomically():
    assert "redis.call('INCR'" in ATOMIC_DAILY_COUNTER_SCRIPT
    assert "redis.call('EXPIRE'" in ATOMIC_DAILY_COUNTER_SCRIPT


def test_seconds_until_midnight_utc():
    now = datetime(2026, 6, 19, 23, 59, 0, tzinfo=UTC)
    assert seconds_until_next_utc_midnight(now) == 60
