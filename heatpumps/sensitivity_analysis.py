import numpy as np
import pandas as pd


def sensitivity(self):
    """Run sensistivity analysis."""
    self.input_dict = dict()

    for var in self.variable_list:
        obj, label, param = var.split('-')
        if obj not in self.input_dict:
            self.input_dict[obj] = dict()
        if label not in self.input_dict[obj]:
            self.input_dict[obj][label] = dict()
        self.input_dict[obj][label].update(
            {param: self.model.param["opt"]["boundary_conditions"][obj][label][param]}
        )

    basecase_result = insert_results(self, f"BASECASE")
    results = pd.DataFrame(
        index=pd.MultiIndex(
            levels=[[], []],
            codes=[[], []],
            names=["gen", "ind"]
        ),
        columns=basecase_result.index
    )

    results.loc[(0, 0), :] = basecase_result.values

    gen = 1
    for obj, data in self.variables.items():
        for label, params in data.items():
            for param in params:
                steps = self.variables[obj][label][param]['steps']
                if steps == 0:
                    continue
                elif steps == 1:
                    raise ValueError("Specify the variable as boundary condition value.")
                else:
                    param_range = np.linspace(
                        self.variables[obj][label][param]['min'],
                        self.variables[obj][label][param]['max'],
                        steps
                    )
                ind = 0
                for param_val in param_range:
                    self.input_dict[obj][label].update(
                        {param: param_val}
                    )

                    results.loc[(gen, ind), :] = insert_results(self, f"{obj}-{label}-{param}").values
                    ind += 1

                self.input_dict[obj][label].update(
                    {param: self.model.param["opt"]["boundary_conditions"][obj][label][param]}
                )
                gen += 1

    return results


def insert_results(self, variable_name):
    result_row = pd.Series(dtype="object")
    result_row["Decision_Variable"] = variable_name
    for var in self.variable_list:
        o, l, p = var.split('-')
        result_row[var] = self.input_dict[o][l][p]

    self.model.solve_model(
        return_results=True, **self.input_dict
    )

    result_row[self.objective] = self.model.get_objective(self.objective)

    return result_row
