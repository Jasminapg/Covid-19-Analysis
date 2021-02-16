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
scenarios = ['masks30_notschools', 'masks30', 'masks15_notschools', 'masks15']
scenarios
T = sc.tic()

# Define plotting functions
#%% Helper functions

def format_ax(ax, sim, key=None):
    @ticker.FuncFormatter
    def date_formatter(x, pos):
        return (sim['start_day'] + dt.timedelta(days=int(x))).strftime('%b-%y')
    ax.xaxis.set_major_formatter(date_formatter)
    pl.xlim([0, sim['n_days']])
    return

def plotter(key, sims, ax, label='', ylabel='', low_q=0.05, high_q=0.95, startday=None):

    color = cv.get_colors()[key.split('_')[1]]

    ys = []
    for s in sims:
        ys.append(s.results[key].values)
    yarr = np.array(ys)

    best = pl.median(yarr, axis=0)
    low  = pl.quantile(yarr, q=low_q, axis=0)
    high = pl.quantile(yarr, q=high_q, axis=0)

    sim = sims[0]

    tvec = np.arange(len(best))

    fill_label = None
    pl.fill_between(tvec, low, high, facecolor=color, alpha=0.2, label=fill_label)
    pl.plot(tvec, best, c=color, label=label, lw=4, alpha=1.0)

    sc.setylim()

    datemarks = pl.array([sim.day('2020-03-01'),sim.day('2020-05-01'),sim.day('2020-07-01'),
                          sim.day('2020-09-01')])
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
nrows = 2
ncols = 2
dx = (1 - (ncols - 1) * xgapm - xgapl - xgapr) / ncols
dy = (1 - (nrows - 1) * ygapm - ygapb - ygapt) / nrows
nplots = nrows * ncols
ax = {}

labels = {'current': ['24% symp. testing \n 47% contact tracing ']*4,
          'optimal': ['57% symp. testing \n 47% contact tracing ',
                      '46% symp. testing \n 47% contact tracing ',
                      '76% symp. testing \n 47% contact tracing ',
                      '68% symp. testing \n 47% contact tracing ']}
for tti_scen in ['current', 'optimal']:

    pl.figure(figsize=(24, 16))
    # Import files
    filepaths = [f'{resfolder}/uk_sim_{scen}_{tti_scen}.obj' for scen in scenarios]
    sims = sc.odict()
    for scen in scenarios:
        filepath = f'{resfolder}/uk_sim_{scen}_{tti_scen}.obj'
        simsfile = sc.loadobj(filepath)
        sims[scen] = simsfile.sims
    sim = sims[0][0] # Extract a sim to refer to

    # Add text
    headings =["             Masks in parts of community              ",
               "             Masks in parts of community             \n"
               "                and in secondary schools             "]
    epsx = 0.003
    epsy = 0.008
    llpad = 0.01
    rlpad = 0.005

    masks_begin = sim.day('2020-09-01')

    for nc in range(ncols):
        pl.figtext(xgapl + (dx + xgapm) * nc + epsx, ygapb + dy * nrows + ygapm * (nrows - 1) + llpad, headings[nc],
               fontsize=36, fontweight='bold', bbox={'edgecolor': 'none', 'facecolor': 'white', 'alpha': 0.5, 'pad': 4})

    pl.figtext(xgapl + dx * ncols + xgapm + rlpad, ygapb + (ygapm + dy) * 0 + epsy,'            Masks: 30% EC        ',
               rotation=90, fontweight='bold',
               bbox={'edgecolor': 'none', 'facecolor': 'white', 'alpha': 0.5, 'pad': 4})
    pl.figtext(xgapl + dx * ncols + xgapm + rlpad, ygapb + (ygapm + dy) * 1 + epsy,'            Masks: 15% EC        ',
               rotation=90, fontweight='bold',
               bbox={'edgecolor': 'none', 'facecolor': 'white', 'alpha': 0.5, 'pad': 4})

    for pn in range(nplots):
        ax[pn] = pl.axes([xgapl + (dx + xgapm) * (pn % ncols), ygapb + (ygapm + dy) * (pn // ncols), dx, dy])
        print([xgapl + (dx + xgapm) * (pn % ncols), ygapb + (ygapm + dy) * (pn // ncols)])
        print(list(sims.keys())[pn])
        format_ax(ax[pn], sim)
        ax[pn].axvline(masks_begin, c=[0, 0, 0], linestyle='--', alpha=0.4, lw=3)
#        pl.figtext(xgapl + (dx + xgapm) * (pn % ncols) + dx, ygapb + (ygapm + dy) * (pn // ncols) + dy, '            24%         ')
        ax[pn].annotate(labels[tti_scen][pn], xy=(700, 340_000), xycoords='data', ha='right', va='top')
        plotter('new_infections', sims[pn], ax[pn])
        ax[pn].set_ylim(0, 150_000)
        ax[pn].set_yticks(np.arange(0, 150_000, 25_000))

        if (pn%ncols) != 0:
            ax[pn].set_yticklabels([])
        else:
            ax[pn].set_ylabel('New infections')
        if pn not in range(ncols):
            ax[pn].set_xticklabels([])

    cv.savefig(f'{figsfolder}/fig_scens_{tti_scen}TTI.png', dpi=100)

sc.toc(T)