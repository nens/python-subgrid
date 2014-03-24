from setuptools import setup
import sys
version = '0.15.dev0'

long_description = '\n\n'.join([
    open('README.rst').read(),
    open('CREDITS.rst').read(),
    open('CHANGES.rst').read(),
    ])

install_requires = [
    'setuptools',
    'numpy',
    'pandas',
    'webob',
    'netCDF4',
    'mmi',
    'scipy',
    'psutil'
    ]

if sys.version_info[0] < 3:
    install_requires.append('faulthandler')


tests_require = [
    'nose',
    'mock',
    'coverage',
    'psutil'
    ]

setup(
    name='python-subgrid',
    version=version,
    description="Python wrapper for the 3Di fortran subgrid library",
    long_description=long_description,
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Intended Audience :: Science/Research"
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development :: Libraries"
    ],
    keywords=["3Di", "subgrid", "hydrodynamic", "simulation", "flooding", "BMI"],
    author='Fedor Baart',
    author_email='fedor.baart@deltares.nl',
    url='https://github.com/nens/python-subgrid',
    license='GPLv3+',
    packages=['python_subgrid'],
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require={'test': tests_require},
    entry_points={
        'console_scripts': [
            '{0} = python_subgrid.utils:{0}'.format(
                'generate_functions_documentation'),
            '{0} = python_subgrid.tools.convert_mdu:main'.format(
                'convert-subgrid-mdu'),
            '{0} = python_subgrid.tools.update_mdu:main'.format(
                'update-subgrid-mdu'),
            '{0} = python_subgrid.tools.update_network:main'.format(
                'update-subgrid-network'),
            '{0} = python_subgrid.tools.update_tables:main'.format(
                'update-subgrid-tables'),
            '{0} = python_subgrid.tools.subgridpy:main'.format(
                'subgridpy')
        ]
    }
)
