import sys
from setuptools import setup

try:
    import pypandoc
    readme = pypandoc.convert('README.md', 'rst')
    readme = readme.replace("\r", "")
except ImportError:
    import io
    with io.open('README.md', encoding="utf-8") as f:
        readme = f.read()

setup(name='modbus_logger',
      version=1.1,
      description='Read data using RS485 Modbus '+
      'and store in local database.',
      long_description=readme,
      url='https://github.com/GuillermoElectrico/modbus-logger',
      download_url='',
      author='Samuel Vestlin',
      author_email='samuel@elphy.se',
      platforms='Raspberry Pi',
      classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: MIT License',
        'Operating System :: Raspbian',
        'Programming Language :: Python :: 3.5'
      ],
      keywords='Energy Meter RS485 Modbus',
      install_requires=[]+(['setuptools','ez_setup','pyserial','minimalmodbus', 'influxdb', 'pyyaml'] if "linux" in sys.platform else []),
      license='MIT',
      packages=[],
      include_package_data=True,
      tests_require=[],
      test_suite='',
      zip_safe=True)
