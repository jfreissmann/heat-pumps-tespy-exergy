import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from heatpumps.models.ihx import HeatPumpIHX
from heatpumps.models.intercooling import HeatPumpIntercooling
from heatpumps.models.parallel import HeatPumpParallelComp
from heatpumps.models.simple import HeatPumpSimple


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
    inputpath = os.path.join(__file__, '..', 'input')
    for dir_path, subdirs, files in os.walk(inputpath):
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
    inputpath = os.path.join(__file__, '..', 'input')
    for dir_path, subdirs, files in os.walk(inputpath):
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

def multiplot_p_high_analysis_refrig_combined(refrig, use_REFPROP=True):
    """Plot p_high analysis for different topologies of the same refrigerant."""
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    markers = ['o', 'x', 's', 'D']
    fig, ax1 = plt.subplots(figsize=(11, 9))
    ax2 = ax1.twinx()
    count = 0
    # print(os.walk(os.path.join(__file__, '..', 'input')'input'))
    inputpath = os.path.join(__file__, '..', 'input')
    for dir_path, subdirs, files in os.walk(inputpath):
        for file in files:
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            # params['ambient']['p'] = 1.013
            # with open(path, 'w') as file:
            #      json.dump(params, file, indent=4)

            if not refrig.upper() == params['setup']['refrig'].upper():
                continue

            if not use_REFPROP and ('REFPROP' in params['fluids']['wf']):
                params['fluids']['wf'] = refrig

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
                    __file__, '..', 'output', 'raw_data',
                    f'multiplot_{params["setup"]["type"]}_{refrig}.csv'
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


def multiplot_p_high_analysis_hp_combined(hptype, use_REFPROP=True):
    """Plot p_high analysis for different topologies of the same refrigerant."""
    plt.rcParams['xtick.direction'] = 'in'
    plt.rcParams['ytick.direction'] = 'in'
    markers = ['o', 'x', 's', 'D']
    fig, ax1 = plt.subplots(figsize=(11, 9))
    ax2 = ax1.twinx()
    count = 0
    inputpath = os.path.join(__file__, '..', 'input')
    for dir_path, subdirs, files in os.walk(inputpath):
        for file in files:
            path = os.path.join(dir_path, file)
            with open(path, 'r') as file:
                params = json.load(file)

            # params['ambient']['p'] = 1.013
            # with open(path, 'w') as file:
            #      json.dump(params, file, indent=4)

            if not hptype == params['setup']['type']:
                continue

            if not use_REFPROP and ('REFPROP' in params['fluids']['wf']):
                params['fluids']['wf'] = refrig

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
                    __file__, '..', 'output', 'raw_data',
                    f'multiplot_{hptype}_{params["setup"]["refrig"]}.csv'
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


if __name__ == '__main__':
    # hp_types = [
    #     'HeatPumpSimple', 'HeatPumpIHX', 'HeatPumpParallelComp',
    #     'HeatPumpIntercooling'
    #     ]
    hp_types = ['HeatPumpIHX']

    # refrigs = ['R600', 'R601', 'R1233zd(E)']
    refrigs = ['R600']

    # res_types = ['COP', 'epsilon']

    # plotpath = os.path.join(__file__, '..', 'output', 'plots')

    # for hp_type in hp_types:
    #     for res_type in res_types:
    #         fig, ax = multiplot_p_high_analysis_hp(hp_type, result=res_type)

    #         figpath = os.path.join(
    #             plotpath, f'multiplot_{hp_type}_{res_type}.pdf'
    #             )
    #         plt.savefig(figpath)

    # for refrig in refrigs:
    #     for res_type in res_types:
    #         fig, ax = multiplot_p_high_analysis_refrig(
    #             refrig, result=res_type
    #             )

    #         figpath = os.path.join(
    #             plotpath, f'multiplot_{refrig}_{res_type}.pdf'
    #             )
    #         plt.savefig(figpath)

    # %% Create data for and example plot of Figure 6
    for refrig in refrigs:
        fig, ax1, ax2 = multiplot_p_high_analysis_refrig_combined(
            refrig, use_REFPROP=True
            )

    #     figpath = os.path.join(plotpath, f'multiplot_{refrig}_combined.pdf')
    #     plt.savefig(figpath)

    # %% Create data for and example plot of Figure 5
    for hp_type in hp_types:
        fig, ax1, ax2 = multiplot_p_high_analysis_hp_combined(
            hp_type, use_REFPROP=True
            )

    #     figpath = os.path.join(plotpath, f'\multiplot_{hp_type}_combined.pdf')
    #     plt.savefig(figpath)

    plt.show()
