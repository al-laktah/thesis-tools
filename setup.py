""""Setup script for the thesis-tools project."""

from setuptools import setup, find_packages

setup(
    name="thesis-tools",
    version="0.3.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pandas>=2.2.2",
        "numpy>=1.21.2",
        "ollama>=0.3.1",
        "SQLAlchemy>=2.0.32",
        "language_tool_python>=2.8.1",
        "diff_match_patch>=20230430"
        "matplotlib>=3.9.2",
        "seaborn>=0.11.2",
    ],
)
