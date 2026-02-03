"""Tests for race_day.py travel cost calculations."""

import warnings
import pytest
from gmr.race_day import calc_travel_cost, normalise_country


class TestNormaliseCountry:
    """Tests for country name normalisation."""

    def test_normalises_uk_variants(self):
        assert normalise_country("uk") == "UK"
        assert normalise_country("UK") == "UK"
        assert normalise_country("england") == "UK"
        assert normalise_country("great britain") == "UK"
        assert normalise_country("britain") == "UK"

    def test_normalises_usa_variants(self):
        assert normalise_country("usa") == "USA"
        assert normalise_country("us") == "USA"
        assert normalise_country("united states") == "USA"
        assert normalise_country("america") == "USA"

    def test_preserves_unknown_countries(self):
        # Unknown countries should be returned as-is (stripped)
        assert normalise_country("Australia") == "Australia"
        assert normalise_country("  Germany  ") == "Germany"


class TestCalcTravelCostDomestic:
    """Tests for domestic (same-country) travel costs."""

    def test_domestic_uk_to_uk(self):
        # Same country = DOMESTIC rate (£25 base)
        cost = calc_travel_cost("UK", "UK", 1948)
        assert cost == 25

    def test_domestic_usa_to_usa(self):
        # USA to USA should be DOMESTIC, not transatlantic!
        cost = calc_travel_cost("USA", "USA", 1948)
        assert cost == 25

    def test_domestic_brazil_to_brazil(self):
        cost = calc_travel_cost("Brazil", "Brazil", 1948)
        assert cost == 25

    def test_domestic_with_era_multiplier(self):
        # Post-1950 gets 1.10x multiplier
        cost = calc_travel_cost("UK", "UK", 1950)
        assert cost == 27  # int(25 * 1.10)


class TestCalcTravelCostTransatlantic:
    """Tests for transatlantic (crossing Atlantic) travel costs."""

    def test_uk_to_usa_is_transatlantic(self):
        # European team to Americas = TRANSATLANTIC (£350 base)
        cost = calc_travel_cost("UK", "USA", 1948)
        assert cost == 350

    def test_usa_to_uk_is_transatlantic(self):
        # Americas team to Europe = TRANSATLANTIC
        cost = calc_travel_cost("USA", "UK", 1948)
        assert cost == 350

    def test_italy_to_brazil_is_transatlantic(self):
        cost = calc_travel_cost("Italy", "Brazil", 1948)
        assert cost == 350

    def test_argentina_to_france_is_transatlantic(self):
        cost = calc_travel_cost("Argentina", "France", 1948)
        assert cost == 350

    def test_transatlantic_with_era_multiplier(self):
        cost = calc_travel_cost("UK", "USA", 1950)
        assert cost == 385  # int(350 * 1.10)


class TestCalcTravelCostIntraAmericas:
    """Tests for travel within the Americas (not domestic, not transatlantic)."""

    def test_usa_to_brazil_is_far_rate(self):
        # Intra-Americas (different countries) = FAR_EUROPE equivalent (£110 base)
        cost = calc_travel_cost("USA", "Brazil", 1948)
        assert cost == 110

    def test_brazil_to_argentina_is_far_rate(self):
        cost = calc_travel_cost("Brazil", "Argentina", 1948)
        assert cost == 110

    def test_argentina_to_usa_is_far_rate(self):
        cost = calc_travel_cost("Argentina", "USA", 1948)
        assert cost == 110


class TestCalcTravelCostEurope:
    """Tests for European travel costs."""

    def test_uk_to_france_is_near_europe(self):
        # Near Europe countries = NEAR_EUROPE rate (£70 base)
        cost = calc_travel_cost("UK", "France", 1948)
        assert cost == 70

    def test_belgium_to_switzerland_is_near_europe(self):
        cost = calc_travel_cost("Belgium", "Switzerland", 1948)
        assert cost == 70

    def test_uk_to_italy_is_far_europe(self):
        # Italy involved = FAR_EUROPE rate (£110 base)
        cost = calc_travel_cost("UK", "Italy", 1948)
        assert cost == 110

    def test_france_to_italy_is_far_europe(self):
        cost = calc_travel_cost("France", "Italy", 1948)
        assert cost == 110


class TestCalcTravelCostUnknownCountries:
    """Tests for unknown country handling and warnings."""

    def test_unknown_country_defaults_to_near_europe(self):
        # Unknown countries should default to NEAR_EUROPE (£70)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cost = calc_travel_cost("UK", "Australia", 1948)
            assert cost == 70
            # Should have emitted a warning
            assert len(w) == 1
            assert "unknown country" in str(w[0].message).lower()
            assert "Australia" in str(w[0].message)

    def test_both_unknown_countries_warns(self):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            cost = calc_travel_cost("Japan", "Australia", 1948)
            assert cost == 70
            assert len(w) == 1
            # Both should be mentioned
            assert "Japan" in str(w[0].message) or "Australia" in str(w[0].message)

    def test_unknown_country_still_gets_era_multiplier(self):
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            cost = calc_travel_cost("UK", "Australia", 1950)
            assert cost == 77  # int(70 * 1.10)


class TestCalcTravelCostNormalisation:
    """Tests that country normalisation works with travel cost calculation."""

    def test_normalises_uk_variants_in_travel(self):
        # Should normalise "england" to "UK" internally
        cost_england = calc_travel_cost("england", "France", 1948)
        cost_uk = calc_travel_cost("UK", "France", 1948)
        assert cost_england == cost_uk == 70

    def test_normalises_usa_variants_in_travel(self):
        # "united states" should be treated as "USA"
        cost_full = calc_travel_cost("united states", "united states", 1948)
        cost_abbrev = calc_travel_cost("USA", "USA", 1948)
        assert cost_full == cost_abbrev == 25  # Domestic rate
