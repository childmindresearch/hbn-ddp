[![DOI](https://zenodo.org/badge/657341621.svg)](https://zenodo.org/doi/10.5281/zenodo.10383685)

# HBN Diagnostic Data Preprocessing
A Python preprocessing package for working with the Healthy Brain Network clinician consensus diagnostic data.

[![Build](https://github.com/childmindresearch/hbn-preprocess/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/childmindresearch/hbn-preprocess/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/childmindresearch/hbn-preprocess/branch/main/graph/badge.svg?token=22HWWFWPW5)](https://codecov.io/gh/childmindresearch/hbn-preprocess)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://childmindresearch.github.io/hbn-preprocess)

## Features
The raw HBN dataset includes final clinician diagnostic data given across ten numbered diagnosis columns. The order of these diagnoses is not indicative of severity, chronology, or importance, and this format requires data manipulation to be useful for analysis. This package transforms the data to a wider format, organized by specific diagnoses or categories rather than diagnosis numbers. It also includes the option to filter by diagnostic certainty or time of diagnosis and creates a visualization of the diagnostic data. Option to either run interactively in the command line (recommended if not familiar with the dataset) or to install as a python package.

| DX_01 | DX_01_Cat | DX_01_Sub | DX_01_Time | DX_01_Confirmed | DX_01_Presum | DX_01_RC | DX_01_RuleOut | DX_02 | DX_02_Cat | DX_02_Sub | DX_02_Time | DX_02_Confirmed | DX_02_Presum | DX_02_RC | DX_02_RuleOut | ... |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADHD - Hyperactive Type | Neurodevelopmental Disorders | ADHD | 1 | 1 | 0 | 0 | 0 | | | | | | | | | ... |
| Selective Mutism | Axiety Disorders | Axiety Disorders | 1 | 1 | 0 | 0 | 0 | Autism Spectrum Disorder | Autism Spectrum Disorder | Neurodevelopmental Disorders | 1 | 0 | 0 | 0 | 1 | ... |

<p align="center">↓</p>

NeurodevelopmentalDisorders_CategoryPresent | ADHDHyperactiveType_DisorderPresent | ADHDHyperactiveType_Time | ADHDHyperactiveType_Certainty | AutismSpectrum_DisorderPresent | AutismSpectrum_Time | AutismSpectrum_Certainty | AnxietyDisorders_CategoryPresent | SelectiveMutism_DisorderPresent | SelectiveMutism_Time | SelectiveMutism_Certainty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | Current | Confirmed | 0 |  |  | 0 | 0 |  |  |
| 1 | 0 |  |  | 1 | Current | Rule-Out | 1 | 1 | Past | Confirmed |

For more information on the HBN data, please see the [HBN Data Portal](https://fcon_1000.projects.nitrc.org/indi/cmi_healthy_brain_network/index.html)


## Installation

Install this package via :

```sh
pip install git+https://github.com/childmindresearch/hbn-preprocess.git
```

## Run interactively in the command line

hbnddp

## Quick start
```python
from hbnddp import HBNData

processed = HBNData.process(
    input_path="path/to/data.csv",
    output_path="path/to/output.csv"
)
```
[Notebook Example](https://github.com/childmindresearch/hbn-preprocess/blob/main/examples/pivot_example.ipynb)

## Links or References
