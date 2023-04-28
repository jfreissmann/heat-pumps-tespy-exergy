import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import SWSHplotting as shplt

from heatpumps.models.ihx import HeatPumpIHX
from heatpumps.models.intercooling import HeatPumpIntercooling
from heatpumps.models.parallel import HeatPumpParallelComp
from heatpumps.models.simple import HeatPumpSimple

plt.rcParams['xtick.direction'] = 'in'
plt.rcParams['ytick.direction'] = 'in'
plt.rcParams['font.size'] = 16

# if os.path.exists('error_log_REFPROP.txt'):
#     os.remove('error_log_REFPROP.txt')

# for dir_path, subdirs, files in os.walk('input_Riedl'):
#     for file in files:
#         # if 'R1336' in file:
#         #     continue
#         path = os.path.join(dir_path, file)
#         with open(path, 'r') as file:
#             params = json.load(file)

#         with open(path, 'w') as file:
#             json.dump(params, file, indent=4)

#         if params['setup']['type'] == 'HeatPumpSimple':
#             hp = HeatPumpSimple(params)
#         elif params['setup']['type'] == 'HeatPumpIHX':
#             hp = HeatPumpIHX(params)
#         elif params['setup']['type'] == 'HeatPumpParallelComp':
#             hp = HeatPumpParallelComp(params)
#         elif params['setup']['type'] == 'HeatPumpIntercooling':
#             hp = HeatPumpIntercooling(params)

#         print('\n######################################')
#         print(
#             f'{hp.params["setup"]["type"]} '
#             + f'{hp.params["setup"]["refrig"]}'
#             )
#         print('######################################\n')
#         try:
#             hp.run_model()
#             with open('error_log_REFPROP.txt', 'a') as file:
#                 file.write(
#                     params['setup']['type'] + ' ' + params['setup']['refrig']
#                     + ' worked.' + '\n'
#                     )
#         except Exception as error:
#             with open('error_log_REFPROP.txt', 'a') as file:
#                 file.write(
#                     params['setup']['type'] + ' ' + params['setup']['refrig']
#                     + ' ' + str(error) + '\n'
#                     )

#         # if 'R1233zd(E)'.upper() == params['setup']['refrig'].upper():
#         #     if params['sensitivity']['p_high_min'] != 40:
#         #         params['sensitivity']['p_high_min'] = 40
#         #         with open(path, 'w') as file:
#         #             json.dump(params, file, indent=4)

#         hp.plot_p_high_analysis(
#             params['sensitivity']['p_high_min'],
#             params['sensitivity']['p_high_max'],
#             stepwidth=2,
#             savefig=True
#             )
# #         try:
# #             diagram = hp.plot_logph({}, return_diagram=True)
# #             diagram.ax.set_title(
# #                 f"{params['setup']['type']} {params['setup']['refrig']}"
# #                 )
# #             filepath = (
# #                 f'plots\\logph_{params["setup"]["type"]}_'
# #                 + f'{params["setup"]["refrig"]}.pdf'
# #                 )
# #             diagram.save(filepath, dpi=300)
# #         except (ValueError) as e:
# #             print(
# #                 params['setup']['type'] + ' ' + params['setup']['refrig']
# #                 + ' ' + str(e) + '\n'
# #                 )

# # shplt.create_multipage_pdf('plots\\logph_all.pdf')

#### DEBUG

# with open('input\\simple_cycle\\parameter_R1233zd(E).json', 'r') as file:
#     params = json.load(file)

# hp = HeatPumpSimple(params)

# hp.generate_components()
# hp.generate_connections()
# hp.init_simulation()
# hp.design_simulation(print_results=True)
# hp.plot_logph({}, savefig=True)


def multiplot_p_high_analysis_hp(hptype, result='COP'):
    """Plot p_high analysis for different refrigerants of the same topology."""
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
    fig, ax = plt.subplots(figsize=(14, 8))
    for dir_path, subdirs, files in os.walk('input_Riedl'):
        for file, c in zip(files, colors.values()):
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            params['ambient']['p'] = 1.013
            with open(path, 'w') as file:
                 json.dump(params, file, indent=4)

            if not hptype == params['setup']['type']:
                continue

            if params['setup']['type'] == 'HeatPumpSimple':
                hp = HeatPumpSimple(params)
            elif params['setup']['type'] == 'HeatPumpIHX':
                hp = HeatPumpIHX(params)
            elif params['setup']['type'] == 'HeatPumpParallelComp':
                hp = HeatPumpParallelComp(params)
            elif params['setup']['type'] == 'HeatPumpIntercooling':
                hp = HeatPumpIntercooling(params)

            hp.run_model()
            res, E_Ds = hp.run_p_high_analysis(
                params['sensitivity']['p_high_min'],
                params['sensitivity']['p_high_max'],
                stepwidth=1
            )

            ax.plot(
                res[result], marker='o',color=c,
                label=hp.params['setup']['refrig']                
                )

    if result == 'COP':
        ax.set_ylabel('Coefficient of Performance $COP$')
        ax.set_ylim((2.3, 3.1))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.025))
    elif result == 'epsilon':
        ax.set_ylabel('Exergy efficiency $\\epsilon$')
        ax.set_ylim((0.6, 0.8))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.01))
    else:
        raise ValueError(
            f"'result' {result} is invalid. Values can be 'COP' or 'epsilon'."
            )
    ax.set_xlabel('High pressure in $bar$')

    fig.suptitle(hptype)
    ax.set_xlim((25, 80))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.grid()
    ax.set_axisbelow(True)
    ax.legend()
    plt.tight_layout()

    return fig, ax

def multiplot_p_high_analysis_refrig(refrig, result='COP'):
    """Plot p_high analysis for different topologies of the same refrigerant."""
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
    fig, ax = plt.subplots(figsize=(14, 8))
    color_count = 0
    for dir_path, subdirs, files in os.walk('input_Riedl'):
        for file in files:
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            params['ambient']['p'] = 1.013
            with open(path, 'w') as file:
                 json.dump(params, file, indent=4)

            if not refrig.upper() == params['setup']['refrig'].upper():
                continue

            if params['setup']['type'] == 'HeatPumpSimple':
                hp = HeatPumpSimple(params)
            elif params['setup']['type'] == 'HeatPumpIHX':
                hp = HeatPumpIHX(params)
            elif params['setup']['type'] == 'HeatPumpParallelComp':
                hp = HeatPumpParallelComp(params)
            elif params['setup']['type'] == 'HeatPumpIntercooling':
                hp = HeatPumpIntercooling(params)

            hp.run_model()
            res, E_Ds = hp.run_p_high_analysis(
                params['sensitivity']['p_high_min'],
                params['sensitivity']['p_high_max'],
                stepwidth=1
            )

            ax.plot(
                res[result], marker='o',color=[*colors.values()][color_count],
                label=hp.params['setup']['type']                
                )
            color_count += 1

    if result == 'COP':
        ax.set_ylabel('Coefficient of Performance $COP$')
        ax.set_ylim((1, 3))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.05))
    elif result == 'epsilon':
        ax.set_ylabel('Exergy efficiency $\\epsilon$')
        ax.set_ylim((0.3, 0.8))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
        ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.01))
    else:
        raise ValueError(
            f"'result' {result} is invalid. Values can be 'COP' or 'epsilon'."
            )
    ax.set_xlabel('High pressure in $bar$')

    fig.suptitle(refrig)
    ax.set_xlim((50, 100))
    ax.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax.grid()
    ax.set_axisbelow(True)
    ax.legend()
    plt.tight_layout()

    return fig, ax

def multiplot_p_high_analysis_refrig_combined(refrig):
    """Plot p_high analysis for different topologies of the same refrigerant."""
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    markers = ['o', 'x', 's', 'D']
    fig, ax1 = plt.subplots(figsize=(11, 9))
    ax2 = ax1.twinx()
    count = 0
    for dir_path, subdirs, files in os.walk('input_Riedl'):
        for file in files:
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            params['ambient']['p'] = 1.013
            with open(path, 'w') as file:
                 json.dump(params, file, indent=4)

            if not refrig.upper() == params['setup']['refrig'].upper():
                continue

            if params['setup']['type'] == 'HeatPumpSimple':
                hp = HeatPumpSimple(params)
            elif params['setup']['type'] == 'HeatPumpIHX':
                hp = HeatPumpIHX(params)
            elif params['setup']['type'] == 'HeatPumpParallelComp':
                hp = HeatPumpParallelComp(params)
            elif params['setup']['type'] == 'HeatPumpIntercooling':
                hp = HeatPumpIntercooling(params)

            hp.run_model()
            res, E_Ds = hp.run_p_high_analysis(
                params['sensitivity']['p_high_min'],
                params['sensitivity']['p_high_max'],
                stepwidth=1
            )

            res.to_csv(
                os.path.join(
                    'raw_data',
                    f'multiplot_{params["setup"]["type"]}_{refrig}_RIEDL.csv'
                    ), sep=';'
                )


            ax1.plot(
                res['COP'], marker=markers[count], color='#00395B',
                label=hp.params['setup']['type']                
                )
            ax2.plot(
                res['epsilon'], marker=markers[count], color='#EC6707'
                )
            count += 1

    ax1.set_ylabel('Coefficient of Performance $COP$', color='#00395B')
    ax1.set_ylim((1, 3))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(0.2))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(0.05))

    ax2.set_ylabel('Exergy efficiency $\\epsilon$', color='#EC6707')
    ax2.set_ylim((0.3, 0.8))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(0.05))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(0.01))

    ax1.set_xlabel('High pressure in $bar$')

    ax1.set_xlim((50, 100))
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax1.grid()
    ax1.set_axisbelow(True)
    ax1.legend()
    plt.tight_layout()

    return fig, ax1, ax2


def multiplot_p_high_analysis_hp_combined(hptype):
    """Plot p_high analysis for different topologies of the same refrigerant."""
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    markers = ['o', 'x', 's', 'D']
    fig, ax1 = plt.subplots(figsize=(11, 9))
    ax2 = ax1.twinx()
    count = 0
    for dir_path, subdirs, files in os.walk('input_Riedl'):
        for file in files:
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            params['ambient']['p'] = 1.013
            with open(path, 'w') as file:
                 json.dump(params, file, indent=4)

            if not hptype == params['setup']['type']:
                continue

            if params['setup']['type'] == 'HeatPumpSimple':
                hp = HeatPumpSimple(params)
            elif params['setup']['type'] == 'HeatPumpIHX':
                hp = HeatPumpIHX(params)
            elif params['setup']['type'] == 'HeatPumpParallelComp':
                hp = HeatPumpParallelComp(params)
            elif params['setup']['type'] == 'HeatPumpIntercooling':
                hp = HeatPumpIntercooling(params)

            hp.run_model()
            res, E_Ds = hp.run_p_high_analysis(
                params['sensitivity']['p_high_min'],
                params['sensitivity']['p_high_max'],
                stepwidth=1
            )

            res.to_csv(
                os.path.join(
                    'raw_data',
                    f'multiplot_{hptype}_{params["setup"]["refrig"]}_RIEDL.csv'
                    ), sep=';'
                )

            ax1.plot(
                res['COP'], marker=markers[count], color='#00395B',
                label=hp.params['setup']['refrig']                
                )
            ax2.plot(
                res['epsilon'], marker=markers[count], color='#EC6707'
                )
            count += 1

    prop_fac = res['epsilon'].mean()/res['COP'].mean()

    ax1.set_ylabel('Coefficient of Performance $COP$', color='#00395B')
    ax1.set_ylim((2.2, 3))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax1.yaxis.set_minor_locator(ticker.MultipleLocator(0.025))

    ax2.set_ylabel('Exergy efficiency $\\epsilon$', color='#EC6707')
    ax2.set_ylim((0.6, 0.8))
    ax2.yaxis.set_major_locator(ticker.MultipleLocator(0.025))
    ax2.yaxis.set_minor_locator(ticker.MultipleLocator(0.005))

    ax1.set_xlabel('High pressure in $bar$')

    ax1.set_xlim((20, 100))
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(5))
    ax1.xaxis.set_minor_locator(ticker.MultipleLocator(1))
    ax1.grid()
    ax1.set_axisbelow(True)
    ax1.legend()
    plt.tight_layout()

    return fig, ax1, ax2

# hp_types = [
#     'HeatPumpSimple', 'HeatPumpIHX', 'HeatPumpParallelComp',
#     'HeatPumpIntercooling'
#     ]
hp_types = ['HeatPumpIHX']

# refrigs = ['R600', 'R601', 'R1233zd(E)']
refrigs = ['R600']

# res_types = ['COP', 'epsilon']

# for hp_type in hp_types:
#     for res_type in res_types:
#         fig, ax = multiplot_p_high_analysis_hp(hp_type, result=res_type)

#         plt.savefig(f'plots\\multiplot_{hp_type}_{res_type}_RIEDL.pdf')

# for refrig in refrigs:
#     for res_type in res_types:
#         fig, ax = multiplot_p_high_analysis_refrig(refrig, result=res_type)

#         plt.savefig(f'plots\\multiplot_{refrig}_{res_type}_RIEDL.pdf')

for refrig in refrigs:
    fig, ax1, ax2 = multiplot_p_high_analysis_refrig_combined(refrig)

    # plt.savefig(f'plots\\multiplot_{refrig}_combined_RIEDL.pdf')

for hp_type in hp_types:
    fig, ax1, ax2 = multiplot_p_high_analysis_hp_combined(hp_type)

    # plt.savefig(f'plots\\multiplot_{hp_type}_combined_RIEDL.pdf')
