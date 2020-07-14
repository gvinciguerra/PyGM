<p align="center">
  <img src="https://gvinciguerra.github.io/PGM-index/images/pygm.svg" alt="pygm" style="width: 565px" />
</p>

<p align="center">PyGM is a Python library that enables fast query operations on sorted lists of numbers (like integers and floats) with a tiny memory overhead. Internally, it features the <a href="https://github.com/gvinciguerra/PGM-index">PGM-index</a>, a state-of-the-art learned data structure that robustly scales to billions of elements in just a few tens of megabytes.</p>

<p align="center">
    <a href="https://github.com/gvinciguerra/PyGM/actions?query=workflow%3Atests"><img src="https://github.com/gvinciguerra/PyGM/workflows/build/badge.svg?branch=master" alt="Build status" /></a>
    <a href="https://codecov.io/gh/gvinciguerra/PyGM"><img src="https://codecov.io/gh/gvinciguerra/PyGM/branch/master/graph/badge.svg?token=G20KV3DLAN" alt="Code coverage"/></a>
    <a href="https://pypi.org/project/pygm/"><img src="https://img.shields.io/pypi/v/pygm" alt="PyPI"/></a>
    <a href="https://github.com/gvinciguerra/PyGM/blob/master/LICENSE"><img src="https://img.shields.io/github/license/gvinciguerra/PyGM" alt="License" /></a>
    <a href="https://github.com/gvinciguerra/PyGM/stargazers"><img src="https://img.shields.io/github/stars/gvinciguerra/PyGM" alt="GitHub stars" /></a>
    <a href="https://github.com/gvinciguerra/PyGM/network/members"><img alt="GitHub forks" src="https://img.shields.io/github/forks/gvinciguerra/PyGM" /></a>
</p>

## Quick start

Install with pip:

```bash
pip install pygm
```

PyGM supports both standard and other useful list and set operations:

```python
>>> from pygm import SortedList, SortedSet
>>> sl = SortedList([0, 1, 34, 144, 1, 55, 233, 2, 3, 21, 89, 5, 8, 13])
>>> sl
SortedList([0, 1, 1, ..., 144, 233])
>>> sl.find_gt(9)                                   # smallest element > 9
13
>>> sl.count(1)                                     # frequency of 1
2
>>> 42 in sl                                        # membership test
False
>>> list(sl.range(0, 21, inclusive=(False, True)))  # elements 0 < x <= 21
[1, 1, 2, 3, 5, 8, 13, 21]
>>> sl[2:10:3]                                      # slicing syntax support
SortedList([1, 5, 21])
>>> (sl + [-3, -2, -1]).rank(0)                     # number of elements <= 0
4
>>> ss = SortedSet([1, 2, 3, 4]) ^ {3, 4, 5}        # set symmetric difference
>>> ss.find_lt(5)
2
```

The full documentation is available [online](https://pgm.di.unipi.it/docs/python-reference/) and in the Python interpreter via the `help()` built-in function.

## Installation

PyGM is compatible with Python 3.3+. The easiest way to install it is through PyPI:

```bash
pip install pygm
```

Otherwise, you can clone the repo, build it from source and install it as follows:

```bash
if [[ "$(uname)" == "Darwin" ]]; then brew install libomp; fi
git clone https://github.com/gvinciguerra/PyGM.git
cd PyGM
git submodule update --init --recursive
pip install .
```

Remember to leave the source directory `PyGM/` and its parent before running Python.  

## Performance

Here are some plots that compare the performance of PyGM with two popular libraries, [sortedcontainers](https://github.com/grantjenks/python-sortedcontainers) and [blist](http://github.com/DanielStutzbach/blist), on synthetic data.

<p align="center">
  <img src="https://gvinciguerra.github.io/PGM-index/images/pygm-lists-time.svg" alt="Query performance of Python packages implementing sorted lists" style="width: 700px" />
</p>

All the graphs are log-log and show, for increasing data sizes, the average time it takes to perform each operation (lower is better). In particular, the `__init__` plot shows the construction time, `__contains__` measures membership queries, and `__getitem__` shows the cost of accessing an element given its position.

The interesting operations on sorted lists are: (i) `index`, which returns the position of the first occurrence of a given element; (ii) `count`, which returns the number of occurrences of a given element; (iii) `bisect_left`, which returns the insertion point for a given value in the list to maintain the sorted order (and is used to implement `find_[ge|gt|le|lt]`).

You can run and plot the experiments on your computer and your data with the notebook in [tests/benchmark.ipynb](https://github.com/gvinciguerra/PyGM/blob/master/tests/benchmark.ipynb).

## License

This project is licensed under the terms of the Apache License 2.0.

If you use the library in an academic setting, please cite the following paper:

> Paolo Ferragina and Giorgio Vinciguerra. The PGM-index: a fully-dynamic compressed learned index with provable worst-case bounds. PVLDB, 13(8): 1162-1175, 2020.

```tex
@article{Ferragina:2020pgm,
  Author = {Paolo Ferragina and Giorgio Vinciguerra},
  Title = {The {PGM-index}: a fully-dynamic compressed learned index with provable worst-case bounds},
  Year = {2020},
  Volume = {13},
  Number = {8},
  Pages = {1162--1175},
  Doi = {10.14778/3389133.3389135},
  Url = {https://pgm.di.unipi.it},
  Issn = {2150-8097},
  Journal = {{PVLDB}}}
```
