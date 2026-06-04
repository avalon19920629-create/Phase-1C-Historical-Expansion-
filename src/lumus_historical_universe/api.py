from __future__ import annotations

from .reconstruct import MembershipResult, reconstruct_from_anchor


class InsufficientCoverageError(RuntimeError):
    """Raised when a date cannot be reconstructed without current-universe bias."""


def get_sp500_members(date: str, *, allow_insufficient: bool = False) -> MembershipResult:
    result = reconstruct_from_anchor(date)
    if result.quality_flag in {"unavailable", "insufficient"} and not allow_insufficient:
        raise InsufficientCoverageError(result.warning)
    return result
