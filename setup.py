# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""
Amazon SOP-Bench packaging setup.

A benchmark for evaluating LLM agents on Standard Operating Procedures.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version
version = {}
version_file = Path(__file__).parent / "src" / "amazon_sop_bench" / "__version__.py"
with open(version_file) as f:
    exec(f.read(), version)

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

setup(
    name="amazon-sop-bench",
    version=version["__version__"],
    description="Benchmark for evaluating LLM agents on Standard Operating Procedures",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Amazon",
    maintainer="Rohith Nama",
    url="https://github.com/amazon-science/sop-bench",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.28.0",
        "pandas>=2.0.0",
        "pyyaml>=6.0",
        "click>=8.0.0",
        "rich>=13.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            # Testing
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.0",
            "pytest-xdist>=3.3.0",
            "moto[all]>=4.2.0",
            # Code quality
            "black>=23.7.0",
            "ruff>=0.0.285",
            "mypy>=1.5.0",
            "isort>=5.12.0",
            # Type stubs
            "types-PyYAML>=6.0.0",
            "boto3-stubs[bedrock-runtime]>=1.28.0",
            # Build
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "generation": [
            "langchain>=0.1.0",
            "langchain-aws>=0.1.0",
            "jinja2>=3.0.0",
        ],
        "docs": [
            "sphinx>=7.1.0",
            "sphinx-rtd-theme>=1.3.0",
            "sphinx-autodoc-typehints>=1.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sop-bench=amazon_sop_bench.cli.main:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    include_package_data=True,
    package_data={
        "amazon_sop_bench": [
            "benchmarks/data/**/*",
        ],
    },
)
