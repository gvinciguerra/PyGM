import glob
import os
import subprocess
import sys
import tempfile

import setuptools
from setuptools.command.build_ext import build_ext

__version__ = '0.1a0'


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
        'pygm._pygm',
        ['pygm/pygm.cpp'],
        include_dirs=[
            get_pybind_include(),
            'PGM-index/include',
        ],
        language='c++'
    ),
]


def is_clang(bin):
    """Check whether the compiler is clang."""
    output = subprocess.check_output([bin, '-v'], stderr=subprocess.STDOUT)
    return 'clang' in output.decode('ascii', 'ignore')


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""

    def build_extensions(self):
        comp_args = ['-std=c++17', '-O3', '-fvisibility=hidden']
        link_args = []

        if sys.platform == 'darwin' and is_clang(self.compiler.compiler[0]):
            omp = '/usr/local/opt/libomp'
            omp_lib = self.compiler.find_library_file([omp + '/lib'], 'omp')
            if omp_lib is not None:
                print('libomp found on macOS')
                comp_args += ['-Xpreprocessor',
                              '-fopenmp',
                              '-I%s/include/' % omp]
                link_args += ['-L%s/lib' % omp,
                              '-lomp']
            comp_args += ['-mmacosx-version-min=10.9']
            link_args += ['-mmacosx-version-min=10.9']
        elif has_flag(self.compiler, '-fopenmp'):
            comp_args += ['-fopenmp']
            link_args += ['-fopenmp']

        for ext in self.extensions:
            ext.extra_compile_args = comp_args
            ext.extra_link_args = link_args

        build_ext.build_extensions(self)


if sys.version_info[:2] < (3, 3):
    raise RuntimeError("Python version >= 3.3 required.")

if 'CXX' not in os.environ:
    path = os.getenv('PATH').split(os.path.pathsep)
    globs = [os.path.join(p, 'g++*') for p in path]
    gccs = [g for p in globs for g in glob.glob(p)]
    gccs = sorted(gccs, key=lambda p: os.path.basename(p))
    if len(gccs) > 0:
        os.environ["CC"] = gccs[-1]
        os.environ["CXX"] = gccs[-1]
        print('Found GCC in ', gccs[-1])

setuptools.setup(
    name='pygm',
    version=__version__,
    author='Giorgio Vinciguerra',
    author_email='i@gvdev.com',
    url='https://pgm.di.unipi.it/',
    project_urls={
        'Documentation': 'https://pgm.di.unipi.it/docs/python-reference/',
        'Source': 'https://github.com/gvinciguerra/PyGM/',
        'Tracker': 'https://github.com/gvinciguerra/PyGM/issues',
    },
    license='GPL-3.0',
    description=('Sorted containers with state-of-the-art query performance '
                 'and compressed memory usage'),
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    ext_modules=ext_modules,
    packages=setuptools.find_packages(),
    setup_requires=['pybind11>=2.5.0'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Natural Language :: English',
        'Programming Language :: C++',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Database',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Software Development',
        'Topic :: System',
        'Topic :: System :: Archiving :: Compression',
        'Topic :: Utilities',
    ],
    keywords=('tree list array btree b+tree vector skiplist container '
              'sortedlist sorted set query index data structure'),
)
