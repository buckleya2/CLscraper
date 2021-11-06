from setuptools import setup, find_packages

setup(
    name='CLscraper Setup File',
    version='1.0',
    packages=find_packages(),
    entry_points={'console_scripts' : ['CLscraper=CLscraper.start:main']}
)
