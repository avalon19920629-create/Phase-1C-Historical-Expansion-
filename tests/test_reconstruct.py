import pytest

from lumus_historical_universe.api import InsufficientCoverageError, get_sp500_members
from lumus_historical_universe.reconstruct import reconstruct_from_anchor


def test_get_2018_does_not_silently_return_high_confidence_current_list():
    with pytest.raises(InsufficientCoverageError):
        get_sp500_members("2018-12-31")
    result = get_sp500_members("2018-12-31", allow_insufficient=True)
    assert result.quality_flag == "insufficient"
    assert result.members == []
    assert "current-only universe" in result.warning


def test_reconstruct_with_explicit_anchor_can_return_members():
    result = reconstruct_from_anchor("2018-12-31", anchor_members={"A", "B"})
    assert isinstance(result.members, list)
    assert result.quality_flag != "insufficient"
