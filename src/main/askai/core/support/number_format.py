"""Compact decimal counts for display, without changing underlying values."""

from decimal import Decimal


def compact_count(value: int) -> str:
    suffixes = ("", "K", "M", "G", "T", "P", "E", "Z", "Y")
    scaled = Decimal(value)
    for suffix in suffixes:
        rounded = round(scaled, 1)
        if abs(rounded) < 1000 or suffix == suffixes[-1]:
            return f"{rounded:.1f}".rstrip("0").rstrip(".") + suffix
        scaled /= 1000
