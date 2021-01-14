import covasim as cv
import pandas as pd
import sciris as sc
import pylab as pl
import numpy as np
from matplotlib import ticker
import matplotlib.dates as mdates
import datetime as dt
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

# Paths and filenames
figsfolder = 'figs'
resfolder = 'results'
T = sc.tic()

# Make the plots
print('Plotting...')

# Fonts and sizes
font_size = 36
font_family = 'Libertinus Sans'
pl.rcParams['font.size'] = font_size
pl.rcParams['font.family'] = font_family
fig = pl.figure(figsize=(24,10))
ax   = pl.axes([0.1, 0.11, 0.85, 0.85])

msim = sc.loadobj(f'{resfolder}/uk_sim_FNL.obj')
sim = msim.base_sim
tt = sim.make_transtree()
#tt = sc.loadobj(f'{resfolder}/tt.obj')
layer_keys = list(sim.people.layer_keys())
layer_mapping = {k:i for i,k in enumerate(layer_keys)}
n_layers = len(layer_keys)
colors = sc.gridcolors(n_layers)

layer_counts = np.zeros((sim.npts, n_layers))
for source_ind, target_ind in tt.transmissions:
    dd = tt.detailed[target_ind]
    date = dd['date']
    layer_num = layer_mapping[dd['layer']]
    layer_counts[date, layer_num] += sim.rescale_vec[date]

lockdown1 = [sc.readdate('2020-03-23'),sc.readdate('2020-05-31')]
lockdown2 = [sc.readdate('2020-11-05'),sc.readdate('2020-12-03')]
lockdown3 = [sc.readdate('2021-01-04'),sc.readdate('2021-02-08')]

labels = ['Household', 'School', 'Workplace', 'Community']
for l in range(n_layers):
    ax.plot(sim.datevec, layer_counts[:,l], c=colors[l], lw=3, label=labels[l])
ax.axvspan(lockdown1[0], lockdown1[1], color='steelblue', alpha=0.2, lw=0)
ax.axvspan(lockdown2[0], lockdown2[1], color='steelblue', alpha=0.2, lw=0)
ax.axvspan(lockdown3[0], lockdown3[1], color='lightblue', alpha=0.2, lw=0)
sc.setylim(ax=ax)
sc.boxoff(ax=ax)
ax.set_ylabel('Transmissions per day')
ax.set_xlim([sc.readdate('2020-01-21'), sc.readdate('2021-03-01')])
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b\n%y'))

datemarks = pl.array([sim.day('2020-02-01'), sim.day('2020-03-01'), sim.day('2020-04-01'), sim.day('2020-05-01'), sim.day('2020-06-01'),
                      sim.day('2020-07-01'), sim.day('2020-08-01'), sim.day('2020-09-01'), sim.day('2020-10-01'),
                      sim.day('2020-11-01'), sim.day('2020-12-01'), sim.day('2021-01-01'), sim.day('2021-02-01'), sim.day('2021-03-01')])
ax.set_xticks([sim.date(d, as_date=True) for d in datemarks])
ax.legend(frameon=False)


yl = ax.get_ylim()
labely = yl[1]*1.015

cv.savefig(f'{figsfolder}/fig_trans.png', dpi=100)

sc.toc(T)