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
import seaborn as sns
import matplotlib.ticker as mtick

# Paths and filenames
figsfolder = 'figs'
resfolder = 'results'
scenarios = ['masks30_notschools', 'masks30', 'masks15_notschools', 'masks15']
resnames = sc.odict({'cum_inf': 'Cumulative infections (millions)',
                     'peak_inf': 'Peak infections (thousands)',
                     'cum_death': 'Cumulative deaths (thousands)'})

T = sc.tic()

# Define plotting functions

# Fonts and sizes
font_size = 36
font_family = 'Libertinus Sans'
pl.rcParams['font.size'] = font_size
pl.rcParams['font.family'] = font_family

# Plot locations
# Subplot sizes
xgapl = 0.075
xgapm = 0.02
xgapr = 0.075
ygapb = 0.065
ygapm = 0.05
ygapt = 0.04
nrows = 2
ncols = 2
dc = 0.025
dx = (1 - ncols * xgapm - xgapl - xgapr - dc) / ncols
dy = (1 - (nrows - 1) * ygapm - ygapb - ygapt) / nrows
ax = {}

# Load all results
sweep_summaries = {}
for scen in scenarios:
    filepath = f'{resfolder}/uk_tti_sweeps_{scen}.obj'
    sweep_summaries[scen] = sc.loadobj(filepath)

msim = sc.loadobj(f'{resfolder}/uk_sim.obj')
msim.reduce()
inf_til_aug = msim.results['cum_infections'].values[-1]
death_til_aug = msim.results['cum_deaths'].values[-1]

# Translate them into a dict of dataframes
dfs = sc.odict()
cbar_lims = {}
for res in resnames.keys():
    dfs[res] = sc.odict()
    for scen in scenarios:
        dfs[res][scen] = pd.DataFrame(sweep_summaries[scen][res])
        if res=='cum_inf':
            dfs[res][scen] = (dfs[res][scen]-inf_til_aug) / 1e6
        elif res=='cum_death':
            dfs[res][scen] = (dfs[res][scen] - death_til_aug) / 1e3
        else:
            dfs[res][scen] /= 1e3
    cbar_lims[res] = max(dfs[res]['masks15_notschools'].max())

#import traceback; traceback.print_exc(); import pdb; pdb.set_trace()

# Add text
headings = ["Masks in community, EC 30%",
            "Masks in community & schools, EC 30%",
            "Masks in community, EC 15%",
            "Masks in community & schools, EC 15%"
            ]

# Loop over each result to create a separate figure
for res,label in resnames.iteritems():

    pl.figure(figsize=(24, 20))
    cbar_ax = pl.axes([xgapl + (dx + xgapm) * ncols, ygapb, dc, dy * nrows + ygapm * (nrows - 1)])

    for pn,scen in enumerate(scenarios):
        pl.figtext(xgapl + (dx+xgapm)*(pn%ncols), ygapb+dy*(pn//ncols+1)+ygapm*(pn//ncols)+ygapm*.25, headings[pn],
               fontsize=36, fontweight='bold', bbox={'edgecolor': 'none', 'facecolor': 'white', 'alpha': 0.5, 'pad': 4})

        ax[pn] = pl.axes([xgapl + (dx + xgapm) * (pn % ncols), ygapb + (ygapm + dy) * (pn // ncols), dx, dy])
        ax[pn] = sns.heatmap(dfs[res][scen], xticklabels=4, yticklabels=4, cmap=sns.cm.rocket_r,
                             vmin=0, vmax=cbar_lims[res],
                             cbar=pn==0, cbar_ax=None if pn else cbar_ax,
                             cbar_kws={'label': label})
        ax[pn].set_ylim(ax[pn].get_ylim()[::-1])

        if (pn%ncols) != 0:
            ax[pn].set_yticklabels([])
        else:
            ax[pn].set_ylabel('Symptomatic testing')
            ax[pn].set_yticklabels([f'{int(i*100)}%' for i in np.linspace(0,1,6)], rotation=0)
        if pn not in range(ncols):
            ax[pn].set_xticklabels([])
        else:
            ax[pn].set_xlabel('% of contacts traced')
            ax[pn].set_xticklabels([f'{int(i * 100)}%' for i in np.linspace(0, 1, 6)])

    cv.savefig(f'{figsfolder}/fig_sweeps_{res}.png', dpi=100)

sc.toc(T)