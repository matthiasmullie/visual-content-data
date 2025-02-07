from setuptools import find_packages, setup

setup(
    name='visual-content-data',
    description='Visual Content data',
    version='0.0.1.dev0',
    author='Matthias Mullie',
    author_email='mmullie@wikimedia.org',
    license='MIT',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
)
