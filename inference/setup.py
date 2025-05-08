#!/usr/bin/env python3
"""
Setup script for Dia TTS Inference package
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="dia-tts-inference",
    version="1.0.0",
    author="Tucker Kirven",
    author_email="example@example.com",
    description="Client for Dia TTS RunPod serverless inference",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/username/dia-tts-inference",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "python-dotenv>=0.20.0",
        "numpy>=1.20.0",
        "soundfile>=0.10.3",
    ],
    entry_points={
        "console_scripts": [
            "dia-tts=inference.inference:main",
        ],
    },
)