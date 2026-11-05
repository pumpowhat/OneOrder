"""Deterministic baseline ETA: the earliest arrival date given business calendars and driving time.

This is the first layer of the ETA model. It answers "when would this shipment arrive if nothing
goes wrong?" using real driving times and national holidays. The ML layer (later) learns the
extra delay on top of it and turns it into P50 / P90.

Assumptions (all overridable through ``BaselineConfig``):
- Orders placed before the cut-off on a business day are dispatched that day; later orders on the
  next business day. The cut-off is 14:00 for DCs and 11:00 for branches (a branch must pick, load
  and deliver within the site's receiving hours). Dispatch day is judged by the *origin* calendar.
- A truck covers at most 8 hours of driving a day: the EU limit is 9 h (Reg. 561/2006) with a
  45 min break per 4.5 h, and unloading takes time too. Longer trips take extra days.
- Deliveries happen on business days of the *destination* country only. Christmas Eve and New
  Year's Eve are treated as closed in all three countries although they are not public holidays.
- Branches can deliver the day they dispatch, DCs need one business day of pick-and-pack.
- Crossing a border adds customs/handling days only when Norway (outside the EU) is involved.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from functools import lru_cache
import math

import holidays

from .drive_times import DriveTime

# Weekend days: Saturday=5, Sunday=6 (date.weekday()).
_WEEKEND = (5, 6)
# Not public holidays, but in practice nobody delivers: (month, day).
_DE_FACTO_CLOSED = frozenset({(12, 24), (12, 31)})


@dataclass(frozen=True)
class BaselineConfig:
    cutoff: dict[str, time] = field(
        default_factory=lambda: {"branch": time(11, 0), "dc": time(14, 0)}
    )
    max_driving_minutes_per_day: int = 8 * 60
    pick_pack_days: dict[str, int] = field(default_factory=lambda: {"branch": 0, "dc": 1})
    # Extra business days when the shipment crosses a border involving a non-EU country.
    non_eu_countries: frozenset[str] = frozenset({"NO"})
    non_eu_border_days: int = 1


@dataclass(frozen=True)
class BaselineETA:
    dispatch_date: date
    arrival_date: date
    business_days_after_dispatch: int
    driving_days: int
    pick_pack_days: int
    border_days: int
    notes: tuple[str, ...]


@lru_cache(maxsize=8)
def _holidays(country: str) -> holidays.HolidayBase:
    return holidays.country_holidays(country)


def is_business_day(day: date, country: str) -> bool:
    return (
        day.weekday() not in _WEEKEND
        and (day.month, day.day) not in _DE_FACTO_CLOSED
        and day not in _holidays(country)
    )


def next_business_day(day: date, country: str) -> date:
    """``day`` itself if it is a business day, otherwise the next one."""
    while not is_business_day(day, country):
        day += timedelta(days=1)
    return day


def add_business_days(day: date, count: int, country: str) -> date:
    """Move forward ``count`` business days of ``country`` (``count`` may be 0)."""
    if count < 0:
        raise ValueError("count must be >= 0")
    current = day
    remaining = count
    while remaining > 0:
        current += timedelta(days=1)
        if is_business_day(current, country):
            remaining -= 1
    return current


def dispatch_date(
    order_time: datetime, origin_type: str, origin_country: str, config: BaselineConfig
) -> date:
    """First day the warehouse can send the goods, given the cut-off and its national calendar."""
    day = order_time.date()
    if order_time.time() >= config.cutoff[origin_type]:
        day += timedelta(days=1)
    return next_business_day(day, origin_country)


def border_delay_days(origin_country: str, dest_country: str, config: BaselineConfig) -> int:
    if origin_country == dest_country:
        return 0
    if origin_country in config.non_eu_countries or dest_country in config.non_eu_countries:
        return config.non_eu_border_days
    return 0


def baseline_eta(
    order_time: datetime,
    origin_type: str,
    origin_country: str,
    dest_country: str,
    drive: DriveTime,
    config: BaselineConfig | None = None,
) -> BaselineETA:
    """Earliest realistic arrival date for one shipment.

    ``origin_type`` is ``"branch"`` or ``"dc"``.
    """
    cfg = config or BaselineConfig()
    if origin_type not in cfg.pick_pack_days or origin_type not in cfg.cutoff:
        raise ValueError(f"Unknown origin_type {origin_type!r}; expected one of {sorted(cfg.pick_pack_days)}")

    dispatch = dispatch_date(order_time, origin_type, origin_country, cfg)
    pick_pack = cfg.pick_pack_days[origin_type]
    driving_days = max(1, math.ceil(drive.duration_min / cfg.max_driving_minutes_per_day))
    border = border_delay_days(origin_country, dest_country, cfg)

    # The first driving day is the delivery day itself; only extra driving days add waiting time.
    business_days = pick_pack + (driving_days - 1) + border
    arrival = add_business_days(dispatch, business_days, dest_country)
    # Same-day delivery still requires the destination to be open that day.
    arrival = next_business_day(arrival, dest_country)

    notes = []
    if dispatch != order_time.date():
        notes.append("dispatch moved to next business day (after cut-off, weekend or holiday)")
    if driving_days > 1:
        notes.append(f"long haul: {driving_days} driving days")
    if border:
        notes.append(f"border {origin_country}->{dest_country}: +{border} business day(s)")

    return BaselineETA(
        dispatch_date=dispatch,
        arrival_date=arrival,
        business_days_after_dispatch=business_days,
        driving_days=driving_days,
        pick_pack_days=pick_pack,
        border_days=border,
        notes=tuple(notes),
    )
