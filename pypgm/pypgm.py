from . import _pypgm
import collections.abc


class SortedList:
    @staticmethod
    def _fromtypecode(arg, typecode):
        if typecode in 'BHI':
            return _pypgm.PGMIndexUInt32(arg)
        elif typecode in 'LQN':
            return _pypgm.PGMIndexUInt64(arg)
        elif typecode in 'bhi':
            return _pypgm.PGMIndexInt32(arg)
        elif typecode in 'lqn':
            return _pypgm.PGMIndexInt64(arg)
        elif typecode in 'ef':
            return _pypgm.PGMIndexFloat(arg)
        elif typecode in 'd':
            return _pypgm.PGMIndexDouble(arg)
        else:
            raise TypeError('Unsupported typecode')

    def __init__(self, arg, typecode=None):
        if arg is None or (hasattr(arg, '__len__') and len(arg) == 0):
            self._typecode = 'b'
            self._impl = _pypgm.PGMIndexInt32()
            return

        if isinstance(arg, (_pypgm.PGMIndexUInt32, _pypgm.PGMIndexUInt64,
                            _pypgm.PGMIndexInt32, _pypgm.PGMIndexInt64,
                            _pypgm.PGMIndexFloat, _pypgm.PGMIndexDouble)):
            self._typecode = typecode
            self._impl = arg
            return

        # Init from an object implementing the buffer protocol
        try:
            v = memoryview(arg)
            self._typecode = typecode or v.format
            self._impl = SortedList._fromtypecode(v, self._typecode)
            return
        except TypeError:
            pass

        # Init from a Python collection
        if isinstance(arg, (list, tuple, set, dict)) and len(arg) > 0:
            if typecode:
                self._typecode = typecode
                self._impl = SortedList._fromtypecode(arg, self._typecode)
                return

            anyfloat = any(isinstance(x, float) for x in arg)
            self._typecode = 'd' if anyfloat else 'q'
            self._impl = SortedList._fromtypecode(arg, self._typecode)
            return

        # Init from an iterator
        if isinstance(arg, collections.abc.Iterable):
            self._typecode = typecode or 'q'
            self._impl = SortedList._fromtypecode(iter(arg), self._typecode)
            return

        raise TypeError('Unsupported argument type')

    def __len__(self):
        """Return the number of elements in the sorted list.

        ``self.__len__()`` <==> ``len(self)``

        Returns:
            int: size of the sorted list
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

    def __iter__(self):
        return self._impl.__iter__()

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
            value of the rightmost element ``< x``
        """
        return self._impl.find_lt(x)

    def find_le(self, x):
        """Find the rightmost element less than or equal to ``x``

        Args:
            x: value to compare the elements to

        Returns:
            value of the rightmost element ``<= x``
        """
        return self._impl.find_le(x)

    def find_gt(self, x):
        """Find the leftmost element greater than ``x``.

        Args:
            x: value to compare the elements to

        Returns:
            value of the leftmost element ``> x``
        """
        return self._impl.find_gt(x)

    def find_ge(self, x):
        """Find the leftmost element greater than or equal to ``x``.

        Args:
            x: value to compare the elements to

        Returns:
            value of the leftmost element ``>= x``
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

    def __add__(self, other):
        """Return a new ``SortedList`` by merging the elements of ``self``
        with ``other``.

        ``self.__add__(other)`` <==> ``self + other``

        Args:
            other: a sequence of values

        Returns:
            SortedList: new list with the merged elements
        """
        return SortedList(self._impl.__add__(other), self._typecode)

    def __sub__(self, other):
        """Return a new ``SortedList`` by removing from ``self`` the elements
        found in ``other``.

        Equivalent elements are treated individually, that is, if some element
        is found m times in ``self`` and n times in ``other``, it will appear
        max(m-n, 0) times in the result.

        ``self.__sub__(other)`` <==> ``self - other``

        Args:
            other: a sequence of values

        Returns:
            SortedList: new list with the elements in the difference
        """
        return SortedList(self._impl.__sub__(other), self._typecode)

    def drop_duplicates(self):
        """Return ``self`` with duplicate elements removed.

        Returns:
            SortedList: new list without duplicates
        """
        return SortedList(self._impl.drop_duplicates(), self._typecode)

    def stats(self):
        """Return a dict containing statistics about self.

        The keys are:

        * ``'data size'``` size of the elements in bytes
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

    def __repr__(self):
        """Return a string representation of self.

        ``self.__repr__()`` <==> ``repr(self)``

        Returns:
            str: repr(self)
        """
        d = self._impl.stats()
        data, index = d['data size'], d['index size']
        name = self.__class__.__name__
        indent = ' ' * (len(name) + 1)
        preview = ''
        if len(self) < 6:
            preview += repr(list(self._impl))
        else:
            fmt_args = (self[0], self[1], self[2], self[-2], self[-1])
            if self._typecode in 'fd':
                preview += '[%g, %g, %g, ..., %g, %g]' % fmt_args
            else:
                preview += '[%d, %d, %d, ..., %d, %d]' % fmt_args
        return '%s(%s,\n%stypecode=%s, bytes=(data=%d,index=%d,total=%d))' % (
            name, preview, indent, self._typecode, data, index, data + index)
