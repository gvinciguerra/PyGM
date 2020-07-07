#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <cassert>
#include <regex>
#include <unordered_map>
#include <vector>

#include "pgm_index.hpp"

namespace py = pybind11;
using namespace pybind11::literals;

template <class InputIt1, class InputIt2, class OutputIt>
OutputIt set_unique_union(InputIt1 first1, InputIt1 last1, InputIt2 first2, InputIt2 last2, OutputIt out) {
    for (; first1 != last1; ++out) {
        if (first2 == last2)
            return std::unique_copy(first1, last1, out);
        if (*first2 < *first1) {
            auto to_skip = *first2++;
            *out = to_skip;
            while (first2 != last2 && *first2 == to_skip)
                ++first2;
        } else {
            auto to_skip = *first1++;
            *out = to_skip;
            while (first2 != last2 && *first2 == to_skip)
                ++first2;
            while (first1 != last1 && *first1 == to_skip)
                ++first1;
        }
    }
    return std::unique_copy(first2, last2, out);
}

template <class InputIt1, class InputIt2, class OutputIt>
OutputIt set_unique_symmetric_difference(InputIt1 first1, InputIt1 last1, InputIt2 first2, InputIt2 last2,
                                         OutputIt out) {
    while (first1 != last1) {
        if (first2 == last2)
            return std::unique_copy(first1, last1, out);

        if (*first1 < *first2) {
            auto to_skip = *first1++;
            *out++ = to_skip;
            while (first1 != last1 && *first1 == to_skip)
                ++first1;
        } else {
            auto to_skip = *first2;
            if (*first2 < *first1) {
                *out++ = to_skip;
            } else {
                while (first1 != last1 && *first1 == to_skip)
                    ++first1;
            }
            while (first2 != last2 && *first2 == to_skip)
                ++first2;
        }
    }
    return std::unique_copy(first2, last2, out);
}

template <typename K> class PGMWrapper {
    K *data;
    size_t n;
    PGMIndex<K> pgm;
    bool duplicates;

    typedef K *(*set_fun)(const K *, const K *, const K *, const K *, K *);

    void build_pgm() {
        if (n < 1ull << 15) {
            pgm = decltype(pgm)(begin(), end());
        } else {
            py::gil_scoped_release release;
            pgm = decltype(pgm)(begin(), end());
        }
    }

    static K implicit_cast(py::handle h) {
        try {
            return h.template cast<K>();
        } catch (const std::exception &e) {
            if constexpr (std::is_floating_point_v<K>)
                return (h.template cast<py::float_>()).template cast<K>();
            return (h.template cast<py::int_>()).template cast<K>();
        }
    }

    template <typename C> static size_t get_size(const C &c) { return c.size(); }

    static size_t get_size(const py::array_t<K> &a) { return a.shape(0); }

  public:
    PGMWrapper() = default;

    PGMWrapper(const PGMWrapper &p, bool drop_duplicates) {
        if (p.duplicates && drop_duplicates) {
            n = p.size();
            data = new K[n];
            auto m = (size_t) std::distance(data, std::unique_copy(p.begin(), p.end(), data));
            if (m < n) {
                auto tmp = data;
                n = m;
                data = new K[m];
                std::copy_n(tmp, m, data);
                delete[] tmp;
            }
            duplicates = false;
            build_pgm();
            return;
        }

        n = p.size();
        pgm = p.pgm;
        duplicates = p.duplicates;
        data = new K[n];
        std::copy_n(p.data, n, data);
    }

    PGMWrapper(py::list l, bool drop_duplicates) {
        n = l.size();
        data = new K[n];

        size_t j;
        auto sorted = true;
        auto it = l.begin();
        if (n > 0)
            data[0] = implicit_cast(*it++);
        for (j = 1; it != l.end(); ++it, ++j) {
            auto x = implicit_cast(*it);
            if (x < data[j - 1])
                sorted = false;
            data[j] = x;
        }

        if (!sorted)
            std::sort(data, data + j);

        if (drop_duplicates) {
            duplicates = false;
            j = std::distance(data, std::unique(data, data + j));
            if (j < n) {
                auto tmp = data;
                n = j;
                data = new K[n];
                std::copy_n(tmp, n, data);
                delete[] tmp;
            }
        } else
            duplicates = true;

        build_pgm();
    }

    PGMWrapper(py::iterator it, bool drop_duplicates) {
        auto sorted = true;
        std::vector<K> v;
        v.reserve(8192);
        for (; it != py::iterator::sentinel(); ++it) {
            auto x = implicit_cast(*it);
            if (x < v.back())
                sorted = false;
            v.push_back(x);
        }

        if (!sorted)
            std::sort(v.begin(), v.end());

        n = v.size();
        data = new K[n];
        if (drop_duplicates) {
            auto j = (size_t) std::distance(data, std::unique_copy(v.begin(), v.end(), data));
            duplicates = false;
            if (j < n) {
                auto tmp = data;
                n = j;
                data = new K[n];
                std::copy_n(tmp, n, data);
                delete[] tmp;
            }
        } else {
            duplicates = true;
            std::copy(v.begin(), v.end(), data);
        }

        build_pgm();
    }

    PGMWrapper(K *data, size_t n, bool duplicates) : data(data), n(n), duplicates(duplicates) { build_pgm(); }

#define FORMAT_TYPE_CASE(c, type)                                                                                      \
    case c: {                                                                                                          \
        auto ptr = (type *) info.ptr;                                                                                  \
        if (n > 0)                                                                                                     \
            data[j++] = K(ptr[0]);                                                                                     \
        for (auto i = 1ull; i < n; ++i) {                                                                              \
            auto x = K(ptr[i]);                                                                                        \
            if (x == data[j - 1]) {                                                                                    \
                if (drop_duplicates)                                                                                   \
                    continue;                                                                                          \
                duplicates = true;                                                                                     \
            }                                                                                                          \
            if (x < data[j - 1])                                                                                       \
                sorted = false;                                                                                        \
            data[j++] = x;                                                                                             \
        }                                                                                                              \
        break;                                                                                                         \
    }

    PGMWrapper(py::buffer b, bool drop_duplicates) {
        py::buffer_info info = b.request();
        if (info.ndim != 1)
            throw py::type_error("Incorrect number of dimensions: " + std::to_string(info.ndim) + "; expected 1");

        n = info.shape[0];
        data = new K[n];
        duplicates = false;
        auto j = 0ull;
        auto sorted = true;

        switch (info.format[0]) {
            FORMAT_TYPE_CASE('c', char);
            FORMAT_TYPE_CASE('b', signed char);
            FORMAT_TYPE_CASE('B', unsigned char);
            FORMAT_TYPE_CASE('h', short);
            FORMAT_TYPE_CASE('H', unsigned short);
            FORMAT_TYPE_CASE('i', int);
            FORMAT_TYPE_CASE('I', unsigned int);
            FORMAT_TYPE_CASE('l', long);
            FORMAT_TYPE_CASE('L', unsigned long);
            FORMAT_TYPE_CASE('q', long long);
            FORMAT_TYPE_CASE('Q', unsigned long long);
            FORMAT_TYPE_CASE('n', ssize_t);
            FORMAT_TYPE_CASE('N', size_t);
            FORMAT_TYPE_CASE('f', float);
            FORMAT_TYPE_CASE('d', double);
        default:
            throw py::type_error("Unsupported buffer format");
        }

        if (j < n) {
            auto tmp = data;
            n = j;
            data = new K[n];
            std::copy_n(tmp, n, data);
            delete[] tmp;
        }

        if (!sorted)
            std::sort(begin(), end());
        build_pgm();
    }

    bool contains(K x) const {
        auto ap = pgm.find_approximate_position(x);
        return std::binary_search(data + ap.lo, data + ap.hi, x);
    }

    K *lower_bound(K x) const {
        auto ap = pgm.find_approximate_position(x);
        return std::lower_bound(data + ap.lo, data + ap.hi, x);
    }

    K *upper_bound(K x) const {
        auto ap = pgm.find_approximate_position(x);
        auto it = std::upper_bound(data + ap.lo, data + ap.hi, x);
        if (!duplicates)
            return it;

        auto step = 1ull;
        while (it + step < end() && *(it + step) == x)
            step *= 2;
        return std::upper_bound(it + (step / 2), std::min(it + step, end()), x);
    }

    // TODO: set_operation taking a py::buffer and a py::iterator
    template <set_fun F>
    PGMWrapper *set_operation(const py::array_t<K> &a, size_t out_size_hint, bool generates_duplicates) const {
        auto r = a.template unchecked<1>();
        auto a_size = r.shape(0);
        auto a_begin = r.data(0);
        auto a_end = r.data(r.shape(0));

        auto tmp_out = new K[out_size_hint];
        K *tmp_out_end;

        if (std::is_sorted(a_begin, a_end))
            tmp_out_end = F(begin(), end(), a_begin, a_end, tmp_out);
        else {
            auto tmp = new K[a_size];
            std::copy(a_begin, a_end, tmp);
            std::sort(tmp, tmp + a_size);
            tmp_out_end = F(begin(), end(), tmp, tmp + a_size, tmp_out);
            delete[] tmp;
        }

        auto out_size = (size_t) std::distance(tmp_out, tmp_out_end);
        if (out_size == out_size_hint)
            return new PGMWrapper<K>(tmp_out, out_size, generates_duplicates);

        auto out = new K[out_size];
        std::copy_n(tmp_out, out_size, out);
        delete[] tmp_out;
        return new PGMWrapper<K>(out, out_size, generates_duplicates);
    }

    template <set_fun F>
    PGMWrapper *set_operation(const PGMWrapper<K> &q, size_t out_size_hint, size_t generates_duplicates) const {
        auto tmp_out = new K[out_size_hint];
        auto tmp_out_end = F(begin(), end(), q.begin(), q.end(), tmp_out);
        auto out_size = (size_t) std::distance(tmp_out, tmp_out_end);

        if (out_size == out_size_hint)
            return new PGMWrapper<K>(tmp_out, out_size, generates_duplicates);

        auto out = new K[out_size];
        std::copy_n(tmp_out, out_size, out);
        delete[] tmp_out;
        return new PGMWrapper<K>(out, out_size, generates_duplicates);
    }

    template <typename Container> PGMWrapper *merge(const Container &c) {
        return set_operation<std::merge>(c, size() + get_size(c), true);
    }

    template <typename Container> PGMWrapper *set_difference(const Container &c) {
        return set_operation<std::set_difference>(c, size(), false);
    }

    template <typename Container> PGMWrapper *set_symmetric_difference(const Container &c) {
        return set_operation<set_unique_symmetric_difference>(c, size() + get_size(c), false);
    }

    template <typename Container> PGMWrapper *set_union(const Container &c) {
        return set_operation<set_unique_union>(c, size() + get_size(c), false);
    }

    template <typename Container> PGMWrapper *set_intersection(const Container &c) {
        assert(!has_duplicates()); // otherwise std::set_intersection may output duplicates
        return set_operation<std::set_intersection>(c, std::min(size(), get_size(c)), false);
    }

    std::unordered_map<std::string, size_t> stats() {
        std::unordered_map<std::string, size_t> stats;
        stats["leaf segments"] = pgm.segments_count();
        stats["data size"] = sizeof(K) * n + sizeof(*this);
        stats["index size"] = pgm.size_in_bytes();
        stats["height"] = pgm.height();
        return stats;
    }

    K operator[](size_t i) const { return begin()[i]; }

    size_t size() const { return n; }

    bool has_duplicates() const { return duplicates; }

    K *begin() const { return data; }

    K *end() const { return data + n; }

    ~PGMWrapper() { delete[] data; }
};

template <typename K> void declare_class(py::module &m, const std::string &name) {
    using PGM = PGMWrapper<K>;
    py::class_<PGM>(m, name.c_str())
        .def(py::init<>())

        .def(py::init<const PGM &, bool>())

        .def(py::init<py::list, bool>())

        .def(py::init<py::iterator, bool>())

        .def(py::init<py::buffer, bool>())

        // sequence protocol
        .def("__len__", &PGM::size)

        .def("__contains__", &PGM::contains)

        .def("__getitem__",
             [](const PGM &p, py::slice slice) -> PGM * {
                 size_t start, stop, step, length;
                 if (!slice.compute(p.size(), &start, &stop, &step, &length))
                     throw py::error_already_set();

                 bool duplicates = false;
                 auto data = new K[length];
                 if (length > 0)
                     data[0] = p[0];
                 for (size_t i = 1; i < length; ++i) {
                     data[i] = p[start];
                     start += step;
                     if (data[i] == data[i - 1])
                         duplicates = true;
                 }

                 return new PGM(data, length, duplicates);
             })

        .def("__getitem__",
             [](const PGM &p, ssize_t i) {
                 if (i < 0)
                     i += p.size();
                 if (i < 0 || (size_t) i >= p.size())
                     throw py::index_error();
                 return p[i];
             })

        // iterator protocol
        .def(
            "__iter__", [](const PGM &p) { return py::make_iterator(p.begin(), p.end()); }, py::keep_alive<0, 1>())

        // query operations
        .def("bisect_left", [](const PGM &p, K x) { return std::distance(p.begin(), p.lower_bound(x)); })

        .def("bisect_right", [](const PGM &p, K x) { return std::distance(p.begin(), p.upper_bound(x)); })

        .def("find_lt",
             [](const PGM &p, K x) {
                 auto it = p.lower_bound(x);
                 if (it <= p.begin())
                     return py::object(py::cast(nullptr));
                 return py::cast(*(it - 1));
             })

        .def("find_le",
             [](const PGM &p, K x) {
                 auto it = p.upper_bound(x);
                 if (it <= p.begin())
                     return py::object(py::cast(nullptr));
                 return py::cast(*(it - 1));
             })

        .def("find_gt",
             [](const PGM &p, K x) -> py::object {
                 auto it = p.upper_bound(x);
                 if (it >= p.end())
                     return py::object(py::cast(nullptr));
                 return py::cast(*it);
             })

        .def("find_ge",
             [](const PGM &p, K x) -> py::object {
                 auto it = p.lower_bound(x);
                 if (it >= p.end())
                     return py::object(py::cast(nullptr));
                 return py::cast(*it);
             })

        .def("rank", [](const PGM &p, K x) { return std::distance(p.begin(), p.upper_bound(x)); })

        .def("count",
             [](const PGM &p, K x) -> size_t {
                 auto lb = p.lower_bound(x);
                 if (lb >= p.end() || *lb != x)
                     return 0;
                 return std::distance(lb, p.upper_bound(x));
             })

        .def(
            "range",
            [](const PGM &p, K a, K b, std::pair<bool, bool> inclusive, bool reverse) {
                auto l_it = inclusive.first ? p.lower_bound(a) : p.upper_bound(a);
                auto r_it = inclusive.second ? p.lower_bound(b) : p.upper_bound(b);
                if (reverse)
                    return py::make_iterator(std::make_reverse_iterator(r_it), std::make_reverse_iterator(l_it));
                return py::make_iterator(l_it, r_it);
            },
            "",
            "a"_a,
            "b"_a,
            "inclusive"_a = std::make_pair(true, true),
            "reverse"_a = false,
            py::keep_alive<0, 1>())

        // list-like operations
        .def(
            "index",
            [](const PGM &p, K x, std::optional<ssize_t> start, std::optional<ssize_t> stop) -> py::object {
                auto it = p.lower_bound(x);
                auto index = (size_t) std::distance(p.begin(), it);

                size_t left, right, step, length;
                auto slice = py::slice(start.value_or(0), stop.value_or(p.size()), 1);
                slice.compute(p.size(), &left, &right, &step, &length);

                if (it >= p.end() || *it != x || index < left || index > right)
                    throw py::value_error(std::to_string(x) + " is not in PGMIndex");
                return py::cast(index);
            },
            "",
            "x"_a,
            "start"_a = std::nullopt,
            "stop"_a = std::nullopt)

        // multiset operations
        .def("merge", &PGM::template merge<const PGM &>)
        .def("merge", &PGM::template merge<const py::array_t<K>>)

        .def("difference", &PGM::template set_difference<const PGM &>)
        .def("difference", &PGM::template set_difference<const py::array_t<K>>)

        .def("symmetric_difference", &PGM::template set_symmetric_difference<const PGM &>)
        .def("symmetric_difference", &PGM::template set_symmetric_difference<const py::array_t<K>>)

        .def("union", &PGM::template set_union<const PGM &>)
        .def("union", &PGM::template set_union<const py::array_t<K>>)

        .def("intersection", &PGM::template set_intersection<const PGM &>)
        .def("intersection", &PGM::template set_intersection<const py::array_t<K>>)

        .def("drop_duplicates",
             [](const PGM &p) {
                 auto tmp = new K[p.size()];
                 auto size = (size_t) std::distance(tmp, std::unique_copy(p.begin(), p.end(), tmp));

                 if (size == p.size())
                     return new PGM(tmp, size, false);

                 auto data = new K[size];
                 std::copy_n(tmp, size, data);
                 delete[] tmp;
                 return new PGM(data, size, false);
             })

        // other methods
        .def("stats", &PGM::stats)

        .def("has_duplicates", &PGM::has_duplicates);
}

PYBIND11_MODULE(_pypgm, m) {
    declare_class<uint32_t>(m, "PGMIndexUInt32");
    declare_class<int32_t>(m, "PGMIndexInt32");
    declare_class<int64_t>(m, "PGMIndexInt64");
    declare_class<uint64_t>(m, "PGMIndexUInt64");
    declare_class<float>(m, "PGMIndexFloat");
    declare_class<double>(m, "PGMIndexDouble");
}