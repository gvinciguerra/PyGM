import bisect
import random
from array import array

import pytest
from pypgm import SortedList


def test_len():
    assert len(SortedList([1, 2, 3])) == 3
    assert len(SortedList([3, 1, 4, 3])) == 4
    assert len(SortedList([1] * 10)) == 10


def test_init():
    assert SortedList() == []
    assert SortedList([]) == []
    assert SortedList((1, 2, 3, 2)) == [1, 2, 2, 3]
    assert SortedList({1: 'a', 2: 'b', 3: 'c'}) == [1, 2, 3]
    assert SortedList({1, 5, 5, 10}) == [1, 5, 10]
    assert SortedList(range(5, 0, -1)) == [1, 2, 3, 4, 5]
    assert SortedList({1, 5, 5, 10}) == [1, 5, 10]
    assert SortedList(array('d', (1, 2, 2, 3))) == [1., 2., 2., 3.]


def test_contains():
    assert 5 in SortedList(range(100))
    assert 50 not in SortedList(list(range(50)) + list(range(51, 100)))
    assert 500. in SortedList([1., 1.] * 10 + [500.] * 2 + [1000.] * 5)


def test_getitem():
    assert SortedList([3, 1, 4, 3])[2] == 3
    assert SortedList(range(100))[50] == 50
    assert SortedList([1, 4, 9, 7] * 10)[2:5] == [1, 1, 1]
    assert SortedList(range(1, 100))[:5] == [1, 2, 3, 4, 5]
    assert SortedList(range(1, 10))[1::2] == [2, 4, 6, 8]


def test_iter():
    assert next(iter(SortedList([0, 1, 4, 10]))) == 0
    assert {x for x in SortedList([0, 1, 3, 3, 4, 10])} == {0, 1, 3, 4, 10}
    assert [x for x in SortedList([-10, 0, 10, 100])] == [-10, 0, 10, 100]


def test_bisect():
    random.seed(42)
    l = sorted([random.randint(-100, 100) for _ in range(500)])
    sl = SortedList(l)
    for x in range(-105, 105):
        assert sl.bisect_left(x) == bisect.bisect_left(l, x)
        assert sl.bisect_right(x) == bisect.bisect_right(l, x)

    l = sorted([random.randint(-1000, 1000) for _ in range(100)])
    sl = SortedList(l)
    for x in range(-100, 100):
        assert sl.bisect_left(x) == bisect.bisect_left(l, x)
        assert sl.bisect_right(x) == bisect.bisect_right(l, x)


def test_find():
    l = SortedList([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233] * 100)
    assert l.find_lt(5) == 3
    assert l.find_lt(22) == 21
    assert l.find_le(14) == 13
    assert l.find_le(89) == 89
    assert l.find_gt(55) == 89
    assert l.find_gt(54) == 55
    assert l.find_ge(5) == 5
    assert l.find_ge(4) == 5
    assert l.find_lt(0) is None
    assert l.find_le(-10) is None
    assert l.find_gt(233) is None
    assert l.find_ge(500) is None


def test_rank():
    l = SortedList([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233] * 10)
    assert l.rank(-5) == 0
    assert l.rank(0) == 10
    assert l.rank(1) == 30
    assert l.rank(4) == 50
    assert l.rank(500) == len(l)


def test_count():
    l = SortedList(range(100))
    assert l.count(-100) == 0
    assert l.count(1000) == 0
    for x in l:
        assert l.count(x) == 1

    l = SortedList([1, 2, 4, 8, 16, 32] * 100)
    assert l.count(-100) == 0
    assert l.count(1000) == 0
    for x in range(6):
        assert l.count(2 ** x) == 100


def test_range():
    l = SortedList(range(1, 100, 4))
    assert list(l.range(25, 50)) == list(range(25, 51, 4))
    assert list(l.range(25, 50, (False, False))) == list(range(25, 50, 4))[1:]
    assert list(l.range(25, 50, (True, False))) == list(range(25, 50, 4))
    assert list(l.range(25, 50, (False, True))) == list(range(25, 51, 4))[1:]
    assert list(l.range(33, 50, (True, True), True)) == [49, 45, 41, 37, 33]


def test_index():
    l = sorted([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233] * 10)
    sl = SortedList(l)
    for x in set(l):
        assert sl.index(x) == l.index(x)

    assert sl.index(1) == 10
    assert sl.index(1, 10) == 10
    assert sl.index(1, 10, 11) == 10

    with pytest.raises(ValueError):
        sl.index(18)
        sl.index(233, 10, -20)


def test_add():
    assert SortedList([1, 1, 3]) + SortedList([5, 1]) == [1, 1, 1, 3, 5]
    assert SortedList([1, 1, 2, 3]) + [5, 1] == [1, 1, 1, 2, 3, 5]


def test_sub():
    assert SortedList([1, 1, 3]) - SortedList([5, 1]) == [1, 3]
    assert SortedList([1, 1, 2, 3, 8]) - [1, 1, 1] == [2, 3, 8]


def test_drop_duplicates():
    assert SortedList([2, 3, 8]).drop_duplicates() == [2, 3, 8]
    assert SortedList([2, 3, 8] * 10).drop_duplicates() == [2, 3, 8]
