# Introduction

This package servers as a repository for the code used to generate the results of the paper "Exergy-based methods for heat pumps" by the authors. It aims to retain the models used and their respective input parametrization, as well as allow for the reproduction of the results by third parties.

# Methodology

The heat pumps are modelled using the free and open-source software [Thermal Engineering Systems in Python (TESPy)](https://github.com/oemof/tespy). The software is developed as part of the [open energy modeling framework (oemof)](https://github.com/oemof) in the scientific field and by industrial users. TESPy accesses the likewise open-source fluid properties database [CoolProp](https://github.com/CoolProp/CoolProp).

# Contents

The repository contains the simple heat pump model displayed in chapter 3 of the paper, as well as all four models compared in chapter 4. The former is a small and straightforward model and therefore is parametrized directly in the code. Since the models of the comparative analyses are more complex and employ four different refrigerants, each model has a corresponding input directory with an input file for each refrigerant. The same general structure is also used for the output of the models, with an additional folder for the raw result data.

# Reproduction

To achieve reproducible results, the necessary dependencies are saved in the `requirements.txt` file. In a clean environment from the root directory the installation from this file should allow the full reproduction of the results.

```
python -m pip install -r requirements.txt
```