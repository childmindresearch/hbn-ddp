[![DOI](https://zenodo.org/badge/657341621.svg)](https://zenodo.org/doi/10.5281/zenodo.10383685)

# HBN Preprocess

[![Build](https://github.com/childmindresearch/hbn-preprocess/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/childmindresearch/hbn-preprocess/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/childmindresearch/hbn-preprocess/branch/main/graph/badge.svg?token=22HWWFWPW5)](https://codecov.io/gh/childmindresearch/hbn-preprocess)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://childmindresearch.github.io/hbn-preprocess)

## Features

- Diagnostic data preprocessing: Pivots the data to a wider format, organized by specific diagnoses or categories rather than diagnosis numbers. Includes the option to filter by diagnostic qualifier (certainty or time of diagnosis). Option to either run interactively or install as a package and use in a notebook.

## Installation

Install this package via :

```sh
pip install git+https://github.com/childmindresearch/hbn-preprocess.git
```

## Run interactively

python -m hbnpreprocess

## Quick start
```sh
from hbnpreprocess.hbn_data import HBNData
HBNData.process()
```
Notebook example: [Notebook Example](https://github.com/childmindresearch/hbn-preprocess/blob/main/examples/pivot_example.ipynb)

## Links or References
