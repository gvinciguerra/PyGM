import collections.abc
from operator import eq, ge, gt, le, lt, ne
from textwrap import dedent

from .sortedcontainer import SortedContainer


class SortedList(SortedContainer):
    def __init__(self, arg=None, typecode=None):
        SortedContainer._initwitharg(self, arg, typecode, False)

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
            other: a sequence of values

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
            other: a sequence of values

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
            other: a sequence

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
