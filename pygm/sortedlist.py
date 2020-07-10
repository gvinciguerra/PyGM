import collections.abc
from operator import eq, ge, gt, le, lt, ne
from textwrap import dedent

from .sortedcontainer import SortedContainer


class SortedList(SortedContainer):
    """A sorted list with efficient query performance and memory usage.

    The list is initialised with the content of the provided iterable ``arg``.

    The ``typecode`` argument is a single character that restricts the
    type of the stored elements. Type codes are defined in the 
    `array <https://docs.python.org/3/library/array.html>`_ module of the
    standard library.  If no type code is specified, the type is inferred
    from the contents of ``arg``.

    The ``epsilon`` argument allows to trade off memory usage with query
    performance. The default value is adequate in most cases.

    Methods for adding and removing elements:

    * :func:`SortedList.__add__`
    * :func:`SortedList.__sub__`
    * :func:`SortedList.drop_duplicates`

    Methods for accessing and querying elements:

    * :func:`SortedList.__getitem__`
    * :func:`SortedList.__contains__`
    * :func:`SortedList.bisect_left`
    * :func:`SortedList.bisect_right`
    * :func:`SortedList.count`
    * :func:`SortedList.find_ge`
    * :func:`SortedList.find_gt`
    * :func:`SortedList.find_le`
    * :func:`SortedList.find_lt`
    * :func:`SortedList.index`
    * :func:`SortedList.rank`

    Methods for iterating elements:

    * :func:`SortedList.range`
    * :func:`SortedList.__iter__`
    * :func:`SortedList.__reversed__`

    Methods for lexicographical comparisons:

    * :func:`SortedList.__eq__`
    * :func:`SortedList.__ne__`
    * :func:`SortedList.__ge__`
    * :func:`SortedList.__gt__`
    * :func:`SortedList.__le__`
    * :func:`SortedList.__lt__`

    Other methods:

    * :func:`SortedList.copy`
    * :func:`SortedList.stats`
    * :func:`SortedList.__repr__`

    Args:
        arg (iterable, optional): initial elements. Defaults to None.
        typecode (char, optional): type of the stored elements. Defaults
            to None.
        epsilon (int, optional): space-time trade-off parameter. Defaults
            to 64.

    Example:
        >>> from pygm import SortedList
        >>> sl = SortedList([0, 1, 34, 144, 1, 55, 233, 2, 3, 21, 89, 5, 8, 13])
        >>> sl
        SortedList([0, 1, 1, ..., 144, 233])
        >>> sl.find_gt(9)                                   # smallest element > 9
        13
        >>> sl.count(1)                                     # number of elements == 1
        2
        >>> 42 in sl                                        # membership test
        False
        >>> list(sl.range(0, 21, inclusive=(False, True)))  # elements 0 < x <= 21
        [1, 1, 2, 3, 5, 8, 13, 21]
        >>> sl[2:10:3]                                      # slicing syntax support
        SortedList([1, 5, 21])
        >>> (sl + [-3, -2, -1]).rank(0)                     # number of elements <= 0
        4
    """

    def __init__(self, arg=None, typecode=None, epsilon=64):
        SortedContainer._initwitharg(self, arg, typecode, epsilon, False)

    def __getitem__(self, i):
        """Return the element at position ``i``.

        ``self.__getitem__(i)`` <==> ``self[i]``

        Args:
            i (int or slice): index of the element

        Returns:
            element at position ``i``
        """
        if isinstance(i, slice):
            return SortedList(self._impl.__getitem__(i), self._typecode)
        return self._impl.__getitem__(i)

    def __add__(self, other):
        """Return a new ``SortedList`` by merging the elements of ``self``
        with ``other``.

        ``self.__add__(other)`` <==> ``self + other``

        Values in ``other`` do not need to be in sorted order.

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedList: new list with the merged elements
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedList(self._impl.merge(*args), self._typecode)

    def __sub__(self, other):
        """Return a new ``SortedList`` by removing from ``self`` the elements
        found in ``other``.

        Equivalent elements are treated individually, that is, if some element
        is found m times in ``self`` and n times in ``other``, it will appear
        max(m-n, 0) times in the result.

        ``self.__sub__(other)`` <==> ``self - other``

        Values in ``other`` do not need to be in sorted order.

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedList: new list with the elements in the difference
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedList(self._impl.difference(*args), self._typecode)

    def drop_duplicates(self):
        """Return ``self`` with duplicate elements removed.

        Returns:
            SortedList: new list without duplicates
        """
        return SortedList(self._impl.drop_duplicates(), self._typecode)

    def copy(self):
        """Return a copy of ``self``.

        Returns:
            SortedList: new list with the same elements of ``self``
        """
        return SortedList(self._impl, self._typecode)

    __copy__ = copy

    def _make_cmp(op, symbol, doc):
        # credits: https://github.com/grantjenks/python-sortedcontainers/
        def comparer(self, other):
            if not isinstance(other, collections.abc.Sequence):
                return NotImplemented

            len_self = len(self)
            len_other = len(other)

            if len_self != len_other:
                if op is eq:
                    return False
                if op is ne:
                    return True

            for x, y in zip(self, other):
                if x != y:
                    return op(x, y)

            return op(len_self, len_other)

        comparer.__name__ = '__{0}__'.format(op)
        doc_str = """Return ``True`` if and only if ``self`` is {0} ``other``.

        ``self.__{1}__(other)`` <==> ``self {2} other``

        Comparisons use the `lexicographical order <https://docs.python.org/3/tutorial/datastructures.html#comparing-sequences-and-other-types>`_.

        Args:
            other (iterable): a sequence of values

        Returns:
            ``True`` if sorted list is {0} `other`
        """
        comparer.__doc__ = dedent(doc_str.format(doc, op.__name__, symbol))
        return comparer

    __eq__ = _make_cmp(eq, '==', 'equal to')
    __ne__ = _make_cmp(ne, '!=', 'not equal to')
    __lt__ = _make_cmp(lt, '<', 'less than')
    __gt__ = _make_cmp(gt, '>', 'greater than')
    __le__ = _make_cmp(le, '<=', 'less than or equal to')
    __ge__ = _make_cmp(ge, '>=', 'greater than or equal to')
    _make_cmp = staticmethod(_make_cmp)
