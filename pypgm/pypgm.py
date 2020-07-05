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
        """Return the number of values."""
        return self._impl.__len__()

    def __contains__(self, x):
        """Check whether self contains the given value or not.

        Args:
            x ([type]): [description]

        Returns:
            [type]: [description]
        """

        return self._impl.__contains__(x)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return SortedList(self._impl.__getitem__(i), self._typecode)
        return self._impl.__getitem__(i)

    def __iter__(self):
        return self._impl.__iter__()

    def bisect_left(self, x):
        """Locate the insertion point for `x` to maintain sorted order.

        If `x` is already present, the insertion point will be before (to the left of) 
        any existing entries.

        Similar to the `bisect` module in the standard library.

        Args:
            x ([type]): [description]

        Returns:
            [type]: [description]
        """
        return self._impl.bisect_left(x)

    def bisect_right(self, x):
        """Locate the insertion point for `x` to maintain sorted order.

        If `x` is already present, the insertion point will be after (to the right of) 
        any existing entries.

        Similar to the `bisect` module in the standard library.

        Args:
            x ([type]): [description]

        Returns:
            [type]: [description]
        """
        return self._impl.bisect_right(x)

    def find_lt(self, x):
        """Find the rightmost value less than `x`.

        Args:
            x: value to compare the elements to
        """
        return self._impl.find_lt(x)

    def find_le(self, x):
        """Find the rightmost value less than or equal to `x`.

        Args:
            x: value to compare the elements to
        """
        return self._impl.find_le(x)

    def find_gt(self, x):
        """Find the leftmost value greater than `x`.

        Args:
            x: value to compare the elements to
        """
        return self._impl.find_gt(x)

    def find_ge(self, x):
        """Find the leftmost value greater than or equal to `x`.

        Args:
            x: value to compare the elements to
        """
        return self._impl.find_ge(x)

    def rank(self, x):
        """Number of values less than or equal to `x`.

        Args:
            x ([type]): [description]
        """
        return self._impl.rank(x)

    def count(self, x):
        """Number of values equal to `x`.

        Args:
            x ([type]): [description]
        """
        return self._impl.count(x)

    def range(self, a, b, inclusive=(True, True), reverse=False):
        """[summary]

        Args:
            a ([type]): [description]
            b ([type]): [description]
            inclusive (tuple, optional): [description]. Defaults to (True, True).
            reverse (bool, optional): [description]. Defaults to False.
        """
        return self._impl.range(a, b, inclusive, reverse)

    def index(self, x, start=None, stop=None):
        """Return the first index of `x`.

        Args:
            x ([type]): [description]
            start ([type], optional): [description]. Defaults to None.
            stop ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]

        Raises:
            ValueError: If `x` is not present.
        """
        return self._impl.index(x, start, stop)

    def __add__(self, other):
        """Return a new SortedList by merging the content of self with the given object.

        Args:
            other ([type]): [description]
        """
        return SortedList(self._impl.__add__(other), self._typecode)

    def __sub__(self, other):
        """Return a new SortedList by removing from self the values found in the given object.

        Args:
            other ([type]): [description]
        """
        return SortedList(self._impl.__sub__(other), self._typecode)

    def drop_duplicates(self):
        """Return self with duplicate values removed.

        Returns:
            [type]: [description]
        """
        return SortedList(self._impl.drop_duplicates(), self._typecode)

    def stats(self):
        """Return a dict containing stats about self, such as the occupied space in bytes.

        Returns:
            [type]: [description]
        """
        d = self._impl.stats()
        d['typecode'] = self._typecode
        return d
