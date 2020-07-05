#include <pybind11/numpy.h>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <algorithm>
#include <regex>
#include <unordered_map>
#include <vector>

#include "pgm_index.hpp"

namespace py = pybind11;
using namespace pybind11::literals;

template <typename K> class PGMWrapper {
    K *data;
    size_t n;
    PGMIndex<K> pgm;

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

  public:
    PGMWrapper() = default;

    PGMWrapper(const std::vector<K> &vector) : n(vector.size()) {
        data = new K[n];
        std::copy_n(vector.data(), n, data);
        if (!std::is_sorted(begin(), end()))
            std::sort(begin(), end());
        build_pgm();
    }

    PGMWrapper(py::list l) {
        n = l.size();
        data = new K[n];
        for (auto i = 0ull; i < n; ++i)
            data[i] = implicit_cast(l[i]);
        if (!std::is_sorted(begin(), end()))
            std::sort(begin(), end());
        build_pgm();
    }

    PGMWrapper(py::iterator it) {
        std::vector<K> v;
        for (; it != py::iterator::sentinel(); ++it)
            v.push_back(implicit_cast(*it));
        n = v.size();
        data = new K[n];
        std::copy_n(v.data(), n, data);
        if (!std::is_sorted(begin(), end()))
            std::sort(begin(), end());
        build_pgm();
    }

    PGMWrapper(K *data, size_t n) : data(data), n(n) { build_pgm(); }

#define FORMAT_TYPE_CASE(c, type)                                                                                      \
    case c:                                                                                                            \
        std::copy_n((type *) info.ptr, n, data);                                                                       \
        break;

    PGMWrapper(py::buffer b) {
        py::buffer_info info = b.request();
        if (info.ndim != 1)
            throw py::type_error("Incorrect number of dimensions: " + std::to_string(info.ndim) + "; expected 1");

        n = info.shape[0];
        data = new K[n];
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
        auto step = 1ull;
        while (it + step < end() && *(it + step) == x)
            step *= 2;
        return std::upper_bound(it + (step / 2), std::min(it + step, end()), x);
    }

    template <set_fun F> PGMWrapper *set_operation(py::array_t<K> &a, size_t out_size_hint) const {
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
            return new PGMWrapper<K>(tmp_out, out_size);

        auto out = new K[out_size];
        std::copy_n(tmp_out, out_size, out);
        delete[] tmp_out;
        return new PGMWrapper<K>(out, out_size);
    }

    template <set_fun F> PGMWrapper *set_operation(const PGMWrapper<K> &q, size_t out_size_hint) const {
        auto tmp_out = new K[out_size_hint];
        auto tmp_out_end = F(begin(), end(), q.begin(), q.end(), tmp_out);
        auto out_size = (size_t) std::distance(tmp_out, tmp_out_end);

        if (out_size == out_size_hint)
            return new PGMWrapper<K>(tmp_out, out_size);

        auto out = new K[out_size];
        std::copy_n(tmp_out, out_size, out);
        delete[] tmp_out;
        return new PGMWrapper<K>(out, out_size);
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

    K *begin() const { return data; }

    K *end() const { return data + n; }

    ~PGMWrapper() { delete[] data; }
};

template <typename K> void declare_class(py::module &m, const std::string &name) {
    using PGM = PGMWrapper<K>;
    py::class_<PGM>(m, name.c_str())
        .def(py::init<>())

        .def(py::init<py::list>())

        .def(py::init<py::iterator>())

        .def(py::init<py::buffer>())

        // sequence protocol
        .def("__len__", &PGM::size)

        .def("__contains__", &PGM::contains)

        .def("__getitem__",
             [](const PGM &p, py::slice slice) -> PGM * {
                 size_t start, stop, step, length;
                 if (!slice.compute(p.size(), &start, &stop, &step, &length))
                     throw py::error_already_set();

                 auto data = new K[length];
                 for (size_t i = 0; i < length; ++i) {
                     data[i] = p[start];
                     start += step;
                 }

                 return new PGM(data, length);
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
        .def("__add__",
             [](const PGM &p, py::array_t<K> a) {
                 return p.template set_operation<std::merge>(a, p.size() + a.shape(0));
             })

        .def("__add__",
             [](const PGM &p, const PGM &q) { return p.template set_operation<std::merge>(q, p.size() + q.size()); })

        .def("__sub__",
             [](const PGM &p, py::array_t<K> a) { return p.template set_operation<std::set_difference>(a, p.size()); })

        .def("__sub__",
             [](const PGM &p, const PGM &q) { return p.template set_operation<std::set_difference>(q, p.size()); })

        .def("drop_duplicates",
             [](const PGM &p) {
                 auto tmp = new K[p.size()];
                 auto size = (size_t) std::distance(tmp, std::unique_copy(p.begin(), p.end(), tmp));

                 if (size == p.size())
                     return new PGM(tmp, size);

                 auto data = new K[size];
                 std::copy_n(tmp, size, data);
                 delete[] tmp;
                 return new PGM(data, size);
             })

        // other methods
        .def("stats", &PGM::stats);
}

PYBIND11_MODULE(_pypgm, m) {
    m.attr("__name__") = "pypgm._pypgm";
    declare_class<uint32_t>(m, "PGMIndexUInt32");
    declare_class<int32_t>(m, "PGMIndexInt32");
    declare_class<int64_t>(m, "PGMIndexInt64");
    declare_class<uint64_t>(m, "PGMIndexUInt64");
    declare_class<float>(m, "PGMIndexFloat");
    declare_class<double>(m, "PGMIndexDouble");
}