from setuptools import setup, find_packages

setup(
    name='backup',
    version='1.0.0',
    author='Cezary Maszczyk',
    author_email='cezary.maszczyk@gmail.com',
    description='Package for automatic backups',
    packages=find_packages(),
    install_requires=[
        'click>=8.0.1',
        'requests>=0.10',
        'pycryptodome>=3.9.6,<4.0.0',
        'pathlib==1.0.1',
        'tenacity>=5.1.5,<6.0.0',
    ],
)
