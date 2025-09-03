#!/usr/bin/env python3
"""Simple setup script for gg-shuffle."""

from setuptools import setup, find_packages

setup(
    name="gg-shuffle",
    version="1.0.0",
    description="Game Grumps episode randomizer with GTK GUI",
    author="Brandon",
    python_requires=">=3.8",
    py_modules=["gg-shuffle"],
    install_requires=[
        "PyGObject>=3.42.0",
        "yt-dlp>=2023.7.6",
    ],
    entry_points={
        "console_scripts": [
            "gg-shuffle=gg-shuffle:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Games/Entertainment",
    ],
)
