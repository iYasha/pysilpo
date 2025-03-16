from datetime import datetime, timezone

import pytest

from pysilpo.utils.cursor import Cursor
from pysilpo.utils.utils import subtract_months


class DummyGenerator:
    def __init__(self):
        self.values = range(23)
        self.limit = 5
        self.rounded_count = 25

    def __call__(self, _offset: int):
        return list(self.values[_offset : _offset + self.limit]), len(self.values)


@pytest.fixture
def cursor():
    generator = DummyGenerator()
    return Cursor(generator=generator, page_size=generator.limit)


class TestCursor:
    def test_create_cursor(self):
        generator = DummyGenerator()
        cursor = Cursor(generator=generator, page_size=generator.limit)
        assert cursor.pages == {}
        assert cursor.page_size == generator.limit
        assert cursor.curr == 0
        assert cursor.total_count is None
        assert cursor.rounded_count is None
        assert cursor.fetched_count == 0

    def test_len(self, cursor):
        total_count = len(cursor.generator.values)
        assert len(cursor) == total_count, "Total count is not equal to len(cursor)"
        assert cursor.total_count == total_count, "Total count is not equal to len(cursor)"
        assert cursor.rounded_count == cursor.generator.rounded_count, "Round count is not equal to len(cursor)"
        assert cursor.curr == 0

        # To know total_count we need to fetch at least one chunk
        assert cursor.fetched_count == cursor.page_size

    def test_iter(self, cursor):
        for i, val in enumerate(cursor):
            assert val == i
        assert cursor.curr == 0

        assert list(cursor) == list(cursor.generator.values)
        assert cursor.curr == 0

    def test_index(self, cursor):
        assert cursor[-1] == list(cursor.generator.values)[-1]
        assert cursor[-5] == list(cursor.generator.values)[-5]

    def test_first(self, cursor):
        total_count = len(cursor.generator.values)
        assert cursor[0] == 0
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count

        # To know total_count we need to fetch at least one chunk
        assert cursor.fetched_count == cursor.page_size

    def test_slice(self, cursor):
        total_count = len(cursor.generator.values)
        assert cursor[1:3] == [1, 2]
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count

        # To know total_count we need to fetch at least one chunk
        assert cursor.fetched_count == cursor.page_size

        assert cursor[1 : cursor.page_size * 2 : 2] == list(range(1, cursor.page_size * 2, 2))
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count

        # To know total_count we need to fetch at least one chunk
        assert cursor.fetched_count == cursor.page_size * 2

        assert cursor[5:1:-1] == [5, 4, 3, 2]

    def test_slice_only_start(self, cursor):
        total_count = len(cursor.generator.values)
        assert cursor[1:] == list(range(1, total_count))
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count
        assert cursor.fetched_count == total_count

    def test_slice_only_stop(self, cursor):
        total_count = len(cursor.generator.values)
        assert cursor[:3] == list(range(3))
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count
        assert cursor.fetched_count == cursor.page_size

    def test_slice_only_step(self, cursor):
        total_count = len(cursor.generator.values)
        assert cursor[::2] == list(range(0, total_count, 2))
        assert cursor.curr == 0
        assert cursor.total_count == total_count
        assert cursor.rounded_count == cursor.generator.rounded_count
        assert cursor.fetched_count == total_count

    def test_index_error(self, cursor):
        with pytest.raises(IndexError):
            cursor[1000]

        assert cursor[1000:2000] == []

        assert cursor[1000:2000:2] == []

        assert cursor[1000:] == []

        assert cursor[:1000] == list(cursor.generator.values)

        assert cursor[1000::2] == []


class TestSubtractMonths:
    """Test suite for the subtract_months function."""

    def test_basic_subtraction(self):
        """Test basic month subtraction that doesn't cross year boundary"""
        date = datetime(2025, 3, 15)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 15)

        date = datetime(2025, 5, 10)
        result = subtract_months(date, 2)
        assert result == datetime(2025, 3, 10)

    def test_cross_year_boundary(self):
        """Test subtraction that crosses year boundary"""
        date = datetime(2025, 1, 15)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 12, 15)

        date = datetime(2025, 3, 10)
        result = subtract_months(date, 15)
        assert result == datetime(2023, 12, 10)

    def test_multiple_year_cross(self):
        """Test subtraction that crosses multiple years"""
        date = datetime(2025, 5, 20)
        result = subtract_months(date, 25)
        assert result == datetime(2023, 4, 20)

    def test_end_of_month_handling(self):
        """Test handling of month end dates"""
        # January 31 -> December 31 (same day)
        date = datetime(2025, 1, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 12, 31)

        # March 31 -> February (should adjust to Feb 28/29)
        date = datetime(2025, 3, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 28)

        # Leap year test
        date = datetime(2024, 3, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 2, 29)

    def test_month_length_differences(self):
        """Test transitions between months with different lengths"""
        # May 31 -> April 30
        date = datetime(2025, 5, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 4, 30)

        # May 30 -> April 30 (same day)
        date = datetime(2025, 5, 30)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 4, 30)

        # December 31 -> November 30
        date = datetime(2025, 12, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 11, 30)

    def test_preserves_time_components(self):
        """Test that time components are preserved"""
        date = datetime(2025, 3, 15, 14, 30, 45, 123456)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 15, 14, 30, 45, 123456)

    def test_preserves_timezone(self):
        """Test that timezone information is preserved"""
        date = datetime(2025, 3, 15, 14, 30, 45, tzinfo=timezone.utc)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 15, 14, 30, 45, tzinfo=timezone.utc)

    def test_zero_months(self):
        """Test subtracting zero months returns the same date"""
        date = datetime(2025, 3, 15)
        result = subtract_months(date, 0)
        assert result == date

    def test_negative_months(self):
        """Test that negative months raises a ValueError"""
        date = datetime(2025, 3, 15)
        with pytest.raises(ValueError):
            subtract_months(date, -1)

    def test_large_month_subtraction(self):
        """Test with large number of months"""
        date = datetime(2025, 3, 15)
        result = subtract_months(date, 100)
        assert result == datetime(2016, 11, 15)

    def test_february_edge_cases(self):
        """Test specific February edge cases, especially around leap years"""
        # Non-leap year: March 29, 30, 31 -> February 28
        date = datetime(2025, 3, 29)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 28)

        date = datetime(2025, 3, 30)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 28)

        date = datetime(2025, 3, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2025, 2, 28)

        # Leap year: March 29 -> February 29
        date = datetime(2024, 3, 29)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 2, 29)

        # Leap year: March 30, 31 -> February 29
        date = datetime(2024, 3, 30)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 2, 29)

        date = datetime(2024, 3, 31)
        result = subtract_months(date, 1)
        assert result == datetime(2024, 2, 29)

    @pytest.mark.parametrize(
        "input_date,months,expected",
        [
            # Basic cases
            (datetime(2025, 5, 15), 1, datetime(2025, 4, 15)),
            (datetime(2025, 5, 15), 3, datetime(2025, 2, 15)),
            # Year boundary
            (datetime(2025, 2, 15), 3, datetime(2024, 11, 15)),
            # Month length adjustments
            (datetime(2025, 5, 31), 1, datetime(2025, 4, 30)),
            (datetime(2025, 3, 31), 1, datetime(2025, 2, 28)),
            (datetime(2024, 3, 31), 1, datetime(2024, 2, 29)),
        ],
    )
    def test_parameterized_cases(self, input_date, months, expected):
        """Test multiple scenarios with parameterization"""
        assert subtract_months(input_date, months) == expected
