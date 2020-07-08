import collections.abc

from . import _pypgm


class SortedContainer(collections.abc.Sequence):
    @staticmethod
    def _fromtypecode(arg, typecode, drop_duplicates):
        if typecode in 'BHI':
            return _pypgm.PGMIndexUInt32(arg, drop_duplicates)
        elif typecode in 'LQN':
            return _pypgm.PGMIndexUInt64(arg, drop_duplicates)
        elif typecode in 'bhi':
            return _pypgm.PGMIndexInt32(arg, drop_duplicates)
        elif typecode in 'lqn':
            return _pypgm.PGMIndexInt64(arg, drop_duplicates)
        elif typecode in 'ef':
            return _pypgm.PGMIndexFloat(arg, drop_duplicates)
        elif typecode in 'd':
            return _pypgm.PGMIndexDouble(arg, drop_duplicates)
        else:
            raise TypeError('Unsupported typecode')

    @staticmethod
    def _trygetimpl(o):
        return o._impl if isinstance(o, SortedContainer) else o

    @staticmethod
    def _initwitharg(self, arg, typecode, drop_duplicates):
        if arg is None or (hasattr(arg, '__len__') and len(arg) == 0):
            self._typecode = 'b'
            self._impl = _pypgm.PGMIndexInt32()
            return

        if isinstance(arg, (_pypgm.PGMIndexUInt32, _pypgm.PGMIndexUInt64,
                            _pypgm.PGMIndexInt32, _pypgm.PGMIndexInt64,
                            _pypgm.PGMIndexFloat, _pypgm.PGMIndexDouble)):
            if drop_duplicates and arg.has_duplicates():
                self._typecode = typecode
                self._impl = SortedContainer._fromtypecode(
                    arg, typecode, drop_duplicates)
                return
            self._typecode = typecode
            self._impl = arg
            return

        # Init from an object implementing the buffer protocol
        try:
            v = memoryview(arg)
            self._typecode = typecode or v.format
            self._impl = SortedContainer._fromtypecode(
                v, self._typecode, drop_duplicates)
            return
        except TypeError:
            pass

        # Init from a Python collection
        if isinstance(arg, (list, tuple, set, dict)) and len(arg) > 0:
            if typecode:
                self._typecode = typecode
                self._impl = SortedContainer._fromtypecode(
                    arg, self._typecode, drop_duplicates)
                return

            anyfloat = any(isinstance(x, float) for x in arg)
            self._typecode = 'd' if anyfloat else 'q'
            self._impl = SortedContainer._fromtypecode(
                arg, self._typecode, drop_duplicates)
            return

        # Init from an iterator
        if isinstance(arg, collections.abc.Iterable):
            self._typecode = typecode or 'q'
            self._impl = SortedContainer._fromtypecode(
                iter(arg), self._typecode, drop_duplicates)
            return

        raise TypeError('Unsupported argument type')

    def __len__(self):
        """Return the number of elements in ``self``.

        ``self.__len__()`` <==> ``len(self)``

        Returns:
            int: number of elements
        """
        return self._impl.__len__()

    def __contains__(self, x):
        """Check whether ``self`` contains the given value ``x`` or not.

        ``self.__repr__(x)`` <==> ``x in self``

        Args:
            x: value to search

        Returns:
            bool: ``True`` if an element equal to ``x`` is found, ``False``
                otherwise
        """
        return self._impl.__contains__(x)

    def bisect_left(self, x):
        """Locate the insertion point for ``x`` to maintain sorted order.

        If ``x`` is already present, the insertion point will be before (to
        the left of) any existing entries.

        Similar to the ``bisect`` module in the standard library.

        Args:
            x: value to compare the elements to

        Returns:
            int: insertion index in sorted list
        """
        return self._impl.bisect_left(x)

    def bisect_right(self, x):
        """Locate the insertion point for ``x`` to maintain sorted order.

        If ``x`` is already present, the insertion point will be after (to the
        right of) any existing entries.

        Similar to the ``bisect`` module in the standard library.

        Args:
            x: value to compare the elements to

        Returns:
            int: insertion index in sorted list
        """
        return self._impl.bisect_right(x)

    def find_lt(self, x):
        """Find the rightmost element less than ``x``.

        Args:
            x: value to compare the elements to

        Returns:
            value of the rightmost element ``< x``, or ``None`` if no such
            element is found
        """
        return self._impl.find_lt(x)

    def find_le(self, x):
        """Find the rightmost element less than or equal to ``x``

        Args:
            x: value to compare the elements to

        Returns:
            value of the rightmost element ``<= x``, or ``None`` if no such
            element is found
        """
        return self._impl.find_le(x)

    def find_gt(self, x):
        """Find the leftmost element greater than ``x``.

        Args:
            x: value to compare the elements to

        Returns:
            value of the leftmost element ``> x``, or ``None`` if no such
            element is found
        """
        return self._impl.find_gt(x)

    def find_ge(self, x):
        """Find the leftmost element greater than or equal to ``x``.

        Args:
            x: value to compare the elements to

        Returns:
            value of the leftmost element ``>= x``, or ``None`` if no such
            element is found
        """
        return self._impl.find_ge(x)

    def rank(self, x):
        """Return the number of elements less than or equal to ``x``

        Args:
            x: value to compare the elements to

        Returns:
            int: number of elements ``<= x``
        """
        return self._impl.rank(x)

    def count(self, x):
        """Return the number of elements equal to ``x``.

        Args:
            x: value to count

        Returns:
            int: number of elements ``== x``
        """
        return self._impl.count(x)

    def range(self, a, b, inclusive=(True, True), reverse=False):
        """Return an iterator over elements between ``a`` and ``b``.

        Args:
            a: lower bound value
            b: upper bound value
            inclusive (tuple[bool, bool], optional): a pair of boolean
                indicating whether the bounds are inclusive (``True``) or
                exclusive (``False``). Defaults to ``(True, True)``.
            reverse (bool, optional): if ``True`` return an reverse iterator.
                Defaults to ``False``.

        Returns:
            iterator over the elements between the given bounds
        """
        return self._impl.range(a, b, inclusive, reverse)

    def index(self, x, start=None, stop=None):
        """Return the first index of ``x``.

        Args:
            x: element in the sorted list
            start (int, optional): restrict the search to the elements from
                this position onwards. Defaults to ``None``.
            stop (int, optional): restrict the search to the elements before
                this position. Defaults to ``None``.

        Returns:
            int: first index of ``x``

        Raises:
            ValueError: if ``x`` is not present
        """
        return self._impl.index(x, start, stop)

    def stats(self):
        """Return a dict containing statistics about self.

        The keys are:

        * ``'data size'`` size of the elements in bytes
        * ``'index size'`` size of the index in bytes
        * ``'height'`` number of levels of the index
        * ``'leaf segments'`` number of segments in the last level of the index
        * ``'typecode'`` type of the elements (see the `array` module)

        Returns:
            dict[str, object]: a dictionary with stats about self
        """
        d = self._impl.stats()
        d['typecode'] = self._typecode
        return d

    def __iter__(self):
        return self._impl.__iter__()

    def __reversed__(self):
        return self._impl.__reversed__()

    def __repr__(self):
        """Return a string representation of self.

        ``self.__repr__()`` <==> ``repr(self)``

        Returns:
            str: repr(self)
        """
        preview = ''
        if len(self) < 6:
            preview += repr(list(self._impl))
        else:
            fmt_args = (self[0], self[1], self[2], self[-2], self[-1])
            if self._typecode in 'fd':
                preview += '[%g, %g, %g, ..., %g, %g]' % fmt_args
            else:
                preview += '[%d, %d, %d, ..., %d, %d]' % fmt_args
        return '%s(%s)' % (self.__class__.__name__, preview)
