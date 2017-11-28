from setuptools import setup

setup(name='ranking_table_tennis',
      version='0.1',
      description='A ranking table tennis system',
      url='http://github.com/srvanrell/ranking-table-tennis',
      author='Sebastián Vanrell',
      author_email='srvanrell@gmail.com',
      license='MIT',
      packages=['ranking_table_tennis'],
      scripts=['bin/preprocess.py'],
      include_package_data=True,
      zip_safe=False)
