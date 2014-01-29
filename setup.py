from distutils.core import setup

setup(
    name='rrdtool-csv',
    version='1.0',
    description='A script to convert data from rrdtool databases to csv format',
    author='Zmicier Zaleznicenka',
    author_email='Zmicier.Zaleznicenka@gmail.com',
    packages=['rrdtoolcsv'],
    platforms=['Linux'],
    scripts = ['rrdtoolcsv/rrdtool-csv.py'],
    data_files = [('rrdtool-csv',['data/data.json'])]
)