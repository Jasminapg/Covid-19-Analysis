'''
Plotting timeseries
'''

import numpy as np
import pylab as pl
import covasim as cv
import matplotlib as mpl
from matplotlib import ticker
import datetime as dt
import sciris as sc
import seaborn as sns
import pandas as pd

T = sc.tic()
# Load files and extract data
msim_details = {'Scenario 1':'results_Vac/uk_sim_calibration_testingonly.obj'}

labels = msim_details.keys()
msims = sc.odict()
plotkeys = ['new_diagnoses', 'r_eff', 'new_quarantined', 'new_severe']
plotdict = {k: {} for k in plotkeys}
plotdict_l = {k: {} for k in plotkeys}
plotdict_h = {k: {} for k in plotkeys}
for l,fp in msim_details.items():
    msims[l] = sc.loadobj(fp)
    for pk in plotkeys:
        plotdict[pk][l] = msims[l].results[pk].values
        plotdict_l[pk][l] = msims[l].results[pk].low
        plotdict_h[pk][l] = msims[l].results[pk].high

# Get a tvec and a sim
sim = msims[0].sims[0]

start_day = '2021-04-01'
data_end_day = '2021-07-30'
end_day = '2021-07-30'
date_inds = np.array([sim.day(start_day), sim.day(end_day)])
date_len = date_inds[1]-date_inds[0]
tvec = np.arange(date_len)

date_inds_d = np.array([sim.day(start_day), sim.day(data_end_day)])
date_len_d = date_inds_d[1]-date_inds_d[0]
tvec_d = np.arange(date_len_d)


#tvec = np.arange(len(msims[0].results['t']))

# Fonts and sizes for all figures
font_size = 22
font_family = 'Proxima Nova'
pl.rcParams['font.size'] = font_size
pl.rcParams['font.family'] = font_family
fig = pl.figure(figsize=(24, 16))

pl.subplots_adjust(left=0.08, right=0.97, bottom=0.05, top=0.97, hspace=0.3, wspace=0.3)
dateformat = '%b-%Y' #'%Y-%b-%d'

fsizel = 40
tx1 = 0.03
tx2 = 0.52
ty1 = 0.96
ty2 = 0.45
pl.figtext(tx1, ty1, 'A', fontsize=fsizel)
pl.figtext(tx2, ty1, 'B', fontsize=fsizel)
pl.figtext(tx1, ty2, 'C', fontsize=fsizel)
pl.figtext(tx2, ty2, 'D', fontsize=fsizel)

# Infections: RdPu, R: GnBu, Severe: YlOrBr, Deaths: Greys
datemarks = pl.array([sim.day('2021-04-01'), sim.day('2021-04-01'), sim.day('2021-05-01'), sim.day('2021-06-01'), sim.day('2021-07-01'), sim.day('2021-08-02')])-sim.day('2021-04-01')

# Plot A: new infections
pl.subplot(2, 2, 1)
colors = pl.cm.RdPu([0.3,0.6,0.9])
for i,l in enumerate(labels):
    if i==0:
        ds = np.arange(0,len(tvec_d),1) # Downsample
        thissim = msims[l].sims[0]
        datatoplot = thissim.data['new_diagnoses'][date_inds_d[0]:date_inds_d[1]]
        pl.plot(tvec_d[ds], datatoplot[ds], 'd', c='k', markersize=12, alpha=0.75, label='Data') 
    toplot = plotdict['new_diagnoses'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    #low    = plotdict_l['new_diagnoses'][l][date_inds[0]:date_inds[1]]
    #high   = plotdict_h['new_diagnoses'][l][date_inds[0]:date_inds[1]]
    #pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)

pl.ylabel('Daily new infections')
ax = pl.gca()
ax.set_xticks(datemarks)
cv.date_formatter(start_day=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
sc.commaticks()
pl.legend(frameon=False)
sc.boxoff()


# Plot B: R_eff
pl.subplot(2, 2, 2)
colors = pl.cm.GnBu([0.9,0.6,0.3])
for i,l in enumerate(labels):
    toplot = plotdict['r_eff'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    low = plotdict_l['r_eff'][l][date_inds[0]:date_inds[1]]
    high = plotdict_h['r_eff'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
pl.ylabel('R')
pl.axhline(1, linestyle=':', c='k', alpha=0.3)
ax = pl.gca()
ax.set_xticks(datemarks)
cv.date_formatter(start_day=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
pl.legend(frameon=False)
sc.boxoff()

# Plot C: isolating
pl.subplot(2, 2, 3)
colors = pl.cm.GnBu([0.9,0.6,0.3])
for i,l in enumerate(labels):
    toplot = plotdict['new_quarantined'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    #low = plotdict_l['new_quarantined'][l][date_inds[0]:date_inds[1]]
    #high = plotdict_h['new_quarantined'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
pl.ylabel('Isolating')
pl.axhline(1, linestyle=':', c='k', alpha=0.3)
ax = pl.gca()
ax.set_xticks(datemarks)
cv.date_formatter(start_day=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
pl.legend(frameon=False)
sc.boxoff()


# Plot D: severe cases
pl.subplot(2, 2, 4)
colors = pl.cm.YlOrBr([0.9,0.6,0.3])
for i,l in enumerate(labels):
    if i==0:
        ds = np.arange(0,len(tvec_d),1) # Downsample
        thissim = msims[l].sims[0]
        datatoplot = thissim.data['new_severe'][date_inds_d[0]:date_inds_d[1]]
        pl.plot(tvec_d[ds], datatoplot[ds], 'd', c='k', markersize=12, alpha=0.75, label='Data')
    toplot = plotdict['new_severe'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    low = plotdict_l['new_severe'][l][date_inds[0]:date_inds[1]]
    high = plotdict_h['new_severe'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
pl.ylabel('Daily Hospitalisations')
ax = pl.gca()
ax.set_xticks(datemarks)
cv.date_formatter(start_day=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
sc.commaticks()
pl.legend(frameon=False)
sc.boxoff()
cv.savefig('figs_Vac/uk_scens_plots.png')

