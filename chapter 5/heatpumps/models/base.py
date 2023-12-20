"""Super class 'HeatPumpBase' and concrete models."""
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from tespy.components import (Compressor, CycleCloser, DropletSeparator,
                              HeatExchanger, Merge, Sink, Source, Valve)
from tespy.connections import Bus, Connection
from tespy.networks import Network
from tespy.tools import ExergyAnalysis


class HeatPumpBase:
    """Base class of all concrete heat pump models."""

    def __init__(self, params):
        """Initialize model and set necessary attributes."""
        self.params = params

        self.wf = self.params['fluids']['wf']
        self.si = self.params['fluids']['si']

        self.fluid_vec_wf = {self.wf.split('::')[-1]: 1, self.si: 0}
        self.fluid_vec_si = {self.wf.split('::')[-1]: 0, self.si: 1}

        self.comps = dict()
        self.conns = dict()
        self.busses = dict()

        self.nw = Network(
            fluids=[self.wf, self.si],
            T_unit='C', p_unit='bar', h_unit='kJ / kg',
            m_unit='kg / s'
            )

        self.cop = np.nan
        self.epsilon = np.nan

        self.stable_solution_path = os.path.join(
            __file__, '..',
            f"{self.params['setup']['type']}_"
            + f"{self.params['setup']['refrig']}_init"
            )

    def generate_components(self):
        """Initialize components of heat pump."""

    def generate_connections(self):
        """Initialize and add connections and busses to network."""

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""

    def _solve_model(self, **kwargs):
        """Solve the model in design mode."""
        if 'iterinfo' in kwargs:
            self.nw.set_attr(iterinfo=kwargs['iterinfo'])
        self.nw.solve('design')
        if 'print_results' in kwargs:
            if kwargs['print_results']:
                self.nw.print_results()
        if self.nw.res[-1] < 1e-3:
            self.nw.save(self.stable_solution_path)

    def run_model(self):
        """Run the initialization and design simulation routine."""
        self.generate_components()
        self.generate_connections()
        self.init_simulation()
        self.design_simulation()

    def perform_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        self.ean = ExergyAnalysis(
            self.nw,
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
            )
        self.ean.analyse(
            pamb=self.params['ambient']['p'], Tamb=self.params['ambient']['T']
            )
        if print_results:
            self.ean.print_results(**kwargs)

        self.epsilon = self.ean.network_data['epsilon']

    def get_log_ph_states(self):
        """Generate log(p)-h-diagram of heat pump process."""

    def plot_logph(self, result_dict, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""
        result_dict = self.get_log_ph_states()

        # Initialize fluid property diagram
        diagram = FluidPropertyDiagram(self.params['setup']['refrig'])
        diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')
        diagram.set_limits(
            x_min=self.params['logph']['x_min'],
            x_max=self.params['logph']['x_max'],
            y_min=self.params['logph']['y_min'],
            y_max=self.params['logph']['y_max']
            )

        # Calculate components process data
        for compdata in result_dict.values():
            compdata['datapoints'] = (
                diagram.calc_individual_isoline(**compdata)
                )
        # breakpoint()

        # Isolines
        diagram.calc_isolines()
        diagram.draw_isolines('logph')

        # Draw heat pump process over fluid property diagram
        for compdata in result_dict.values():
            datapoints = compdata['datapoints']
            diagram.ax.plot(datapoints['h'], datapoints['p'], color='#EC6707')
            diagram.ax.scatter(
                datapoints['h'][0], datapoints['p'][0], color='#B54036'
                )

        if savefig:
            filepath = (
                f'logph_{self.params["setup"]["type"]}_'
                + f'{self.params["setup"]["refrig"]}.pdf'
                )
            diagram.save(filepath, dpi=300)

        if return_diagram:
            return diagram

    def run_p_high_analysis(self, p_min, p_max, stepwidth=1):
        """Variate high pressure and calculate COP and epsilon."""
        skip_comps = [
            'Source in', 'Source out', 'Sink in', 'Sink out', 'CycleCloser'
            ]
        p_high_range = [*range(p_min, p_max, stepwidth)]
        results = pd.DataFrame(index=p_high_range, columns=['COP', 'epsilon'])
        E_Ds = pd.DataFrame(index=p_high_range)

        for p_high in p_high_range:
            print('\n##########################################')
            print(
                f'{self.params["setup"]["type"]} '
                + f'{self.params["setup"]["refrig"]}'
                + f' @ {p_high} bar.'
                )
            print('##########################################\n')
            self.conns['c32'].set_attr(p=p_high)


            # if self.params['setup']['type'] == 'HeatPumpIntercooling':
            #     p_mid = np.sqrt(self.nw.get_conn('36').p.val * p_high)
            #     self.conns['c39'].set_attr(p=p_mid)
            #     print(f'\n\n########## p_mid: {p_mid} bar ##########\n\n')
            # elif self.params['setup']['type'] == 'HeatPumpParallelComp':
            #     p_mid = np.sqrt(self.nw.get_conn('37').p.val * p_high)
            #     self.conns['c34'].set_attr(p=p_mid)

            try:
                self.nw.solve('design', init_path=self.stable_solution_path)
                if self.nw.res[-1] < 1e-3:
                    self.nw.save(self.stable_solution_path)
                self.perform_exergy_analysis()
                results.loc[p_high, 'COP'] = (
                    abs(self.comps['gc'].Q.val)/self.busses['power input'].P.val
                    )
                cop_false = (
                    results.loc[p_high, 'COP'] > 10
                    or results.loc[p_high, 'COP'] < 1
                    )
                if cop_false:
                    results.loc[p_high, 'COP'] = np.nan

                results.loc[p_high, 'epsilon'] = (
                    self.ean.network_data['epsilon']
                    )
                epsilon_false = (
                    results.loc[p_high, 'epsilon'] >= 1
                    or results.loc[p_high, 'epsilon'] < 0
                )
                if epsilon_false:
                    results.loc[p_high, 'epsilon'] = np.nan
                else:
                    for comp in self.comps.values():
                        if comp.label in skip_comps:
                            continue

                        E_Ds.loc[p_high, comp.label] = (
                            self.ean.aggregation_data.loc[comp.label, 'y_Dk']
                        )
                    E_Ds.loc[p_high, 'E_D_tot'] = (
                        self.ean.network_data['E_D'] * 1e-6
                        )
            except Exception as error:
                print(
                    f'Simulation failed with high pressure of {p_high} bar with'
                    + f' the following excpetion:\n\n"{error}"'
                    )

        return results, E_Ds

    def plot_p_high_analysis(self, p_min, p_max, stepwidth=1, savefig=False):
        """Generate two part plot of COP and exergy efficiency."""
        res, E_Ds = self.run_p_high_analysis(p_min, p_max, stepwidth)

        # hpihx_r600 = (
        #     (self.params['setup']['type'] == 'HeatPumpIHX')
        #     and (self.params['setup']['refrig'] == 'R600')
        #     )
        # if hpihx_r600:
        #     E_Ds.to_csv('y_Dk_R600_HPIHX.csv', sep=';')

        fig, axs = plt.subplots(2, 1, sharex=True, figsize=(10, 6))

        axs[0].plot(res.index, res['COP'], marker='o', color='#EC6707')
        axs[1].plot(res.index, res['epsilon'], marker='o', color='#B54036')

        axs[0].set_ylabel('Coefficient of Performance $COP$')
        axs[1].set_ylabel('Exergy efficiency $\\epsilon$')
        axs[1].set_xlabel('High pressure in $bar$')

        axs[0].grid()
        axs[1].grid()

        # fig.suptitle(
        #     f'{self.params["setup"]["type"]} {self.params["setup"]["refrig"]}'
        #     )

        if savefig:
            if not os.path.exists('p_high_analysis'):
                os.mkdir('p_high_analysis')
            filepath = (
                f'{self.params["setup"]["type"]}_'
                + f'{self.params["setup"]["refrig"]}_COP_epsilon.pdf'
                )
            plt.savefig(os.path.join('p_high_analysis', filepath))
        else:
            plt.show()

        try:
            colors = {
                'darkblue': '#00395B',
                'red': '#B54036',
                'lightblue': '#74ADC0',
                'orange': '#EC6707',
                'grey': '#BFBFBF',
                'dimgrey': 'dimgrey',
                'lightgrey': 'lightgrey',
                'slategrey': 'slategrey',
                'darkgrey': '#A9A9A9'
            }
            fig, ax = plt.subplots(figsize=(10, 6))

            bottom = np.zeros(len(E_Ds.index))
            for comp, c in zip(E_Ds.columns, colors.values()):
                if comp == 'E_D_tot':
                    continue
                ax.bar(
                    E_Ds.index, E_Ds[comp], width=stepwidth/2, bottom=bottom,
                    label=comp, color=c
                    )
                bottom += E_Ds[comp]
            ax.set_ylabel(r'Exergy destruction ratio by component $y_{D,k}$')
            ax.set_xlabel('High pressure in $bar$')
            ax.set_ylim((0, 0.42))
            ax.grid(axis='y')
            ax.set_axisbelow(True)
            ax.legend(prop={'size': 8})

            # ax2 = ax.twinx()

            # ax2.bar(E_Ds.index, E_Ds['E_D_tot'], width=stepwidth/8, color='k', alpha=0.3)
            # ax2.set_ylabel(
            #     r'Total network exergy destruction rate $\dot{E}_D$ in $MW$'
            #     )
            # ax2.set_ylim((0, E_Ds['E_D_tot'].max()*1.2))
            # ax2.set_ylim((0, 1.2))
            # fig.suptitle(
            #     f'{self.params["setup"]["type"]} {self.params["setup"]["refrig"]}'
            #     )

            if savefig:
                filepath = (
                    f'{self.params["setup"]["type"]}_'
                    + f'{self.params["setup"]["refrig"]}_ystar_dk.pdf'
                    )
                plt.savefig(os.path.join('p_high_analysis', filepath))
            else:
                plt.show()
        except Exception as e:
            print(e)
