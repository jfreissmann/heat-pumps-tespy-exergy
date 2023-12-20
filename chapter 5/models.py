"""Super class 'HeatPumpBase' and concrete models."""
import numpy as np
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

        self.fluid_vec_wf = {self.wf: 1, self.si: 0}
        self.fluid_vec_si = {self.wf: 0, self.si: 1}

        self.comps = dict()
        self.conns = dict()
        self.busses = dict()

        self.nw = Network(
            fluids=[self.wf, self.si],
            T_unit='C', p_unit='bar', h_unit='kJ / kg',
            m_unit='kg / s', Q_unit='kW'
            )

        self.cop = np.nan
        self.epsilon = np.nan

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

    def run_model(self):
        """Run the initialization and design simulation routine."""
        self.generate_components()
        self.generate_connections()
        self.init_simulation()
        self.design_simulation()

    def perfrom_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""

    def plot_logph(self, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""

    def plot_key_params(self, savefig=False, return_fig_ax=False):
        """Generate 3 part plot of COP, exergy efficiency and Lorenz-COP."""


class HeatPumpSimple(HeatPumpBase):
    """Heat pump with basic cycle."""

    def generate_components(self):
        """Initialize components of heat pump."""
        # Main Cycle
        self.comps['gc'] = HeatExchanger('Gas cooler')
        self.comps['ev'] = HeatExchanger('Evaporator')
        self.comps['va'] = Valve('Valve')
        self.comps['cp'] = Compressor('Compressor')

        self.comps['cc'] = CycleCloser('CycleCloser')

        # Heat sink
        self.comps['si_in'] = Source('Sink in')
        self.comps['si_out'] = Sink('Sink out')

        # Heat source
        self.comps['sou_in'] = Source('Source in')
        self.comps['sou_out'] = Sink('Source out')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Main Cycle
        self.conns['c31'] = Connection(
            self.comps['cc'], 'out1', self.comps['gc'], 'in1', label="31"
            )
        self.conns['c32'] = Connection(
            self.comps['gc'], 'out1', self.comps['va'], 'in1', label="32"
            )
        self.conns['c33'] = Connection(
            self.comps['va'], 'out1', self.comps['ev'], 'in2', label="33"
            )
        self.conns['c34'] = Connection(
            self.comps['ev'], 'out2', self.comps['cp'], 'in1', label="34"
            )
        self.conns['c30'] = Connection(
            self.comps['cp'], 'out1', self.comps['cc'], 'in1', label="30"
            )

        # Heat Sink
        self.conns['c21'] = Connection(
            self.comps['si_in'], 'out1', self.comps['gc'], 'in2', label="21"
            )
        self.conns['c22'] = Connection(
            self.comps['gc'], 'out2', self.comps['si_out'], 'in1', label="22"
            )

        # Heat Source
        self.conns['c11'] = Connection(
            self.comps['sou_in'], 'out1', self.comps['ev'], 'in1', label="11"
            )
        self.conns['c12'] = Connection(
            self.comps['ev'], 'out1', self.comps['sou_out'], 'in1', label="12"
            )

        self.nw.add_conns(*[conn for conn in self.conns])

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.comps['gc'].set_attr(
            pr1=self.params['gc']['pr1'], pr2=self.params['gc']['pr2'],
            Q=self.params['gc']['Q']
            )
        self.comps['ev'].set_attr(
            pr1=self.params['ev']['pr1'], pr2=self.params['ev']['pr1']
            )
        self.comps['cp'].set_attr(eta_s=self.params['cp']['eta_s'])

        # Connections
        # Main cycle
        h_c32_start = PSI(
            'H', 'P', self.params['c32']['p']*1e5,
            'T', self.params['c32']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c32'].set_attr(h=h_c32_start, p=self.params['c32']['p'])

        self.conns['c33'].set_attr(p=self.params['c33']['p'])

        h_c34_start = PSI(
            'H', 'P', self.params['c34']['p_start']*1e5,
            'T', self.params['c34']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c34'].set_attr(h=h_c34_start, fluid=self.fluid_vec_wf)

        # Heat Sink
        self.conns['c21'].set_attr(
            T=self.params['c21']['T'], p=self.params['c21']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c22'].set_attr(T=self.params['c22']['T'])

        # Heat Source
        self.conns['c11'].set_attr(
            T=self.params['c11']['T'], p=self.params['c11']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c12'].set_attr(T=self.params['c12']['T'])

        # Busses
        self.busses['power input'] = Bus('power input')
        self.busses['power input'].add_comps(
            {'comp': self.comps['cp'], 'base': 'bus'}
            )

        self.busses['heat input'] = Bus('heat input')
        self.busses['heat input'].add_comps(
            {'comp': self.comps['sou_in'], 'base': 'bus'},
            {'comp': self.comps['sou_out'], 'base': 'component'}
            )

        self.busses['heat output'] = Bus('heat output')
        self.busses['heat output'].add_comps(
            {'comp': self.comps['si_in'], 'base': 'bus'},
            {'comp': self.comps['si_out'], 'base': 'component'}
            )

        self.nw.add_busses(
            self.busses['power input'], self.busses['heat input'],
            self.busses['heat output']
            )

        # Solve model
        self._solve_model(**kwargs)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.conns['c32'].set_attr(h=None)
        self.comps['gc'].set_attr(ttd_l=self.params['gc']['ttd_l'])

        self.conns['c33'].set_attr(p=None)
        self.comps['ev'].set_attr(ttd_l=self.params['ev']['ttd_l'])

        self.conns['c34'].set_attr(h=None, Td_bp=self.params['c34']['Td_bp'])

        # Solve model
        self._solve_model(**kwargs)

        self.cop = abs(self.comps['gc'].Q_val)/self.busses['power input'].P.val

    def perfrom_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        ean = ExergyAnalysis(
            self.nw,
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
            )
        ean.analyse(pamb=self.params['amb']['p'], Tamb=self.params['amb']['T'])
        if print_results:
            ean.print_results(**kwargs)

        self.epsilon = ean.network_data['epsilon']

        return ean

    def plot_logph(self, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""
        # Get component plotting data
        result_dict = dict()
        result_dict.update(
            {self.comps['ev'].label: self.comps['ev'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['cp'].label: self.comps['cp'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['gc'].label: self.comps['gc'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va'].label: self.comps['va'].get_plotting_data()[1]}
            )

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
                + f'{self.params["setup"]["refrig"]}.png'
                )
            diagram.save(filepath, dpi=300)

        if return_diagram:
            return diagram


class HeatPumpIHX(HeatPumpBase):
    """Heat pump with internal heat exchanger betwenn condensate and vapor."""

    def generate_components(self):
        """Initialize components of heat pump."""
        # Main Cycle
        self.comps['gc'] = HeatExchanger('Gas cooler')
        self.comps['ev'] = HeatExchanger('Evaporator')
        self.comps['va'] = Valve('Valve')
        self.comps['cp'] = Compressor('Compressor')
        self.comps['ihx'] = HeatExchanger("Internal Heat Exchanger")

        self.comps['cc'] = CycleCloser('CycleCloser')

        # Heat sink
        self.comps['si_in'] = Source('Sink in')
        self.comps['si_out'] = Sink('Sink out')

        # Heat source
        self.comps['sou_in'] = Source('Source in')
        self.comps['sou_out'] = Sink('Source out')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Main Cycle
        self.conns['c31'] = Connection(
            self.comps['cc'], 'out1', self.comps['gc'], 'in1', label="31"
            )
        self.conns['c32'] = Connection(
            self.comps['gc'], 'out1', self.comps['ihx'], 'in1', label="32"
            )
        self.conns['c33'] = Connection(
            self.comps['ihx'], 'out1', self.comps['va'], 'in1', label="33"
            )
        self.conns['c34'] = Connection(
            self.comps['va'], 'out1', self.comps['ev'], 'in2', label="34"
            )
        self.conns['c35'] = Connection(
            self.comps['ev'], 'out2', self.comps['ihx'], 'in2', label="35"
            )
        self.conns['c36'] = Connection(
            self.comps['ihx'], 'out2', self.comps['cp'], 'in1', label="36"
            )
        self.conns['c30'] = Connection(
            self.comps['cp'], 'out1', self.comps['cc'], 'in1', label="30"
            )

        # Heat Sink
        self.conns['c21'] = Connection(
            self.comps['si_in'], 'out1', self.comps['gc'], 'in2', label="21"
            )
        self.conns['c22'] = Connection(
            self.comps['gc'], 'out2', self.comps['si_out'], 'in1', label="22"
            )

        # Heat Source
        self.conns['c11'] = Connection(
            self.comps['sou_in'], 'out1', self.comps['ev'], 'in1', label="11"
            )
        self.conns['c12'] = Connection(
            self.comps['ev'], 'out1', self.comps['sou_out'], 'in1', label="12"
            )

        self.nw.add_conns(*[conn for conn in self.conns])

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.comps['gc'].set_attr(
            pr1=self.params['gc']['pr1'], pr2=self.params['gc']['pr2'],
            Q=self.params['gc']['Q']
            )
        self.comps['ev'].set_attr(
            pr1=self.params['ev']['pr1'], pr2=self.params['ev']['pr1']
            )
        self.comps['ihx'].set_attr(
            pr1=self.params['ihx']['pr1'], pr2=self.params['ihx']['pr1']
            )
        self.comps['cp'].set_attr(eta_s=self.params['cp']['eta_s'])

        # Connections
        # Main cycle
        h_c36_start = PSI(
            'H', 'P', self.params['c36']['p_start']*1e5,
            'T', self.params['c36']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c36'].set_attr(
            h=h_c36_start, p=self.params['c36']['p_start'],
            fluid=self.fluid_vec_wf
            )

        h_c32_start = PSI(
            'H', 'P', self.params['c32']['p']*1e5,
            'T', self.params['c32']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c32'].set_attr(h=h_c32_start, p=self.params['c32']['p'])

        h_c35_start = PSI(
            'H', 'P', self.params['c35']['p_start']*1e5,
            'T', self.params['c35']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c35'].set_attr(h=h_c35_start)

        # Heat Sink
        self.conns['c21'].set_attr(
            T=self.params['c21']['T'], p=self.params['c21']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c22'].set_attr(T=self.params['c22']['T'])

        # Heat Source
        self.conns['c11'].set_attr(
            T=self.params['c11']['T'], p=self.params['c11']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c12'].set_attr(T=self.params['c12']['T'])

        # Busses
        self.busses['power input'] = Bus('power input')
        self.busses['power input'].add_comps(
            {'comp': self.comps['cp'], 'base': 'bus'}
            )

        self.busses['heat input'] = Bus('heat input')
        self.busses['heat input'].add_comps(
            {'comp': self.comps['sou_in'], 'base': 'bus'},
            {'comp': self.comps['sou_out'], 'base': 'component'}
            )

        self.busses['heat output'] = Bus('heat output')
        self.busses['heat output'].add_comps(
            {'comp': self.comps['si_in'], 'base': 'bus'},
            {'comp': self.comps['si_out'], 'base': 'component'}
            )

        self.nw.add_busses(
            self.busses['power input'], self.busses['heat input'],
            self.busses['heat output']
            )

        # Solve model
        self._solve_model(**kwargs)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.conns['c36'].set_attr(h=None, p=None)
        self.comps['ev'].set_attr(ttd_l=self.params['ev']['ttd_l'])

        self.comps['ihx'].set_attr(ttd_u=self.params['ihx']['ttd_u'])

        self.conns['c32'].set_attr(h=None)
        self.comps['gc'].set_attr(ttd_l=self.params['gc']['ttd_l'])

        self.conns['c35'].set_attr(h=None, Td_bp=self.params['c35']['Td_bp'])

        # Solve model
        self._solve_model(**kwargs)

        self.cop = abs(self.comps['gc'].Q_val)/self.busses['power input'].P.val

    def perfrom_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        ean = ExergyAnalysis(
            self.nw,
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
            )
        ean.analyse(pamb=self.params['amb']['p'], Tamb=self.params['amb']['T'])
        if print_results:
            ean.print_results(**kwargs)

        self.epsilon = ean.network_data['epsilon']

        return ean

    def plot_logph(self, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""
        # Get component plotting data
        result_dict = dict()
        ihx_label = self.comps['ihx'].label
        result_dict.update(
            {self.comps['ev'].label: self.comps['ev'].get_plotting_data()[2]}
            )
        result_dict.update(
            {f'{ihx_label} (cold)': self.comps['ihx'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['cp'].label: self.comps['cp'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['gc'].label: self.comps['gc'].get_plotting_data()[1]}
            )
        result_dict.update(
            {f'{ihx_label} (hot)': self.comps['ihx'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va'].label: self.comps['va'].get_plotting_data()[1]}
            )

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
                + f'{self.params["setup"]["refrig"]}.png'
                )
            diagram.save(filepath, dpi=300)

        if return_diagram:
            return diagram


class HeatPumpParallelComp(HeatPumpBase):
    """Heat pump with a complex parallel compression"""

    def generate_components(self):
        """Initialize components of heat pump."""
        # Main Cycle
        self.comps['gc'] = HeatExchanger('Gas cooler')
        self.comps['ev'] = HeatExchanger('Evaporator')
        self.comps['va_1'] = Valve('Valve 1')
        self.comps['va_2'] = Valve('Valve 2')
        self.comps['cp_1'] = Compressor('Compressor 1')
        self.comps['cp_2'] = Compressor('Compressor 2')
        self.comps['ihx_1'] = HeatExchanger('Internal Heat Exchanger 1')
        self.comps['ihx_2'] = HeatExchanger('Internal Heat Exchanger 2')

        self.comps['fl'] = DropletSeparator('Flash Tank')
        self.comps['mg'] = Merge('Merge')

        self.comps['cc'] = CycleCloser('CycleCloser')

        # Heat sink
        self.comps['si_in'] = Source('Sink in')
        self.comps['si_out'] = Sink('Sink out')

        # Heat source
        self.comps['sou_in'] = Source('Source in')
        self.comps['sou_out'] = Sink('Source out')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Main Cycle
        self.conns['c31'] = Connection(
            self.comps['cc'], 'out1', self.comps['gc'], 'in1', label="31"
            )
        self.conns['c32'] = Connection(
            self.comps['gc'], 'out1', self.comps['ihx_2'], 'in1', label="32"
            )
        self.conns['c33'] = Connection(
            self.comps['ihx_2'], 'out1', self.comps['va_1'], 'in2', label="33"
            )
        self.conns['c34'] = Connection(
            self.comps['va_1'], 'out2', self.comps['fl'], 'in1', label="34"
            )
        self.conns['c35'] = Connection(
            self.comps['fl'], 'out1', self.comps['ihx_1'], 'in1', label="35"
            )
        self.conns['c36'] = Connection(
            self.comps['ihx_1'], 'out1', self.comps['va_2'], 'in1', label="36"
            )
        self.conns['c37'] = Connection(
            self.comps['va_2'], 'out1', self.comps['ev'], 'in2', label="37"
            )
        self.conns['c38'] = Connection(
            self.comps['ev'], 'out2', self.comps['ihx_1'], 'in2', label="38"
            )
        self.conns['c39'] = Connection(
            self.comps['ihx_1'], 'out2', self.comps['cp_1'], 'in1', label="39"
            )
        self.conns['c40'] = Connection(
            self.comps['cp_1'], 'out1', self.comps['mg'], 'in1', label="40"
            )
        self.conns['c41'] = Connection(
            self.comps['fl'], 'out2', self.comps['ihx_2'], 'in2', label="41"
            )
        self.conns['c42'] = Connection(
            self.comps['ihx_2'], 'out2', self.comps['cp_2'], 'in1', label="42"
            )
        self.conns['c43'] = Connection(
            self.comps['cp_2'], 'out1', self.comps['mg'], 'in2', label="43"
            )
        self.conns['c30'] = Connection(
            self.comps['mg'], 'out1', self.comps['cc'], 'in1', label="30"
            )

        # Heat Sink
        self.conns['c21'] = Connection(
            self.comps['si_in'], 'out1', self.comps['gc'], 'in2', label="21"
            )
        self.conns['c22'] = Connection(
            self.comps['gc'], 'out2', self.comps['si_out'], 'in1', label="22"
            )

        # Heat Source
        self.conns['c11'] = Connection(
            self.comps['sou_in'], 'out1', self.comps['ev'], 'in1', label="11"
            )
        self.conns['c12'] = Connection(
            self.comps['ev'], 'out1', self.comps['sou_out'], 'in1', label="12"
            )

        self.nw.add_conns(*[conn for conn in self.conns])

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.comps['ev'].set_attr(
            pr1=self.params['ev']['pr1'], pr2=self.params['ev']['pr2']
            )
        self.comps['gc'].set_attr(
            pr1=self.params['gc']['pr1'], pr2=self.params['gc']['pr2'],
            Q=self.params['gc']['Q']
            )
        self.comps['ihx_1'].set_attr(
            pr1=self.params['ihx_1']['pr1'], pr2=self.params['ihx_1']['pr2']
            )
        self.comps['ihx_2'].set_attr(
            pr1=self.params['ihx_2']['pr1'], pr2=self.params['ihx_2']['pr2']
            )
        self.comps['cp_1'].set_attr(eta_s=self.params['cp_1']['eta_s'])
        self.comps['cp_2'].set_attr(eta_s=self.params['cp_2']['eta_s'])

        # Connections
        # Main cycle
        h_c32_start = PSI(
            'H', 'P', self.params['c32']['p']*1e5,
            'T', self.params['c32']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c32'].set_attr(h=h_c32_start, p=self.params['c32']['p'])

        self.conns['c34'].set_attr(
            p=self.params['c34']['p'], fluid=self.fluid_vec_wf
            )

        self.conns['c37'].set_attr(p=self.params['c37']['p'])

        h_c38_start = PSI(
            'H', 'P', self.params['c38']['p_start']*1e5,
            'T', self.params['c38']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c38'].set_attr(h=h_c38_start)

        h_c39_start = PSI(
            'H', 'P', self.params['c39']['p_start']*1e5,
            'T', self.params['c39']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c39'].set_attr(h=h_c39_start)

        h_c42_start = PSI(
            'H', 'P', self.params['c42']['p_start']*1e5,
            'T', self.params['c42']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c42'].set_attr(h=h_c42_start)

        # Heat Sink
        self.conns['c21'].set_attr(
            T=self.params['c21']['T'], p=self.params['c21']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c22'].set_attr(T=self.params['c22']['T'])

        # Heat Source
        self.conns['c11'].set_attr(
            T=self.params['c11']['T'], p=self.params['c11']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c12'].set_attr(T=self.params['c12']['T'])

        # Busses
        self.busses['power input'] = Bus('power input')
        self.busses['power input'].add_comps(
            {'comp': self.comps['cp_1'], 'base': 'bus'},
            {'comp': self.comps['cp_2'], 'base': 'bus'}
            )

        self.busses['heat input'] = Bus('heat input')
        self.busses['heat input'].add_comps(
            {'comp': self.comps['sou_in'], 'base': 'bus'},
            {'comp': self.comps['sou_out'], 'base': 'component'}
            )

        self.busses['heat output'] = Bus('heat output')
        self.busses['heat output'].add_comps(
            {'comp': self.comps['si_in'], 'base': 'bus'},
            {'comp': self.comps['si_out'], 'base': 'component'}
            )

        self.nw.add_busses(
            self.busses['power input'], self.busses['heat input'],
            self.busses['heat output']
            )

        # Solve model
        self._solve_model(**kwargs)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.conns['c37'].set_attr(p=None)
        self.conns['c38'].set_attr(h=None, Td_bp=self.params['c38']['Td_bp'])
        self.comps['ev'].set_attr(ttd_l=self.params['ev']['ttd_l'])

        self.conns['c39'].set_attr(h=None)
        self.comps['ihx_1'].set_attr(ttd_u=self.params['ihx_1']['ttd_u'])
        self.conns['c42'].set_attr(h=None)
        self.comps['ihx_2'].set_attr(ttd_u=self.params['ihx_2']['ttd_u'])

        self.conns['c32'].set_attr(h=None)
        self.comps['gc'].set_attr(ttd_l=self.params['gc']['ttd_l'])

        self.conns['c35'].set_attr(h=None, Td_bp=self.params['c35']['Td_bp'])

        # Solve model
        self._solve_model(**kwargs)

        self.cop = abs(self.comps['gc'].Q_val)/self.busses['power input'].P.val

    def perfrom_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        ean = ExergyAnalysis(
            self.nw,
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
            )
        ean.analyse(pamb=self.params['amb']['p'], Tamb=self.params['amb']['T'])
        if print_results:
            ean.print_results(**kwargs)

        self.epsilon = ean.network_data['epsilon']

        return ean

    def plot_logph(self, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""
        # Get component plotting data
        result_dict = dict()
        ihx_1_label = self.comps['ihx_1'].label
        ihx_2_label = self.comps['ihx_2'].label
        result_dict.update(
            {self.comps['ev'].label: self.comps['ev'].get_plotting_data()[2]}
            )
        result_dict.update(
            {f'{ihx_1_label} (cold)': self.comps['ihx_1'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['cp_1'].label: self.comps['cp_1'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['mg'].label + ' 1': self.comps['mg'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['gc'].label: self.comps['gc'].get_plotting_data()[1]}
            )
        result_dict.update(
            {f'{ihx_2_label} (hot)': self.comps['ihx_2'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va_2'].label: self.comps['va_2'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['fl'].label + ' 2': self.comps['fl'].get_plotting_data()[2]}
            )
        result_dict.update(
            {f'{ihx_2_label} (cold)': self.comps['ihx_2'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['cp_2'].label: self.comps['cp_2'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['mg'].label + ' 2': self.comps['mg'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['fl'].label + ' 1': self.comps['fl'].get_plotting_data()[1]}
            )
        result_dict.update(
            {f'{ihx_1_label} (hot)': self.comps['ihx_1'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va_1'].label: self.comps['va_1'].get_plotting_data()[1]}
            )

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
                + f'{self.params["setup"]["refrig"]}.png'
                )
            diagram.save(filepath, dpi=300)

        if return_diagram:
            return diagram


class HeatPumpIntercooling(HeatPumpBase):
    """Heat pump with compression intercooling and internal heat exchanger."""

    def generate_components(self):
        """Initialize components of heat pump."""
        # Main Cycle
        self.comps['gc'] = HeatExchanger('Gas cooler')
        self.comps['ev'] = HeatExchanger('Evaporator')
        self.comps['va_1'] = Valve('Valve 1')
        self.comps['va_2'] = Valve('Valve 2')
        self.comps['cp_1'] = Compressor('Compressor 1')
        self.comps['cp_2'] = Compressor('Compressor 2')
        self.comps['ihx'] = HeatExchanger('Internal Heat Exchanger')

        self.comps['fl'] = DropletSeparator('Flash Tank')
        self.comps['mg'] = Merge('Merge')

        self.comps['cc'] = CycleCloser('CycleCloser')

        # Heat sink
        self.comps['si_in'] = Source('Sink in')
        self.comps['si_out'] = Sink('Sink out')

        # Heat source
        self.comps['sou_in'] = Source('Source in')
        self.comps['sou_out'] = Sink('Source out')

    def generate_connections(self):
        """Initialize and add connections and busses to network."""
        # Main Cycle
        self.conns['c31'] = Connection(
            self.comps['cc'], 'out1', self.comps['gc'], 'in1', label="31"
            )
        self.conns['c32'] = Connection(
            self.comps['gc'], 'out1', self.comps['ihx'], 'in1', label="32"
            )
        self.conns['c33'] = Connection(
            self.comps['ihx'], 'out1', self.comps['va_1'], 'in1', label="33"
            )
        self.conns['c34'] = Connection(
            self.comps['va_1'], 'out1', self.comps['fl'], 'in1', label="34"
            )
        self.conns['c35'] = Connection(
            self.comps['fl'], 'out1', self.comps['va_2'], 'in1', label="35"
            )
        self.conns['c36'] = Connection(
            self.comps['va_2'], 'out1', self.comps['ev'], 'in2', label="36"
            )
        self.conns['c37'] = Connection(
            self.comps['ev'], 'out2', self.comps['ihx'], 'in2', label="37"
            )
        self.conns['c38'] = Connection(
            self.comps['ihx'], 'out2', self.comps['cp_1'], 'in1', label="38"
            )
        self.conns['c39'] = Connection(
            self.comps['cp_1'], 'out1', self.comps['mg'], 'in1', label="39"
            )
        self.conns['c40'] = Connection(
            self.comps['mg'], 'out1', self.comps['cp_2'], 'in1', label="40"
            )
        self.conns['c41'] = Connection(
            self.comps['fl'], 'out2', self.comps['mg'], 'in2', label="41"
            )
        self.conns['c30'] = Connection(
            self.comps['cp_2'], 'out1', self.comps['cc'], 'in1', label="30"
            )

        # Heat Sink
        self.conns['c21'] = Connection(
            self.comps['si_in'], 'out1', self.comps['gc'], 'in2', label="21"
            )
        self.conns['c22'] = Connection(
            self.comps['gc'], 'out2', self.comps['si_out'], 'in1', label="22"
            )

        # Heat Source
        self.conns['c11'] = Connection(
            self.comps['sou_in'], 'out1', self.comps['ev'], 'in1', label="11"
            )
        self.conns['c12'] = Connection(
            self.comps['ev'], 'out1', self.comps['sou_out'], 'in1', label="12"
            )

        self.nw.add_conns(*[conn for conn in self.conns])

    def init_simulation(self, **kwargs):
        """Perform initial parametrization with starting values."""
        # Components
        self.comps['ev'].set_attr(
            pr1=self.params['ev']['pr1'], pr2=self.params['ev']['pr2']
            )
        self.comps['gc'].set_attr(
            pr1=self.params['gc']['pr1'], pr2=self.params['gc']['pr2'],
            Q=self.params['gc']['Q']
            )
        self.comps['ihx'].set_attr(
            pr1=self.params['ihx']['pr1'], pr2=self.params['ihx']['pr2']
            )
        self.comps['cp_1'].set_attr(eta_s=self.params['cp_1']['eta_s'])
        self.comps['cp_2'].set_attr(eta_s=self.params['cp_2']['eta_s'])

        # Connections
        # Main cycle
        h_c38_start = PSI(
            'H', 'P', self.params['c38']['p']*1e5,
            'T', self.params['c38']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c38'].set_attr(
            h=h_c38_start, p=self.params['c38']['p'], fluid=self.fluid_vec_wf
            )

        self.conns['c39'].set_attr(p=self.params['c39']['p'])

        h_c32_start = PSI(
            'H', 'P', self.params['c32']['p']*1e5,
            'T', self.params['c32']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c32'].set_attr(
            h=h_c32_start, p=self.params['c32']['p']
            )

        h_c37_start = PSI(
            'H', 'P', self.params['c37']['p_start']*1e5,
            'T', self.params['c37']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c37'].set_attr(h=h_c37_start)

        # Heat Sink
        self.conns['c21'].set_attr(
            T=self.params['c21']['T'], p=self.params['c21']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c22'].set_attr(T=self.params['c22']['T'])

        # Heat Source
        self.conns['c11'].set_attr(
            T=self.params['c11']['T'], p=self.params['c11']['p'],
            fluid=self.fluid_vec_si
            )
        self.conns['c12'].set_attr(T=self.params['c12']['T'])

        # Busses
        self.busses['power input'] = Bus('power input')
        self.busses['power input'].add_comps(
            {'comp': self.comps['cp_1'], 'base': 'bus'},
            {'comp': self.comps['cp_2'], 'base': 'bus'}
            )

        self.busses['heat input'] = Bus('heat input')
        self.busses['heat input'].add_comps(
            {'comp': self.comps['sou_in'], 'base': 'bus'},
            {'comp': self.comps['sou_out'], 'base': 'component'}
            )

        self.busses['heat output'] = Bus('heat output')
        self.busses['heat output'].add_comps(
            {'comp': self.comps['si_in'], 'base': 'bus'},
            {'comp': self.comps['si_out'], 'base': 'component'}
            )

        self.nw.add_busses(
            self.busses['power input'], self.busses['heat input'],
            self.busses['heat output']
            )

        # Solve model
        self._solve_model(**kwargs)

    def design_simulation(self, **kwargs):
        """Perform final parametrization and design simulation."""
        self.conns['c38'].set_attr(h=None, p=None)
        self.comps['ihx'].set_attr(ttd_u=self.params['ihx']['ttd_u'])
    
        self.conns['c37'].set_attr(p=None, Td_bp=self.params['c37']['Td_bp'])
        self.comps['ev'].set_attr(ttd_l=self.params['ev']['ttd_l'])

        self.conns['c32'].set_attr(h=None)
        self.comps['gc'].set_attr(ttd_l=self.params['gc']['ttd_l'])

        # Solve model
        self._solve_model(**kwargs)

        self.cop = abs(self.comps['gc'].Q_val)/self.busses['power input'].P.val

    def perfrom_exergy_analysis(self, print_results=False, **kwargs):
        """Perform exergy analysis."""
        ean = ExergyAnalysis(
            self.nw,
            E_F=[self.busses['power input'], self.busses['heat input']],
            E_P=[self.busses['heat output']]
            )
        ean.analyse(pamb=self.params['amb']['p'], Tamb=self.params['amb']['T'])
        if print_results:
            ean.print_results(**kwargs)

        self.epsilon = ean.network_data['epsilon']

        return ean

    def plot_logph(self, savefig=False, return_diagram=False):
        """Generate log(p)-h-diagram of heat pump process."""
        # Get component plotting data
        result_dict = dict()
        ihx_label = self.comps['ihx'].label
        result_dict.update(
            {self.comps['ev'].label: self.comps['ev'].get_plotting_data()[2]}
            )
        result_dict.update(
            {f'{ihx_label} (cold)': self.comps['ihx'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['cp_1'].label: self.comps['cp_1'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['fl'].label + ' 2': self.comps['fl'].get_plotting_data()[2]}
            )
        result_dict.update(
            {self.comps['mg'].label + ' 1': self.comps['mg'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['cp_2'].label: self.comps['cp_2'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['gc'].label: self.comps['gc'].get_plotting_data()[1]}
            )
        result_dict.update(
            {f'{ihx_label} (hot)': self.comps['ihx'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va_1'].label: self.comps['va_1'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['fl'].label + ' 1': self.comps['fl'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['va_2'].label: self.comps['va_2'].get_plotting_data()[1]}
            )
        result_dict.update(
            {self.comps['mg'].label + ' 2': self.comps['mg'].get_plotting_data()[2]}
            )

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
                + f'{self.params["setup"]["refrig"]}.png'
                )
            diagram.save(filepath, dpi=300)

        if return_diagram:
            return diagram
