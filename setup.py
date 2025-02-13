import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ace",
    version="1.0.0",
    author="Ryan Roche, Bryant Vencill",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ryan-w-roche/auto-chart-engine",
    packages=setuptools.find_packages(),
    classifiers= [
        "Programming Language :: Python :: 3",
        "Development Status :: Code Drop 2",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Music",
        "Intended Audience :: Clone Hero Drum Charters",
    ]
)