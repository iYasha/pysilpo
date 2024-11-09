import math
from typing import Generic, Protocol, TypeVar, Union

T = TypeVar("T")


class Empty:
    pass


class Generator(Protocol):
    def __call__(self, _offset: int) -> tuple[list[T], int]:
        ...


class Cursor(Generic[T]):
    def __init__(self, generator: Generator, page_size: int):
        self.generator = generator
        self.total_count = None
        self.rounded_count = None
        self.fetched_count = 0
        self.pages = {}
        self.page_size = page_size
        self.curr = 0

    def fetch_new_page(self, index: int) -> list[T]:
        page_index = math.floor(index // self.page_size)
        if self.rounded_count is not None and index > self.rounded_count:
            raise IndexError
        page_content, total_count = self.generator(_offset=page_index * self.page_size)
        self.total_count = total_count

        # We need rounded count to know how many items we have in total, because we can't rely on total_count
        self.rounded_count = math.ceil(total_count / self.page_size) * self.page_size
        if not page_content:
            raise IndexError
        if page_index not in self.pages:
            self.fetched_count += len(page_content)
        self.pages[page_index] = page_content
        return self.pages[page_index]

    def get_page(self, index: int) -> list[T]:
        try:
            return self.pages[math.floor(index // self.page_size)]
        except KeyError:
            return self.fetch_new_page(index)

    def get(self, index: int) -> Union[T, Empty]:
        try:
            return self.get_page(index)[index % self.page_size]
        except IndexError:
            return Empty

    def first(self) -> T:
        return self[0]

    def __getitem__(self, index: Union[int, slice]) -> Union[list[T], T]:
        if isinstance(index, slice):
            return [
                self.get(i)
                for i in range(index.start or 0, index.stop or len(self), index.step or 1)
                if self.get(i) is not Empty
            ]
        if index < 0:
            index = len(self) + index
        val = self.get(index)
        if val is Empty:
            raise IndexError
        return val

    def __iter__(self):
        return self

    def __next__(self) -> T:
        try:
            val = self[self.curr]
        except IndexError:
            self.curr = 0
            raise StopIteration from None
        self.curr += 1
        return val

    def __len__(self) -> int:
        """
        Some API endpoints might return more items than they return in `total`
        :return: Total count of fetched items if it's more than `total` or `total` otherwise
        """
        if self.total_count is None:
            self.fetch_new_page(0)
        return self.fetched_count if self.fetched_count >= self.total_count else self.total_count

    def __repr__(self):
        return f"<Cursor len={len(self)}> at {hex(id(self))}"
