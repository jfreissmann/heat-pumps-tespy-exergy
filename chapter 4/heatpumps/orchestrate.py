# -*- coding: utf-8 -*-

import pandas as pd
import pygmo as pg
import json
import os
from tespy.tools import OptimizationProblem

from .models.base import HeatPumpSimple
from .models.base import HeatPumpIHX
from .models.base import HeatPumpIntercooling
from .models.base import HeatPumpParallelComp
from .sensitivity_analysis import sensitivity


OptimizationProblem.sensitivity = sensitivity


model_lookup = {
    "HeatPumpSimple": HeatPumpSimple,
    "HeatPumpIHX": HeatPumpIHX,
    "HeatPumpIntercooling": HeatPumpIntercooling,
    "HeatPumpParallelComp": HeatPumpParallelComp,
}



def program_opt(scenariopath):
    basedir = get_scenario_dir(scenariopath)
    scenario_data = read_scenario_information(basedir)
    scenario_data["scenario"] = "optimization"

    optimize = create_problem(scenario_data)

    algo = pg.algorithm(pg.pso())
    pop = pg.population(pg.problem(optimize), size=scenario_data["opt"]["num_ind"])
    optimize.run(algo, pop, scenario_data["opt"]["num_ind"], scenario_data["opt"]["num_gen"])

    optimize.individuals.to_csv(
        os.path.join(basedir, 'optimization_result.csv'), sep=";"
    )


def program_sensitivity(scenariopath):
    basedir = get_scenario_dir(scenariopath)
    general_data, ts_data = read_scenario_information(basedir)
    general_data["scenario"] = "sensitivity"

    sens = create_problem(general_data, ts_data)
    results = sens.sensitivity()
    results.to_csv(
        os.path.join(basedir, 'sensitivity_result.csv'), sep=";"
    )


def get_scenario_dir(scenariopath):
    return os.path.join(os.getcwd(), scenariopath)


def read_scenario_information(basedir):
    if "scenario.json" not in os.listdir(basedir):
        raise ValueError("Missing configuration file.")

    with open(os.path.join(basedir, "scenario.json"), "r") as f:
        scenario_data = json.load(f)

    scenario_data["path"] =  basedir

    return scenario_data


def create_problem(scenario_data):

    boundary_conditions = scenario_data["opt"]['boundary_conditions']
    variables = scenario_data["opt"]['variables']
    constraints = scenario_data["opt"]['constraints']
    objective = scenario_data["opt"]['objective']

    plant = model_lookup[scenario_data["model"]](scenario_data)
    plant.set_parameters(**boundary_conditions)

    optimize = OptimizationProblem(plant, variables, constraints, objective)

    return optimize
