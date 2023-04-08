from setuptools import setup, find_packages

setup(
    name="lottery_data_scraper",
    version="0.0.1",
    author="Eric Ihli",
    author_email="eihli@owoga.com",
    url="https://github.com/owogac/lottery_data_scraper",
    packages=find_packages(),
    install_requires=[
        "beautifulsoup4",
        "requests==2.28.2",
        "urllib3==1.26.15",
        "numpy",
        "pandas",
        "lxml",
        "html2text",
        "html5lib",
        "marshmallow==3.19.0",
        "selenium==3.141.0",
        "pybind11",
        # If you want to develop locally and don't want to mess around with
        # Xvfb (https://en.wikipedia.org/wiki/Xvfb), then just comment out
        # the next line before you run `python3 setup.py install`.
        "xvfbwrapper==0.2.9",
        "table_ocr==0.2.5",
    ],
)
