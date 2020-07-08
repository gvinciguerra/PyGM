import os
import subprocess
import sys
import tempfile

import setuptools
from setuptools.command.build_ext import build_ext


__version__ = '0.1'


class get_pybind_include(object):
    """Helper class to determine the pybind11 include path."""

    def __str__(self):
        import pybind11
        return pybind11.get_include()


def has_flag(compiler, flag):
    """Check whether a flag is supported on the specified compiler."""
    with tempfile.NamedTemporaryFile('w', suffix='.cpp') as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        try:
            compiler.compile([f.name], extra_postargs=[flag])
        except setuptools.distutils.errors.CompileError:
            return False
    return True


ext_modules = [
    setuptools.Extension(
        'pypgm._pypgm',
        ['pypgm/pypgm.cpp'],
        include_dirs=[
            get_pybind_include(),
            'PGM-index/include',
        ],
        language='c++'
    ),
]


def box_msg(msg):
    """Create an ASCII box around a string."""
    row = len(msg)
    h = ''.join(['+'] + ['-' * row] + ['+'])
    return h + '\n'"|" + msg + "|"'\n' + h


def is_clang(bin):
    """Check whether the compiler is clang."""
    output = subprocess.check_output([bin, '-v'], stderr=subprocess.STDOUT)
    return 'clang' in output.decode('ascii', 'ignore')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    def build_extensions(self):
        comp_args = ['-std=c++17', '-O3', '-fvisibility=hidden']
        link_args = []

        print('is_clang', is_clang(self.compiler.compiler[0]))
        if sys.platform == 'darwin' and is_clang(self.compiler.compiler[0]):
            omp = '/usr/local/opt/libomp'
            if self.compiler.find_library_file([omp + '/lib'], 'omp') is None:
                sys.exit(box_msg('OpenMP is needed. Run brew install libomp'))
            comp_args += ['-Xpreprocessor',
                          '-fopenmp',
                          '-mmacosx-version-min=10.9',
                          '-I%s/include/' % omp]
            link_args += ['-L%s/lib' % omp,
                          '-lomp',
                          '-mmacosx-version-min=10.9']
        else:
            comp_args += ['-fopenmp']
            link_args += ['-fopenmp']

        for ext in self.extensions:
            ext.extra_compile_args = comp_args
            ext.extra_link_args = link_args
        build_ext.build_extensions(self)


setuptools.setup(
    name='pypgm',
    version=__version__,
    author='Giorgio Vinciguerra',
    author_email='i@gvdev.com',
    url='https://github.com/gvinciguerra/PyPGM',
    license='GPL-3.0',
    description='Python wrapper for the PGM-index',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    ext_modules=ext_modules,
    packages=setuptools.find_packages(),
    setup_requires=['pybind11>=2.5.0'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: GPL-3.0 License',
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3',
        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: System',
        'Topic :: System :: Archiving :: Compression',
    ],
    keywords='tree list array btree b+tree vector skiplist container sortedlist sorted set query index data structure',
)
