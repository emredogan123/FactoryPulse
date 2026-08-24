from app.services.quality_measurement import (
    calculate_is_within_spec,
)


def test_no_limits_returns_none() -> None:
    result = calculate_is_within_spec(
        value=245.0,
        lower_spec_limit=None,
        upper_spec_limit=None,
    )

    assert result is None


def test_value_inside_limits_returns_true() -> None:
    result = calculate_is_within_spec(
        value=245.0,
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
    )

    assert result is True


def test_value_below_lower_limit_returns_false() -> None:
    result = calculate_is_within_spec(
        value=230.0,
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
    )

    assert result is False


def test_value_above_upper_limit_returns_false() -> None:
    result = calculate_is_within_spec(
        value=255.0,
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
    )

    assert result is False


def test_values_on_limits_are_accepted() -> None:
    lower_result = calculate_is_within_spec(
        value=235.0,
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
    )

    upper_result = calculate_is_within_spec(
        value=250.0,
        lower_spec_limit=235.0,
        upper_spec_limit=250.0,
    )

    assert lower_result is True
    assert upper_result is True