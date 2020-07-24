from distutils.core import setup, Extension
import numpy

setup(name = 'cPSCS', version = '1.0',  \
   ext_modules = [Extension('cPSCS', ['cmodule.c'], include_dirs=[numpy.get_include()])])
