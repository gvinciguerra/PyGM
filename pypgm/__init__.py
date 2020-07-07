__all__ = ['SortedList', 'SortedSet']
__version__ = '0.1'
__author__ = 'Giorgio Vinciguerra'

import os as _os

from .sortedlist import SortedList
from .sortedset import SortedSet

_os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
