from .sortedcontainer import SortedContainer


class SortedSet(SortedContainer):
    """A sorted set with efficient query performance and memory usage.

    The set is initialised with the content of the provided iterable ``arg``.

    The ``typecode`` argument is a single character that restricts the
    type of the stored elements. Type codes are defined in the 
    `array <https://docs.python.org/3/library/array.html>`_ module of the
    standard library.  If no type code is specified, the type is inferred
    from the contents of ``arg``.

    The ``epsilon`` argument allows to trade off memory usage with query
    performance. The default value is adequate in most cases.

    Methods for set operations:

    * :func:`SortedSet.difference`
    * :func:`SortedSet.intersection`
    * :func:`SortedSet.union`
    * :func:`SortedSet.symmetric_difference`

    Methods for accessing and querying elements:

    * :func:`SortedSet.__getitem__`
    * :func:`SortedSet.__contains__`
    * :func:`SortedSet.bisect_left`
    * :func:`SortedSet.bisect_right`
    * :func:`SortedSet.count`
    * :func:`SortedSet.find_ge`
    * :func:`SortedSet.find_gt`
    * :func:`SortedSet.find_le`
    * :func:`SortedSet.find_lt`
    * :func:`SortedSet.index`
    * :func:`SortedSet.rank`

    Methods for iterating elements:

    * :func:`SortedSet.range`
    * :func:`SortedSet.__iter__`
    * :func:`SortedSet.__reversed__`

    Other methods:

    * :func:`SortedSet.copy`
    * :func:`SortedSet.stats`
    * :func:`SortedSet.__repr__`

    Args:
        arg (iterable, optional): initial elements. Defaults to None.
        typecode (char, optional): type of the stored elements. Defaults
            to None.
        epsilon (int, optional): space-time trade-off parameter. Defaults
            to 64.
    """

    def __init__(self, arg=None, typecode=None, epsilon=64):
        SortedContainer._initwitharg(self, arg, typecode, epsilon, True)

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

        ``self.union(other)`` <==> ``self | other``

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedSet: new set with the elements in the union
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedSet(self._impl.union(*args), self._typecode)

    __or__ = union

    def difference(self, other):
        """Return a ``SortedSet`` with the elements of ``self`` not found in
        ``other``.

        Values in ``other`` do not need to be in sorted order.

        ``self.difference(other)`` <==> ``self.__sub__(other)`` <==>
        ``self - other``

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedSet: new set with the elements in the difference
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedSet(self._impl.difference(*args), self._typecode)

    __sub__ = difference

    def symmetric_difference(self, other):
        """Return a ``SortedSet` with the elements found in either ``self`` or
        ``other`` but not in both of them.

        Values in ``other`` do not need to be in sorted order.

        ``self.symmetric_difference(other)`` <==> ``self.__xor__(other)`` <==>
        ``self ^ other``

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedSet: new set with the elements in the symmetric difference
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedSet(self._impl.symmetric_difference(*args), self._typecode)

    __xor__ = symmetric_difference

    def intersection(self, other):
        """Return a ``SortedSet`` with the elements found in both ``self`` and
        ``other``.

        Values in ``other`` do not need to be in sorted order.

        ``self.intersection(other)`` <==> ``self.__and__(other)`` <==>
        ``self & other``

        Args:
            other (iterable): a sequence of values

        Returns:
            SortedSet: new set with the elements in the intersection
        """
        args = SortedContainer._impl_or_iter(other)
        return SortedSet(self._impl.intersection(*args), self._typecode)

    __and__ = intersection

    def copy(self):
        """Return a copy of ``self``.

        Returns:
            SortedSet: new set with the same elements of ``self``
        """
        return SortedSet(self._impl, self._typecode)

    __copy__ = copy
