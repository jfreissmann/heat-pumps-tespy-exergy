"""Super class 'HeatPumpBase' and concrete models."""
import numpy as np
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from tespy.components import (Compressor, CycleCloser, DropletSeparator,
                              HeatExchanger, Merge, Sink, Source, Valve)
from tespy.connections import Bus, Connection
from tespy.networks import Network
from tespy.tools import ExergyAnalysis

from .base import HeatPumpBase


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

        self.nw.add_conns(*[conn for conn in self.conns.values()])

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
            'H', 'P', self.params['c36']['p']*1e5,
            'T', self.params['c36']['T_start']+273.15, self.wf
            ) * 1e-3
        self.conns['c36'].set_attr(
            h=h_c36_start, p=self.params['c36']['p'],
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

        self.cop = abs(self.comps['gc'].Q.val)/self.busses['power input'].P.val

    def get_log_ph_states(self):
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
        return result_dict