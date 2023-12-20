import os

import plotly.graph_objects as go
from CoolProp.CoolProp import PropsSI as PSI
from fluprodia import FluidPropertyDiagram
from tespy.components import (Compressor, CycleCloser, HeatExchanger,
                              HeatExchangerSimple, Sink, Source, Valve)
from tespy.connections import Bus, Connection
from tespy.networks import Network
from tespy.tools import ExergyAnalysis

# fluid names
wf = 'R407c'
hf = 'water'
gh = 'air'
fld_wf = {wf: 1, hf: 0, gh: 0}
fld_hf = {wf: 0, hf: 1, gh: 0}
fld_gh = {wf: 0, hf: 0, gh: 1}

# network
heatpump = Network(
    fluids=[wf, hf, gh],
    T_unit='C', p_unit='bar', h_unit='kJ / kg', m_unit='kg / s'
    )

# components
cmp_th = Valve('throttle')
cmp_ev = HeatExchanger('evaporator')
cmp_cp = Compressor('compressor')
cmp_co = HeatExchanger('condenser')
cmp_cc = CycleCloser('cycle-closer')

src_gh = Source('ground-heat-fluid-source')
snk_gh = Sink('ground-heat-fluid-sink')

src_hf = Source('heating-fluid-source')
snk_hf = Sink('heating-fluid-sink')

# connections
c03 = Connection(cmp_cc, 'out1', cmp_th, 'in1', label='03')
c04 = Connection(cmp_th, 'out1', cmp_ev, 'in2', label='04')
c01 = Connection(cmp_ev, 'out2', cmp_cp, 'in1', label='01')
c02 = Connection(cmp_cp, 'out1', cmp_co, 'in1', label='02')
c02cc = Connection(cmp_co, 'out1', cmp_cc, 'in1', label='02cc')

c11 = Connection(src_gh, 'out1', cmp_ev, 'in1', label='11')
c12 = Connection(cmp_ev, 'out1', snk_gh, 'in1', label='12')

c21 = Connection(src_hf, 'out1', cmp_co, 'in2', label='21')
c22 = Connection(cmp_co, 'out2', snk_hf, 'in1', label='22')

heatpump.add_conns(c01, c02, c02cc, c03, c04, c11, c12, c21, c22)

# parameters

# components
cmp_ev.set_attr(pr1=1, pr2=1)
cmp_cp.set_attr(eta_s=0.75)
cmp_co.set_attr(pr1=1, pr2=1, Q=-20e3)

# connections
c03.set_attr(p=20, T=40, fluid=fld_wf)
c04.set_attr(p=5)
T_sup = PSI("T", "Q", 1, "P", 5e5, wf) + 273.15 + 2
h_sup = PSI("H", "T", T_sup - 273.15, "P", 5*1e5, wf) / 1e3
c01.set_attr(h=h_sup)

c11.set_attr(p=1.013, T=15, fluid=fld_gh)
c12.set_attr(T=10)

c21.set_attr(p=2, T=35, fluid=fld_hf)
c22.set_attr(T=50)

# power and heat busses
motor = Bus('motor')
motor.add_comps({'comp': cmp_cp, 'char': 0.95, 'base': 'bus'})

groundheat = Bus('groundheat')
groundheat.add_comps({
      'comp': src_gh, 'base': 'bus'},
      {'comp': snk_gh, 'base': 'component'}
      )

heating = Bus('heating')
heating.add_comps({
      'comp': src_hf, 'base': 'bus'}, 
      {'comp': snk_hf, 'base': 'component'}
      )

heatpump.add_busses(motor, groundheat, heating)

# solve
heatpump.solve(mode='design')
heatpump.print_results()

print('### init ###')
print('COP:', abs(cmp_co.Q.val) / motor.P.val)

c01.set_attr(h=None)
cmp_ev.set_attr(ttd_u=5)

heatpump.solve(mode='design')
heatpump.print_results()

# print coefficient of performance
print('### final ###')
print('COP:', abs(cmp_co.Q.val) / motor.P.val)

# exergy analysis
ean = ExergyAnalysis(network=heatpump, E_F=[motor, groundheat], E_P=[heating])
ean.analyse(pamb=1.013, Tamb=15)
ean.print_results()

# grassmann diagram

links, nodes = ean.generate_plotly_sankey_input()
fig = go.Figure(go.Sankey(
    arrangement="snap",
    node={
        "label": nodes,
        'pad': 11,
        'color': 'orange'},
    link=links),
    layout=go.Layout({'width': 800})
    )
# figpath = os.path.join(
#     __file__, '..', 'plots', 'simpl_heat_pump_grassmann.pdf'
#     )
# fig.write_image(figpath)

# log p,h-diagram

result_dict = {}
result_dict.update({cmp_ev.label : cmp_ev.get_plotting_data()[2]})
result_dict.update({cmp_cp.label : cmp_cp.get_plotting_data()[1]})
result_dict.update({cmp_co.label : cmp_co.get_plotting_data()[1]})
result_dict.update({cmp_th.label : cmp_th.get_plotting_data()[1]})

diagram = FluidPropertyDiagram(wf)
diagram.set_unit_system(T='°C', p='bar', h='kJ/kg')

for key, data in result_dict.items():
    result_dict[key]['datapoints'] = diagram.calc_individual_isoline(**data)

diagram.set_limits(x_min=200, x_max=500, y_min=1e0, y_max=1e2)
diagram.calc_isolines()
diagram.draw_isolines('logph')

for key in result_dict.keys():
    if key == 'throttle':
        continue
    datapoints = result_dict[key]['datapoints']
    diagram.ax.plot(datapoints['h'],datapoints['p'], color='#EC6707')
    diagram.ax.scatter(datapoints['h'][0],datapoints['p'][0], color='#B54036')

diagram.ax.plot([c03.h.val, c04.h.val], [c03.p.val, c04.p.val], color='#EC6707')
diagram.ax.scatter(
    [c03.h.val, c04.h.val], [c03.p.val, c04.p.val], color='#B54036'
    )

# figpath = os.path.join(
#     __file__, '..', 'plots', 'simple_heat_pump_logp-h.pdf'
#     )
# diagram.save(figpath, dpi=300)