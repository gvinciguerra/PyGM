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

template <class InputIt1, class InputIt2>
bool set_unique_includes(InputIt1 first1, InputIt1 last1, InputIt2 first2, InputIt2 last2, bool proper) {
    bool is_proper = !proper;

    for (; first2 != last2; ++first1) {
        if (first1 == last1 || *first2 < *first1)
            return false;

        if (!(*first1 < *first2)) {
            ++first2;
            while (first2 != last2 && *first2 == *first1)
                ++first2;
        } else
            is_proper = true;
    }

    is_proper |= first1 != last1;
    return true && is_proper;
}

#define EPSILON_RECURSIVE 4

template <typename K> class PGMWrapper : private PGMIndex<K, 1, EPSILON_RECURSIVE, double> {
    std::vector<K> data;
    bool duplicates;
    size_t epsilon = 64;

    void build_internal_pgm() {
        this->n = size();
        if (this->n == 0) {
            this->first_key = 0;
            return;
        }
        this->first_key = data.front();
        if (this->n < 1ull << 15)
            this->build(begin(), end(), epsilon, EPSILON_RECURSIVE);
        else {
            py::gil_scoped_release release;
            this->build(begin(), end(), epsilon, EPSILON_RECURSIVE);
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
    using iterator = typename std::vector<K>::iterator;
    using const_iterator = typename std::vector<K>::const_iterator;

    PGMWrapper() = default;

    PGMWrapper(const PGMWrapper &p, bool drop_duplicates, size_t epsilon) : epsilon(epsilon) {
        if (epsilon < 16)
            throw std::invalid_argument("epsilon must be >= 16");

        if (p.has_duplicates() && drop_duplicates) {
            data.reserve(p.size());
            std::unique_copy(p.begin(), p.end(), std::back_inserter(data));
            data.shrink_to_fit();
            duplicates = false;
            build_internal_pgm();
            return;
        }

        data = p.data;
        duplicates = p.duplicates;

        if (p.get_epsilon() == epsilon) {
            this->n = p.n;
            this->segments = p.segments;
            this->first_key = p.first_key;
            this->levels_sizes = p.levels_sizes;
            this->levels_offsets = p.levels_offsets;
        } else {
            build_internal_pgm();
        }
    }

    PGMWrapper(py::iterator it, size_t size_hint, bool drop_duplicates, size_t epsilon) : epsilon(epsilon) {
        if (epsilon < 16)
            throw std::invalid_argument("epsilon must be >= 16");

        auto sorted = true;
        data.reserve(size_hint);
        if (it != py::iterator::sentinel())
            data.push_back(implicit_cast(*it++));
        for (; it != py::iterator::sentinel(); ++it) {
            auto x = implicit_cast(*it);
            if (x < data.back())
                sorted = false;
            data.push_back(x);
        }

        if (!sorted)
            std::sort(data.begin(), data.end());
        if (drop_duplicates) {
            data.erase(std::unique(data.begin(), data.end()), data.end());
            duplicates = false;
        } else
            duplicates = true;

        data.shrink_to_fit();
        build_internal_pgm();
    }

    PGMWrapper(std::vector<K> &&data, bool duplicates, size_t epsilon)
        : data(std::move(data)), duplicates(duplicates), epsilon(epsilon) {
        if (epsilon < 16)
            throw std::invalid_argument("epsilon must be >= 16");
        build_internal_pgm();
    }

    ApproxPos find_approximate_position(const K &key) const {
        auto k = std::max(this->first_key, key);
        auto it = this->segment_for_key(k);
        auto pos = std::min<size_t>((*it)(k), std::next(it)->intercept);
        auto lo = SUB_ERR(pos, epsilon);
        auto hi = ADD_ERR(pos, epsilon + 1, this->n);
        return {pos, lo, hi};
    }

    bool contains(K x) const {
        auto ap = find_approximate_position(x);
        return std::binary_search(data.begin() + ap.lo, data.begin() + ap.hi, x);
    }

    const_iterator lower_bound(K x) const {
        auto ap = find_approximate_position(x);
        return std::lower_bound(data.begin() + ap.lo, data.begin() + ap.hi, x);
    }

    const_iterator upper_bound(K x) const {
        auto ap = find_approximate_position(x);
        auto it = std::upper_bound(data.begin() + ap.lo, data.begin() + ap.hi, x);
        if (!duplicates)
            return it;

        auto step = 1ull;
        while (it + step < end() && *(it + step) == x)
            step *= 2;
        return std::upper_bound(it + (step / 2), std::min(it + step, end()), x);
    }

    template <typename O> PGMWrapper<K> *merge(const O &o, size_t o_size) const {
        return set_operation<std::merge>(o, o_size, size() + o_size, true);
    }

    template <typename O> PGMWrapper<K> *set_difference(const O &o, size_t o_size) const {
        return set_operation<std::set_difference>(o, o_size, size(), false);
    }

    template <typename O> PGMWrapper<K> *set_symmetric_difference(const O &o, size_t o_size) const {
        return set_operation<set_unique_symmetric_difference>(o, o_size, size() + o_size, false);
    }

    template <typename O> PGMWrapper<K> *set_union(const O &o, size_t o_size) const {
        return set_operation<set_unique_union>(o, o_size, size() + o_size, false);
    }

    template <typename O> PGMWrapper<K> *set_intersection(const O &o, size_t o_size) const {
        assert(!has_duplicates()); // otherwise std::set_intersection may output duplicates
        return set_operation<std::set_intersection>(o, o_size, std::min(size(), o_size), false);
    }

    template <bool Reverse> bool subset(const PGMWrapper<K> &q, size_t, bool proper) const {
        if constexpr (Reverse)
            return set_unique_includes(begin(), end(), q.begin(), q.end(), proper);
        return set_unique_includes(q.begin(), q.end(), begin(), end(), proper);
    }

    template <bool Reverse> bool subset(py::iterator it, size_t it_size_hint, bool proper) const {
        auto tmp = to_sorted_vector(it, it_size_hint);
        if constexpr (Reverse)
            return set_unique_includes(begin(), end(), tmp.begin(), tmp.end(), proper);
        return set_unique_includes(tmp.begin(), tmp.end(), begin(), end(), proper);
    }

    bool equal_to(const PGMWrapper<K> &q, size_t) const { return data == q.data; }

    bool equal_to(py::iterator it, size_t it_size_hint) const { return data == to_sorted_vector(it, it_size_hint); }

    bool not_equal_to(const PGMWrapper<K> &q, size_t) const { return data != q.data; }

    bool not_equal_to(py::iterator it, size_t it_size_hint) const { return data != to_sorted_vector(it, it_size_hint); }

    std::unordered_map<std::string, size_t> stats() const {
        std::unordered_map<std::string, size_t> stats;
        stats["epsilon"] = get_epsilon();
        stats["height"] = this->height();
        stats["index size"] = this->size_in_bytes();
        stats["data size"] = sizeof(K) * size() + sizeof(*this);
        stats["leaf segments"] = this->segments_count();
        return stats;
    }

    K operator[](size_t i) const { return data[i]; }

    size_t size() const { return data.size(); }

    size_t get_epsilon() const { return epsilon; }

    bool has_duplicates() const { return duplicates; }

    auto begin() { return data.begin(); }

    auto end() { return data.end(); }

    auto begin() const { return data.cbegin(); }

    auto end() const { return data.cend(); }

  private:
    using back_iterator = typename std::back_insert_iterator<std::vector<K>>;
    using set_fun = back_iterator (*)(const_iterator, const_iterator, const_iterator, const_iterator, back_iterator);

    static std::vector<K> to_sorted_vector(py::iterator &it, size_t it_size_hint) {
        std::vector<K> tmp;
        tmp.reserve(it_size_hint);

        auto sorted = true;
        if (it != py::iterator::sentinel())
            tmp.push_back(implicit_cast(*it++));
        for (; it != py::iterator::sentinel(); ++it) {
            auto x = implicit_cast(*it);
            if (x < tmp.back())
                sorted = false;
            tmp.push_back(x);
        }

        if (!sorted)
            std::sort(tmp.begin(), tmp.end());
        return tmp;
    }

    template <set_fun F>
    PGMWrapper<K> *set_operation(py::iterator it, size_t it_size_hint, size_t size_hint,
                                 bool generates_duplicates) const {
        std::vector<K> out;
        out.reserve(size_hint);
        auto tmp = to_sorted_vector(it, it_size_hint);
        F(begin(), end(), tmp.begin(), tmp.end(), std::back_inserter(out));
        out.shrink_to_fit();
        return new PGMWrapper<K>(std::move(out), generates_duplicates, epsilon);
    }

    template <set_fun F>
    PGMWrapper<K> *set_operation(const PGMWrapper<K> &q, size_t, size_t size_hint, bool generates_duplicates) const {
        std::vector<K> out;
        out.reserve(size_hint);
        F(begin(), end(), q.begin(), q.end(), std::back_inserter(out));
        out.shrink_to_fit();
        return new PGMWrapper<K>(std::move(out), generates_duplicates, epsilon);
    }
};

template <typename K> void declare_class(py::module &m, const std::string &name) {
    using PGM = PGMWrapper<K>;
    py::class_<PGM>(m, name.c_str())
        .def(py::init<>())
        .def(py::init<const PGM &, bool, size_t>())
        .def(py::init<py::iterator, size_t, bool, size_t>())

        // sequence protocol
        .def("__len__", &PGM::size)

        .def("__contains__", &PGM::contains)

        .def(
            "slice",
            [](const PGM &p, py::slice slice) -> PGM * {
                size_t start, stop, step, length;
                if (!slice.compute(p.size(), &start, &stop, &step, &length))
                    throw py::error_already_set();

                bool duplicates = false;
                std::vector<K> out;
                out.reserve(length);
                if (length > 0) {
                    out.push_back(p[start]);
                    start += step;
                }
                for (size_t i = 1; i < length; ++i) {
                    auto x = p[start];
                    start += step;
                    if (x == out.back())
                        duplicates = true;
                    out.push_back(x);
                }

                return new PGM(std::move(out), duplicates, p.get_epsilon());
            },
            "slice"_a.noconvert())

        .def(
            "__getitem__",
            [](const PGM &p, ssize_t i) {
                if (i < 0)
                    i += p.size();
                if (i < 0 || (size_t) i >= p.size())
                    throw py::index_error();
                return p[i];
            },
            "i"_a.noconvert())

        .def(
            "__iter__", [](const PGM &p) { return py::make_iterator(p.begin(), p.end()); }, py::keep_alive<0, 1>())

        .def(
            "__reversed__",
            [](const PGM &p) {
                return py::make_iterator(std::make_reverse_iterator(p.end()), std::make_reverse_iterator(p.begin()));
            },
            py::keep_alive<0, 1>())

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
                auto r_it = inclusive.second ? p.upper_bound(b) : p.lower_bound(b);
                if (reverse)
                    return py::make_iterator(std::make_reverse_iterator(r_it), std::make_reverse_iterator(l_it));
                return py::make_iterator(l_it, r_it);
            },
            py::keep_alive<0, 1>())

        // list-like operations
        .def("index",
             [](const PGM &p, K x, std::optional<ssize_t> start, std::optional<ssize_t> stop) -> py::object {
                 auto it = p.lower_bound(x);
                 auto index = (size_t) std::distance(p.begin(), it);

                 size_t left, right, step, length;
                 auto slice = py::slice(start.value_or(0), stop.value_or(p.size()), 1);
                 slice.compute(p.size(), &left, &right, &step, &length);

                 if (it >= p.end() || *it != x || index < left || index > right)
                     throw py::value_error(std::to_string(x) + " is not in PGMIndex");
                 return py::cast(index);
             })

        // multiset operations
        .def("merge", &PGM::template merge<const PGM &>)
        .def("merge", &PGM::template merge<py::iterator>)

        .def("drop_duplicates", [](const PGM &p) { return new PGM(p, true, p.get_epsilon()); })

        // set operations
        .def("difference", &PGM::template set_difference<const PGM &>)
        .def("difference", &PGM::template set_difference<py::iterator>)

        .def("symmetric_difference", &PGM::template set_symmetric_difference<const PGM &>)
        .def("symmetric_difference", &PGM::template set_symmetric_difference<py::iterator>)

        .def("union", &PGM::template set_union<const PGM &>)
        .def("union", &PGM::template set_union<py::iterator>)

        .def("intersection", &PGM::template set_intersection<const PGM &>)
        .def("intersection", &PGM::template set_intersection<py::iterator>)

        .def("subset", py::overload_cast<const PGM &, size_t, bool>(&PGM::template subset<false>, py::const_))
        .def("subset", py::overload_cast<py::iterator, size_t, bool>(&PGM::template subset<false>, py::const_))

        .def("superset", py::overload_cast<const PGM &, size_t, bool>(&PGM::template subset<true>, py::const_))
        .def("superset", py::overload_cast<py::iterator, size_t, bool>(&PGM::template subset<true>, py::const_))

        .def("equal_to", py::overload_cast<const PGM &, size_t>(&PGM::equal_to, py::const_))
        .def("equal_to", py::overload_cast<py::iterator, size_t>(&PGM::equal_to, py::const_))

        .def("not_equal_to", py::overload_cast<const PGM &, size_t>(&PGM::not_equal_to, py::const_))
        .def("not_equal_to", py::overload_cast<py::iterator, size_t>(&PGM::not_equal_to, py::const_))

        // other methods
        .def("stats", &PGM::stats)

        .def("has_duplicates", &PGM::has_duplicates);
}

PYBIND11_MODULE(_pygm, m) {
    declare_class<uint32_t>(m, "PGMIndexUInt32");
    declare_class<int32_t>(m, "PGMIndexInt32");
    declare_class<int64_t>(m, "PGMIndexInt64");
    declare_class<uint64_t>(m, "PGMIndexUInt64");
    declare_class<float>(m, "PGMIndexFloat");
    declare_class<double>(m, "PGMIndexDouble");
}