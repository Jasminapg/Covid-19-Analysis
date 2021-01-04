import covasim as cv
import pandas as pd
import sciris as sc
import pylab as pl
import numpy as np
from matplotlib import ticker
import datetime as dt
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# Paths and filenames
figsfolder = 'figs'
resfolder = 'results'
scenarios = ['staggeredPNL', 'primaryPNL', 'FNL']
labels = ['Staggered PNL', 'Primary-only PNL', 'FNL']
T = sc.tic()

# Define plotting functions
#%% Helper functions

def format_ax(ax, sim, key=None):
    @ticker.FuncFormatter
    def date_formatter(x, pos):
        return (sim['start_day'] + dt.timedelta(days=int(x))).strftime('%b-%y')
    ax.xaxis.set_major_formatter(date_formatter)
    if key != 'r_eff':
        sc.commaticks()
    pl.xlim([0, sim['n_days']])
    pl.axvspan(lockdown1[0], lockdown1[1], color='steelblue', alpha=0.2, lw=0)
    pl.axvspan(lockdown2[0], lockdown2[1], color='steelblue', alpha=0.2, lw=0)
    pl.axvspan(lockdown3[0], lockdown3[1], color='lightblue', alpha=0.2, lw=0)

    return

def plotter(key, sims, ax, label='', ylabel='', low_q=0.05, high_q=0.95, subsample=2):

    which = key.split('_')[1]
    try:
        color = cv.get_colors()[which]
    except:
        color = [0.5,0.5,0.5]

    ys = []
    for s in sims:
        ys.append(s.results[key].values)
    yarr = np.array(ys)

    best = pl.median(yarr, axis=0)
    low  = pl.quantile(yarr, q=low_q, axis=0)
    high = pl.quantile(yarr, q=high_q, axis=0)


    tvec = np.arange(len(best))
#    tempsim = cv.Sim(datafile='../UK_Covid_cases_january03.xlsx')
#    sim = sims[0]
#    if key in tempsim.data:
#        data_t = np.array((tempsim.data.index-sim['start_day'])/np.timedelta64(1,'D'))
#        inds = np.arange(0, len(data_t), subsample)
#        data = tempsim.data[key][inds]
#        pl.plot(data_t[inds], data, 'd', c=color, markersize=10, alpha=0.5, label='Data')

    fill_label = None
    end = None
    start = 2 if key == 'r_eff' else 0
    pl.fill_between(tvec[start:end], low[start:end], high[start:end], facecolor=color, alpha=0.2, label=fill_label)
    pl.plot(tvec[start:end], best[start:end], c=color, label=label, lw=4, alpha=1.0)

    sc.setylim()

    datemarks = pl.array([sim.day('2020-03-01'),sim.day('2020-06-01'),sim.day('2020-09-01'),sim.day('2020-12-01')])
    ax.set_xticks(datemarks)
    pl.ylabel(ylabel)

    return


# Fonts and sizes
font_size = 36
font_family = 'Libertinus Sans'
pl.rcParams['font.size'] = font_size
pl.rcParams['font.family'] = font_family

# Plot locations
# Subplot sizes
xgapl = 0.1
xgapm = 0.02
xgapr = 0.03
ygapb = 0.05
ygapm = 0.02
ygapt = 0.1
nrows = 3
ncols = 3
dx = (1 - (ncols - 1) * xgapm - xgapl - xgapr) / ncols
dy = (1 - (nrows - 1) * ygapm - ygapb - ygapt) / nrows
nplots = nrows * ncols
ax = {}


pl.figure(figsize=(24, 16))
# Import files
filepaths = [f'{resfolder}/uk_sim_{scen}.obj' for scen in scenarios]
sims = sc.odict()
for scen in scenarios:
    filepath = f'{resfolder}/uk_sim_{scen}.obj'
    simsfile = sc.loadobj(filepath)
    sims[scen] = simsfile.sims
sim = sims[0][0] # Extract a sim to refer to

epsx = 0.003
epsy = 0.008
llpad = 0.01
rlpad = 0.005

lockdown1 = [sim.day('2020-03-23'),sim.day('2020-05-31')]
lockdown2 = [sim.day('2020-11-05'),sim.day('2020-12-03')]
lockdown3 = [sim.day('2021-01-04'),sim.day('2021-02-08')]

for nc in range(ncols):
    pl.figtext(xgapl + (dx + xgapm) * nc + epsx, ygapb + dy * nrows + ygapm * (nrows - 1) + llpad, labels[nc],
           fontsize=36, fontweight='bold', bbox={'edgecolor': 'none', 'facecolor': 'white', 'alpha': 0.5, 'pad': 4})

for pn in range(nplots):
    ax[pn] = pl.axes([xgapl + (dx + xgapm) * (pn % ncols), ygapb + (ygapm + dy) * (pn // ncols), dx, dy])
    print([xgapl + (dx + xgapm) * (pn % ncols), ygapb + (ygapm + dy) * (pn // ncols)])
    print(list(sims.keys())[pn % ncols])
    format_ax(ax[pn], sim)

    if (pn%ncols) != 0:
        ax[pn].set_yticklabels([])
    else:
        ax[pn].set_ylabel('New infections')

    if pn in range(ncols):
        plotter('r_eff', sims[pn % ncols], ax[pn])
        ax[pn].set_ylim(0, 3.5)
        ax[pn].axhline(y=1, color='red', linestyle='--')
        if (pn%ncols) == 0:
            ax[pn].set_ylabel('R')
    elif pn in range(ncols,ncols*2):
        plotter('cum_deaths', sims[pn % ncols], ax[pn])
        ax[pn].set_ylim(0, 100_000)
        if (pn%ncols) == 0:
            ax[pn].set_ylabel('Total deaths')
    else:
        plotter('new_infections', sims[pn % ncols], ax[pn])
        ax[pn].set_ylim(0, 150_000)
        if (pn%ncols) == 0:
            ax[pn].set_ylabel('New infections')

    if pn not in range(ncols):
        ax[pn].set_xticklabels([])

cv.savefig(f'{figsfolder}/fig_UK_school_scens.png', dpi=100)

sc.toc(T)