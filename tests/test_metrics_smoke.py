import pytest


@pytest.mark.asyncio
async def test_metrics_counters_increment():
    from utils.performance_monitor import monitor
    monitor.increment_counter("registrations")
    monitor.increment_hourly("participant_pushes")
    stats = await monitor.get_stats()
    assert stats["counters"].get("registrations", 0) >= 1
    assert stats["hourly"].get("participant_pushes", 0) >= 1


