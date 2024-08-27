""""Setup script for the thesis-tools project."""

from setuptools import setup, find_packages

setup(
    name="thesis-tools",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.2.2",
        "ollama>=0.3.1",
        "SQLAlchemy>=2.0.32",
    ],
)
