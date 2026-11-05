"""Checks on the precomputed drive-time table used by the ETA model."""

import pytest

from backend.services.eta import get_drive_time, load_drive_times
from backend.services.orchestration import haversine_km, load_sites, load_warehouses


def test_table_covers_every_warehouse_site_pair():
    table = load_drive_times()
    expected = {f"{w.code}|{s.id}" for w in load_warehouses() for s in load_sites()}
    assert set(table) == expected


def test_values_are_positive():
    for key, dt in load_drive_times().items():
        assert dt.distance_km > 0, key
        assert dt.duration_min > 0, key


def test_road_distance_is_never_shorter_than_straight_line():
    sites = {s.id: s for s in load_sites()}
    for w in load_warehouses():
        for site in sites.values():
            crow = haversine_km(w.latitude, w.longitude, site.latitude, site.longitude)
            road = get_drive_time(w.code, site.id).distance_km
            assert road >= crow * 0.95, f"{w.code}->{site.id}: road {road} < crow {crow:.1f}"


def test_average_speed_is_plausible():
    for key, dt in load_drive_times().items():
        if dt.distance_km >= 50:
            speed = dt.distance_km / (dt.duration_min / 60)
            assert 25 <= speed <= 120, f"{key}: {speed:.0f} km/h"


def test_cross_water_pair_is_much_longer_than_straight_line():
    """Jutland branch to a Swedish site has to detour via the Oresund bridge."""
    assert get_drive_time("DK-BR-04", "SITE-SE-02").distance_km > 400


def test_unknown_pair_raises_clear_error():
    with pytest.raises(KeyError, match="NOPE"):
        get_drive_time("NOPE", "SITE-DK-01")
