from setuptools import setup

setup(name='rloopsim',
      version='0.1',
      description='rLoop Hyperloop pod simulator',
      url='http://github.com/rLoopTeam/eng-embed-sim',
      author='Ryan Adams',
      author_email='radams@cyandata.com',
      license='',
      packages=['rloopsim'],
      install_requires=['numpy', 'pint', 'bokeh', 'pandas'],
      zip_safe=False)
