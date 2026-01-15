[![DOI](https://zenodo.org/badge/657341621.svg)](https://zenodo.org/doi/10.5281/zenodo.10383685)

# HBN Diagnostic Data Preprocessing
A Python preprocessing package for working with the Healthy Brain Network clinician consensus diagnostic data.

[![Build](https://github.com/childmindresearch/hbn-ddp/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/childmindresearch/hbn-ddp/actions/workflows/test.yaml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/childmindresearch/hbn-ddp/branch/main/graph/badge.svg?token=721bbea6-7f0a-4f6b-a6e5-33f4dee8c3b4)](https://codecov.io/gh/childmindresearch/hbn-ddp)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
![stability-stable](https://img.shields.io/badge/stability-stable-green.svg)
[![pages](https://img.shields.io/badge/api-docs-blue)](https://childmindresearch.github.io/hbn-ddp)

## Features
The raw HBN dataset includes final clinician diagnostic data given across ten numbered diagnosis columns. The order of these diagnoses is not indicative of severity, chronology, or importance, and this format requires data manipulation to be useful for analysis. This package transforms the data to a wider format, organized by specific diagnoses or categories rather than diagnosis numbers. It also includes the option to filter by diagnostic certainty or time of diagnosis and creates a visualization of the diagnostic data. Option to either run interactively in the command line (recommended if not familiar with the dataset) or to install as a python package.

| DX_01 | DX_01_Cat | DX_01_Sub | DX_01_Time | DX_01_Confirmed | DX_01_Presum | DX_01_RC | DX_01_RuleOut | DX_02 | DX_02_Cat | DX_02_Sub | DX_02_Time | DX_02_Confirmed | DX_02_Presum | DX_02_RC | DX_02_RuleOut | ... |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ADHD - Hyperactive Type | Neurodevelopmental Disorders | ADHD | 1 | 1 | 0 | 0 | 0 | | | | | | | | | ... |
| Selective Mutism | Anxiety Disorders | Anxiety Disorders | 1 | 1 | 0 | 0 | 0 | Autism Spectrum Disorder | Autism Spectrum Disorder | Neurodevelopmental Disorders | 1 | 0 | 0 | 0 | 1 | ... |

<p align="center">↓</p>

Neurodevelopmental_Disorders_CategoryPresent | ADHD_Hyperactive_Type_DiagnosisPresent | ADHD_Hyperactive_Type_Time | ADHD_Hyperactive_Type_Certainty | Autism_Spectrum_DiagnosisPresent | Autism_Spectrum_Time | Autism_Spectrum_Certainty | Anxiety_Disorders_CategoryPresent | Selective_Mutism_DiagnosisPresent | Selective_Mutism_Time | Selective_Mutism_Certainty |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | Current | Confirmed | 0 |  |  | 0 | 0 |  |  |
| 1 | 0 |  |  | 1 | Current | Rule-Out | 1 | 1 | Past | Confirmed |

For more information on the HBN data, please see the [HBN Data Portal](https://fcon_1000.projects.nitrc.org/indi/cmi_healthy_brain_network/index.html)


## Installation

Install this package via :

```sh
pip install git+https://github.com/childmindresearch/hbn-ddp.git
```

## Run interactively in the command line

hbnddp

## Quick start
```python
from hbnddp import HBNData

data = HBNData.create(input_path="path/to/data.csv")
processed_data = data.process(
    # change to output path if you want to save the results
    output_path="path/to/output.csv",
    # pivot on diagnoses, subcategories, categories or all
    by="diagnoses",
    # add certainty filter if desired
    certainty_filter=None,
    # set True to visualize results
    viz=True,
)
```
[Notebook Example](./examples/pivot_example.ipynb)

## Links or References
