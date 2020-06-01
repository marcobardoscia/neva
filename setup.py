from setuptools import setup

setup(name='neva',
      version='0.2',
      description='Network valuation in financial systems',
      long_description='''This is an implementation of the Neva framework 
                       in https://doi.org/10.1111/mafi.12272. Neva 
                       allows to perform the valuation of equities of banks 
                       that hold cross-holding of debt. Several known 
                       contagion algorithms (e.g. Furfine, Eisenberg and Noe, 
                       and Linear DebtRank) are special cases of Neva.''',
      url='http://github.com/marcobardoscia/neva',
      author='Marco Bardoscia',
      author_email='marco.open@gmail.com',
      license='LGPLv3',
      packages=['neva'],
      include_package_data=True,
      zip_safe=False)
