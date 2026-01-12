"""Tests for prediction parsing in the infinite game."""
import pytest

from logic.infinite_game import InvalidPredictionError, Prediction


def test_prediction_exact_match():
    """Verify that 'higher' and 'lower' map correctly."""
    assert Prediction.input_from_player("higher") == Prediction.HIGHER
    assert Prediction.input_from_player("lower") == Prediction.LOWER

def test_prediction_aliases():
    """Verify that shorthand aliases like 'h' and 'l' work."""
    assert Prediction.input_from_player("h") == Prediction.HIGHER
    assert Prediction.input_from_player("L") == Prediction.LOWER


@pytest.mark.parametrize(
    "typo, expected",
    [
        ("highe", Prediction.HIGHER),  # Missing last letter
        ("lowr", Prediction.LOWER),  # Missing middle letter
        ("HigheR", Prediction.HIGHER),  # Mixed case with typo
    ],
)
def test_prediction_fuzzy_matching(typo, expected):
    """Check that the Levenshtein distance handles minor typos."""
    assert Prediction.input_from_player(typo) == expected


def test_prediction_invalid_input():
    """Check that completely wrong words still raise an error."""
    with pytest.raises(InvalidPredictionError):
        Prediction.input_from_player("Hawkeye is my dream job!")


def test_prediction_equal_rejected():
    """Equal should be rejected in the infinite game."""
    with pytest.raises(InvalidPredictionError):
        Prediction.input_from_player("equal")
