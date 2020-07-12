import bisect
import itertools
import random
from array import array

import pytest
from pygm import SortedList, SortedSet


def test_len():
    assert len(SortedSet([1, 2, 3])) == 3
    assert len(SortedSet([3, 1, 4, 3])) == 3
    assert len(SortedSet([1] * 10)) == 1


def test_init():
    assert list(SortedSet()) == []
    assert list(SortedSet([])) == []
    assert list(SortedSet((1, 2, 3, 2))) == [1, 2, 3]
    assert list(SortedSet({1: 'a', 2: 'b', 3: 'c'})) == [1, 2, 3]
    assert list(SortedSet({1, 5, 5, 10})) == [1, 5, 10]
    assert list(SortedSet(range(5, 0, -1))) == [1, 2, 3, 4, 5]
    assert list(SortedSet(array('d', (1, 2, 2, 3)))) == [1., 2., 3.]


def test_compare():
    assert SortedSet({1, 2, 4, 8}) == {1, 2, 4, 8}
    assert SortedSet({1, 2, 4, 8}) <= {1, 2, 4, 8}
    assert SortedSet({1, 2, 4, 8}) >= {1, 2, 4, 8}
    assert SortedSet({1, 2, 4, 8}) <= {1, 2, 3, 4, 8, 16}
    assert SortedSet({1, 2, 4, 8}) >= {2, 8}
    assert SortedSet({1, 2, 4, 8}) != {1, 2, 3, 8}
    assert not SortedSet({1, 2, 4, 8}) == {1, 2, 4}
    assert SortedSet({1, 2, 4, 8}) != {1, 2, 4, 8, 16}
    assert SortedSet({1, 2, 4, 8}) > {2, 8}
    assert SortedSet({1, 2, 4, 8}) < {1, 2, 3, 4, 8, 16}
    assert SortedSet({1, 2, 4, 8}).issubset({1, 2, 4, 8, 16})
    assert SortedSet({1, 2, 4, 8}).issuperset({2, 8})

    random.seed(42)
    ss = SortedSet(random.sample(range(250), 15))
    for k in range(len(ss)):
        for c in itertools.combinations(ss, k):
            assert ss > set(c)

    for op in ['eq', 'ge', 'gt', 'le', 'lt', 'ne']:
        f = getattr(SortedSet({1}), '__%s__' % op)
        assert NotImplemented == f({'a': 1, 'b': 2})


def test_contains():
    assert 5 in SortedSet(range(100))
    assert 50 not in SortedSet(list(range(50)) + list(range(51, 100)))
    assert 500. in SortedSet([1., 1.] * 10 + [500.] * 2 + [1000.] * 5)


def test_getitem():
    assert SortedSet([0, 1, 3, 3, 4, 10])[-1] == 10
    assert SortedSet([0, 1, 3, 3, 4, 10])[3] == 4
    assert SortedSet(range(100))[50] == 50
    assert list(SortedSet([1, 4, 9, 7] * 10)[2:-1]) == [7]
    assert list(SortedSet(range(1, 100))[:5]) == [1, 2, 3, 4, 5]
    assert list(SortedSet(range(1, 10))[1::2]) == [2, 4, 6, 8]


def test_iter():
    assert next(iter(SortedSet([0, 1, 4, 10]))) == 0
    assert {x for x in SortedSet([0, 1, 3, 3, 4, 10])} == {0, 1, 3, 4, 10}
    assert [x for x in SortedSet([-10, -10, 0, 10, 100])] == [-10, 0, 10, 100]


def test_bisect():
    random.seed(42)
    l = sorted(random.sample(range(250), 100))
    sl = SortedSet(l)
    for x in range(-5, 255):
        assert sl.bisect_left(x) == bisect.bisect_left(l, x)
        assert sl.bisect_right(x) == bisect.bisect_right(l, x)


def test_find():
    l = SortedSet([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233])
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
    l = SortedSet([0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233])
    assert l.rank(-5) == 0
    assert l.rank(0) == 1
    assert l.rank(1) == 2
    assert l.rank(4) == 4
    assert l.rank(14) == 7
    assert l.rank(500) == 13


def test_count():
    l = SortedSet(range(100))
    assert l.count(-100) == 0
    assert l.count(1000) == 0
    for x in l:
        assert l.count(x) == 1

    l = SortedSet([1, 2, 4, 8, 16, 32] * 100)
    assert l.count(-100) == 0
    assert l.count(1000) == 0
    for x in range(6):
        assert l.count(2 ** x) == 1


def test_range():
    l = SortedSet(range(1, 100, 4))
    assert list(l.range(25, 50)) == list(range(25, 51, 4))
    assert list(l.range(25, 50, (False, False))) == list(range(25, 50, 4))[1:]
    assert list(l.range(25, 50, (True, False))) == list(range(25, 50, 4))
    assert list(l.range(25, 50, (False, True))) == list(range(25, 51, 4))[1:]
    assert list(l.range(33, 50, (True, True), True)) == [49, 45, 41, 37, 33]


def test_index():
    l = sorted([0, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233])
    sl = SortedSet(l)
    for x in set(l):
        assert sl.index(x) == l.index(x)

    assert sl.index(1) == 1
    assert sl.index(21, 5) == 7
    assert sl.index(21, 5, 10) == 7

    with pytest.raises(ValueError):
        sl.index(18)
        sl.index(233, 10, -20)


def test_union():
    l1 = SortedSet(range(0, 100, 3))
    l2 = SortedSet(range(1, 100, 3))
    l3 = SortedSet(range(2, 100, 3))
    assert list(l1.union(l2).union(l3)) == list(range(100))
    assert list(l1.union([-1, 5])) == sorted(list(range(0, 100, 3)) + [-1, 5])
    assert len(l1.union(SortedList([-1, 3, 0, 3, 3]))) == 35


def test_difference():
    assert list(SortedSet([1, 2, 4, 8, 16]).difference([16, 2])) == [1, 4, 8]
    assert list(SortedSet([2, 4, 8, 16]).difference([8, 8])) == [2, 4, 16]
    assert list(SortedSet(range(7)).difference([5, 8])) == [0, 1, 2, 3, 4, 6]


def test_intersection():
    for x in SortedSet(range(1000)).intersection(range(0, 10, 2)):
        assert x > 10 or x % 2 == 0


def test_symmetric_difference():
    for x in SortedSet(range(100)).symmetric_difference(range(50, 150)):
        assert x < 50 or x > 99


def test_copy():
    assert len(SortedSet().copy()) == 0
    assert list(SortedSet([4, 1, 3, 3, 2]).copy()) == [1, 2, 3, 4]


def test_isdisjoint():
    assert SortedSet({1, 2, 4, 8}).isdisjoint({3, 5, 6, 9})
    assert not SortedSet({1, 2, 4, 8}).isdisjoint({3, 5, 6, 8})
    assert not SortedSet({1, 2, 4, 8}).isdisjoint(SortedSet({1, 2, 4, 8}))
    assert SortedSet().isdisjoint(set())
    assert SortedSet().isdisjoint(SortedSet())
