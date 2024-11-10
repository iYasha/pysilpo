import pytest

from pysilpo.utils import Cursor


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
