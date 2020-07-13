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

    * :func:`SortedSet.difference` (alias for ``set - other``)
    * :func:`SortedSet.intersection` (alias for ``set & other``)
    * :func:`SortedSet.union` (alias for ``set | other``)
    * :func:`SortedSet.symmetric_difference` (alias for ``set ^ other``)

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

    Methods for set comparisons:

    * :func:`SortedSet.__eq__` (set equality)
    * :func:`SortedSet.__ne__` (set inequality)
    * :func:`SortedSet.__ge__` (superset)
    * :func:`SortedSet.__gt__` (proper superset)
    * :func:`SortedSet.__le__` (subset)
    * :func:`SortedSet.__lt__` (proper subset)

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
            return SortedSet(self._impl.slice(i), self._typecode)
        return self._impl[i]

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
        """Return a ``SortedSet`` with the elements found in either ``self`` or
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

    def __eq__(self, other):
        """Return ``True`` if and only if ``self`` is equal to ``other``.

        ``self.__eq__(other)`` <==> ``self == other``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is equal to ``other``
        """
        if isinstance(other, (SortedSet, set)):
            if len(self) != len(other):
                return False
            args = SortedContainer._impl_or_iter(other)
            return self._impl.equal_to(*args)
        return NotImplemented

    def __ne__(self, other):
        """Return ``True`` if and only if ``self`` is not equal to ``other``.

        ``self.__eq__(other)`` <==> ``self != other``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is not equal to ``other``
        """
        if isinstance(other, (SortedSet, set)):
            if len(self) != len(other):
                return True
            args = SortedContainer._impl_or_iter(other)
            return self._impl.not_equal_to(*args)
        return NotImplemented

    def __lt__(self, other):
        """Return ``True`` if and only if ``self`` is a proper subset of ``other``.

        ``self.__lt__(other)`` <==> ``self < other``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is a proper subset of ``other``
        """
        if isinstance(other, (SortedSet, set)):
            args = SortedContainer._impl_or_iter(other)
            return self._impl.subset(*args, True)
        return NotImplemented

    def __gt__(self, other):
        """Return ``True`` if and only if ``self`` is a proper superset of ``other``.

        ``self.__gt__(other)`` <==> ``self > other``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is a proper superset of ``other``
        """
        if isinstance(other, (SortedSet, set)):
            args = SortedContainer._impl_or_iter(other)
            return self._impl.superset(*args, True)
        return NotImplemented

    def __le__(self, other):
        """Return ``True`` if and only if ``self`` is a subset of ``other``.

        ``self.__le__(other)`` <==> ``self <= other`` <==> 
        ``self.issubset(other)``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is a subset of ``other``
        """
        if isinstance(other, (SortedSet, set)):
            args = SortedContainer._impl_or_iter(other)
            return self._impl.subset(*args, False)
        return NotImplemented

    def __ge__(self, other):
        """Return ``True`` if and only if ``self`` is a superset of ``other``.

        ``self.__ge__(other)`` <==> ``self >= other`` <==> 
        ``self.issuperset(other)``

        Comparisons use `set <https://docs.python.org/3/library/stdtypes.html#set>`_
        semantics.

        Args:
            other (SortedSet or set): a sequence of values

        Returns:
            bool: ``True`` if sorted set is a superset of ``other``
        """
        if isinstance(other, (SortedSet, set)):
            args = SortedContainer._impl_or_iter(other)
            return self._impl.superset(*args, False)
        return NotImplemented

    def isdisjoint(self, other):
        """Return ``True`` if and only if the set has no elements in common
        with ``other``.

        Sets are disjoint if and only if their intersection is the empty set.

        Args:
            other (iterable): a sequence of values

        Returns:
            bool: ``True`` if ``self`` is disjoint from ``other``
        """
        return len(self & other) == 0

    issubset = __le__
    issuperset = __ge__
