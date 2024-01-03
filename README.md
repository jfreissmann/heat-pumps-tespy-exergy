[![DOI](https://zenodo.org/badge/633761164.svg)](https://zenodo.org/doi/10.5281/zenodo.10453873)

# Introduction

This package servers as a repository for the code used to generate the results of the paper "Exergy-based methods for heat pumps" by the authors. It aims to retain the models used and their respective input parametrization, as well as allow for the reproduction of the results by third parties.

# Methodology

The heat pumps are modelled using the free and open-source software [Thermal Engineering Systems in Python (TESPy)](https://github.com/oemof/tespy). The software is developed as part of the [open energy modeling framework (oemof)](https://github.com/oemof) in the scientific field and by industrial users. TESPy accesses the likewise open-source fluid properties database [CoolProp](https://github.com/CoolProp/CoolProp).

# Contents

The repository contains the simple heat pump model displayed in chapter 4 of the paper, as well as all four models compared in chapter 5. The former is a small and straightforward model and therefore is parametrized directly in the code. Since the models of the comparative analyses are more complex and employ four different refrigerants, each model has a corresponding input directory with an input file for each refrigerant. The same general structure is also used for the output of the models, with a folder for the each type of result data.

# Reproduction

To achieve reproducible results, the necessary dependencies are saved in the `requirements.txt` file. In a clean environment from the root directory the installation from this file should allow the full reproduction of the results. This steps could look like this:

```
conda create -n my_new_env python=3.11
```

```
conda activate my_new_env
```

```
python -m pip install -r requirements.txt
```
