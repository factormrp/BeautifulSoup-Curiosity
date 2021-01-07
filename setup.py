from setuptools import find_packages, setup
setup(
    name='foodscrape',
    packages=find_packages(include=['foodscrape']),
    version='0.0.5',
    description='Custom scraping library for allrecipes.com',
    author='Maximiliano Rivera-Patton',
    license='MIT',
    install_requires=['bs4'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest==4.4.1'],
    test_suite='tests'
)