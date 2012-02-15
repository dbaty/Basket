import os
from setuptools import find_packages
from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()
DESCRIPTION = README

REQUIRES = ()

setup(name='Basket',
      version='0.8',
      description='A local static PyPI repository builder',
      long_description='\n\n'.join((README, CHANGES)),
      classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Software Distribution',
        ),
      author='Damien Baty',
      author_email='damien.baty.remove@gmail.com',
      url='http://packages.python.org/basket',
      keywords='eggs easy_install pip package static repository pypi',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=REQUIRES,
      test_suite='basket.tests',
      entry_points='''
      [console_scripts]
      basket = basket.main:main
      ''')
