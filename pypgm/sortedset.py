import collections.abc

from .sortedcontainer import SortedContainer


class SortedSet(SortedContainer):
    def __init__(self, arg=None, typecode=None):
        SortedContainer._initwitharg(self, arg, typecode, True)

    def __getitem__(self, i):
        """Return the element at position ``i``.

        ``self.__getitem__(i)`` <==> ``self[i]``

        Args:
            i (int or slice): index of the element

        Returns:
            element at position ``i``
        """
        if isinstance(i, slice):
            return SortedSet(self._impl.__getitem__(i), self._typecode)
        return self._impl.__getitem__(i)

    def union(self, other):
        """Return a new ``SortedSet`` with the elements in one or both ``self``
        and ``other``.

        Values in ``other`` do not need to be in sorted order.

        Args:
            other: a sequence of values

        Returns:
            SortedSet: new set with the elements in the union
        """
        o = SortedContainer._trygetimpl(other)
        return SortedSet(self._impl.union(o), self._typecode)

    def difference(self, other):
        """Return a ``SortedSet` with the elements of ``self`` not found in
        ``other``.

        Values in ``other`` do not need to be in sorted order.

        Args:
            other: a sequence of values

        Returns:
            SortedSet: new set with the elements in the difference
        """
        o = SortedContainer._trygetimpl(other)
        return SortedSet(self._impl.difference(o), self._typecode)

    def symmetric_difference(self, other):
        """Return a ``SortedSet` with the elements found in either ``self`` or
        ``other`` but not in both of them.

        Values in ``other`` do not need to be in sorted order.

        Args:
            other: a sequence of values

        Returns:
            SortedSet: new set with the elements in the symmetric difference
        """
        o = SortedContainer._trygetimpl(other)
        return SortedSet(self._impl.symmetric_difference(o), self._typecode)

    def intersection(self, other):
        """Return a ``SortedSet`` with the elements found in both ``self`` and
        ``other``.

        Args:
            other: a sequence of values

        Returns:
            SortedSet: new set with the elements in the intersection
        """
        o = SortedContainer._trygetimpl(other)
        return SortedSet(self._impl.intersection(o), self._typecode)
