from distutils.core import setup
from Cython.Build import cythonize
from Cython.Distutils import Extension
from distutils.command.build_ext import build_ext

import glob
import os
import os.path
import numpy
import mpi4py

package_basedir = os.path.abspath(os.path.dirname(__file__))

def build_pfft(prefix, compiler, cflags):
    optimize="--enable-sse2"
    line = ('CFLAGS="%s -fvisibility=hidden" ' % cflags+
            'MPICC="%s" ' % compiler +
            'CC="%s" ' % compiler +
            'sh %s/depends/install_pfft.sh ' % package_basedir +
             os.path.abspath(prefix) +
            ' %s' % optimize)
    if os.path.exists(os.path.join(prefix, 
        'lib', 'libpfft.a')):
        return

    ret=os.system(line)
    if ret != 0:
        raise ValueError("could not build fftw; check MPICC?")

def myext(*args):
    return 

extensions = [
        ]

class build_ext_subclass(build_ext):
    user_options = build_ext.user_options + \
            [
            ('mpicc', None, 'MPICC')
            ]
    def initialize_options(self):
        try:
            compiler = str(mpi4py.get_config()['mpicc'])
        except:
            pass
        compiler = "mpicc"
        self.mpicc = os.environ.get('MPICC', compiler)

        build_ext.initialize_options(self)    

    def finalize_options(self):
        build_ext.finalize_options(self)    
        self.pfft_build_dir = os.path.join(self.build_temp, 'depends')

        self.include_dirs.insert(0, os.path.join(
                        self.pfft_build_dir, 'include'))

    def build_extensions(self):
        # turns out set_executables only works for linker_so, but for compiler_so
        self.compiler.compiler_so[0] = self.mpicc
        self.compiler.linker_so[0] = self.mpicc
        build_pfft(self.pfft_build_dir, self.mpicc, ' '.join(self.compiler.compiler_so[1:]))
        link_objects = [ 
                'libpfft.a', 
                'libpfftf.a',
                'libfftw3_mpi.a', 
                'libfftw3.a', 
                'libfftw3f_mpi.a', 
                'libfftw3f.a', 
                ]
        
        link_objects = [list(glob.glob(os.path.join(self.pfft_build_dir, '*', i)))[0] for i in link_objects]
        self.compiler.set_link_objects(link_objects)

        #for ext in self.extensions:
        #    ext.depends += link_objects

        build_ext.build_extensions(self)

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

setup(
    name="pfft-python", version="0.1.5",
    author="Yu Feng",
    author_email="rainwoodman@gmail.com",
    description="python binding of PFFT, a massively parallel FFT library",
    url="http://github.com/rainwoodman/pfft-python",
    #package_dir = {'pfft': 'pfft'},
    zip_safe=False,
    install_requires=['cython', 'numpy'],
    packages= ['pfft'],
    requires=['numpy'],
    ext_modules = cythonize(Extension( 
                "pfft.core", 
                ["pfft/core.pyx"],
                include_dirs=["./", 
                numpy.get_include(),
                ],
                cython_directives = {"embedsignature": True}
                )),
    cmdclass = {
        "build_py":build_py,
        "build_ext": build_ext_subclass}
)

