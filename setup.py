#!/usr/bin/env python3
"""
Setup script for Plugwise Pi project.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="plugwise-pi",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python-based system for collecting data from Plugwise domotics devices",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/plugwise_pi",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Home Automation",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "black",
            "flake8",
            "mypy",
            "pytest",
            "pytest-cov",
            "pytest-asyncio",
        ],
    },
    entry_points={
        "console_scripts": [
            "plugwise-collector=plugwise_pi.collector:main",
            "plugwise-api=plugwise_pi.api:main",
        ],
    },
    include_package_data=True,
    package_data={
        "plugwise_pi": ["config/*.yaml", "config/*.yml"],
    },
) 