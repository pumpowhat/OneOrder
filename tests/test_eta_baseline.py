"""Baseline ETA: cut-off, business calendars, driving days and borders."""

from datetime import date, datetime

import pytest

from backend.services.eta import (
    DriveTime,
    add_business_days,
    baseline_eta,
    get_drive_time,
    is_business_day,
    next_business_day,
)

SHORT = DriveTime(distance_km=40, duration_min=50)
LONG = DriveTime(distance_km=1000, duration_min=700)  # > 9 h -> 2 driving days


def eta(order, origin_type="dc", origin="DK", dest="DK", drive=SHORT):
    return baseline_eta(order, origin_type, origin, dest, drive)


def test_calendar_helpers():
    assert not is_business_day(date(2026, 11, 7), "DK")  # Saturday
    assert not is_business_day(date(2026, 12, 25), "SE")  # Christmas Day
    assert next_business_day(date(2026, 11, 7), "DK") == date(2026, 11, 9)  # Sat -> Mon
    assert add_business_days(date(2026, 11, 6), 1, "DK") == date(2026, 11, 9)  # Fri +1 -> Mon
    assert add_business_days(date(2026, 11, 6), 0, "DK") == date(2026, 11, 6)
    with pytest.raises(ValueError):
        add_business_days(date(2026, 11, 6), -1, "DK")


def test_dc_before_cutoff_delivers_next_business_day():
    r = eta(datetime(2026, 11, 4, 10, 0))  # Wed 10:00
    assert r.dispatch_date == date(2026, 11, 4)
    assert r.arrival_date == date(2026, 11, 5)


def test_after_cutoff_dispatches_next_day():
    r = eta(datetime(2026, 11, 4, 15, 0))  # Wed 15:00
    assert r.dispatch_date == date(2026, 11, 5)
    assert r.arrival_date == date(2026, 11, 6)
    assert any("next business day" in n for n in r.notes)


def test_exactly_at_cutoff_counts_as_after():
    assert eta(datetime(2026, 11, 4, 14, 0)).dispatch_date == date(2026, 11, 5)


def test_friday_afternoon_order_arrives_tuesday():
    r = eta(datetime(2026, 11, 6, 16, 0))  # Fri after cut-off -> Mon dispatch -> Tue
    assert r.dispatch_date == date(2026, 11, 9)
    assert r.arrival_date == date(2026, 11, 10)


def test_branch_can_deliver_same_day():
    r = eta(datetime(2026, 11, 4, 9, 0), origin_type="branch")
    assert r.arrival_date == date(2026, 11, 4)


def test_branch_same_day_skips_closed_destination():
    # Dispatch Fri 2026-11-06 is fine, but a Saturday dispatch is impossible; check holiday dest.
    r = eta(datetime(2026, 12, 24, 9, 0), origin_type="branch", origin="SE", dest="SE")
    assert is_business_day(r.arrival_date, "SE")


def test_holiday_in_destination_postpones_delivery():
    # DC dispatches Thu 24 Dec (DK is open), arrival would be Fri 25 Dec = holiday -> next business day.
    r = eta(datetime(2026, 12, 24, 9, 0), origin="DK", dest="DK")
    assert r.arrival_date == date(2026, 12, 28)


def test_long_haul_adds_driving_day():
    r = eta(datetime(2026, 11, 3, 9, 0), origin_type="branch", drive=LONG)
    assert r.driving_days == 2
    assert r.arrival_date == date(2026, 11, 4)


def test_norway_border_adds_day_but_dk_se_does_not():
    base = datetime(2026, 11, 3, 9, 0)
    dk_se = eta(base, origin="DK", dest="SE")
    dk_no = eta(base, origin="DK", dest="NO")
    assert dk_se.border_days == 0
    assert dk_no.border_days == 1
    assert dk_no.arrival_date > dk_se.arrival_date


def test_arrival_never_before_dispatch_and_always_a_business_day():
    for hour in (8, 13, 14, 20):
        for day in range(2, 30):
            r = eta(datetime(2026, 11, day, hour), origin="SE", dest="NO", drive=LONG)
            assert r.arrival_date >= r.dispatch_date
            assert is_business_day(r.arrival_date, "NO")


def test_unknown_origin_type_rejected():
    with pytest.raises(ValueError, match="origin_type"):
        eta(datetime(2026, 11, 4, 9, 0), origin_type="truck")


def test_with_real_drive_times():
    drive = get_drive_time("DK-BR-04", "SITE-SE-02")
    r = baseline_eta(datetime(2026, 11, 3, 9, 0), "branch", "DK", "SE", drive)
    assert r.arrival_date >= date(2026, 11, 3)
    assert r.driving_days >= 1
