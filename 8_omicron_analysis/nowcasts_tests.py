'''
Plotting UK vaccine scenarios
'''

import numpy as np
import pylab as pl
import covasim as cv
import sciris as sc

T = sc.tic()
# Load files and extract data
msim_details = {#'Nowcasting 01 Dec': 'results_Vac/uk_sim_test_20Nov.obj',
                #'Opening Schools in January 2022 and partial lockdown': 'results/uk_sim_test_01Dec_omic.obj',
                'Lockdown January-March 2022': 'results/uk_sim_test_01Dec_omic.obj'}
                #'Delta, June Step 4 opening and Vaccine extended to teenagers': 'results_Vac/uk_sim_test_vx1.obj'}

    #for the PTRSA paper
                #'Scenario 1: no Delta, Vaccine and June Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov_openJune_nodelta.obj',
                #'Scenario 2: Delta, Vaccine and June Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov_openJune.obj',
               # 'Scenario 3: Delta, Vaccine and June Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov_vx1.obj'}
                #'Scenario 3: Delta, Vaccine and July Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov.obj'}
                #'Scenario 4: no Delta, No Vaccine and June Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov_openJune_nodelta_novac.obj',
                #'Scenario 5: Delta, No Vaccine and June Stage 4 opening': 'results_Vac/uk_sim_calibration_2Nov_openJune_delta_novac.obj'}
labels = msim_details.keys()
msims = sc.odict()
plotkeys = ['new_diagnoses', 'new_severe', 'n_severe', 'new_deaths']
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

start_day = '2021-01-01'
end_day = '2022-01-01'
data_end_day  = '2022-01-01' # Final date for calibration -- set this to a date before boosters started


#start_day = '2021-05-01'
#data_end_day = '2021-11-22'
#end_day = '2021-12-30'
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
datemarks = pl.array([sim.day('2021-01-01'), sim.day('2021-03-01'),  sim.day('2021-05-01'), sim.day('2021-07-01'), sim.day('2021-09-01'), sim.day('2021-10-01'), sim.day('2021-11-01'), sim.day('2021-12-01'), sim.day('2022-01-01')])-sim.day('2021-01-01')
#datemarks = pl.array([sim.day('2021-09-01'), sim.day('2021-10-01'), sim.day('2021-11-01'), sim.day('2021-12-01'), sim.day('2022-01-01'), sim.day('2022-02-01')])-sim.day('2021-09-01')
#datemarks = pl.array([sim.day('2021-12-01'), sim.day('2021-12-01'), sim.day('2022-01-01'), sim.day('2022-02-01')])-sim.day('2021-12-01')


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
    low    = plotdict_l['new_diagnoses'][l][date_inds[0]:date_inds[1]]
    high   = plotdict_h['new_diagnoses'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)

pl.ylabel('Daily new diagnoses')
ax = pl.gca()
ax.set_xticks(datemarks)
sc.datenumformatter(start_date=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
sc.commaticks()
pl.legend(frameon=False)
sc.boxoff()


# Plot B: R_eff
#pl.subplot(2, 2, 2)
#colors = pl.cm.RdPu([0.3,0.6,0.9])
#colors = pl.cm.GnBu([0.9,0.6,0.3])
#for i,l in enumerate(labels):
#    toplot = plotdict['r_eff'][l][date_inds[0]:date_inds[1]]
#    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
#    low = plotdict_l['r_eff'][l][date_inds[0]:date_inds[1]]
#    high = plotdict_h['r_eff'][l][date_inds[0]:date_inds[1]]
#    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
#pl.ylabel('R')
#pl.axhline(1, linestyle=':', c='k', alpha=0.3)
#ax = pl.gca()
#ax.set_xticks(datemarks)
#cv.date_formatter(start_day=start_day, ax=ax, dateformat=dateformat)
#sc.setylim()
#pl.legend(frameon=False)
#sc.boxoff()

# Plot C: severe cases
pl.subplot(2, 2, 2)
colors = pl.cm.RdPu([0.3,0.6,0.9])
colors = pl.cm.YlOrBr([0.9,0.6,0.3])
for i,l in enumerate(labels):
    if i==0:
        ds = np.arange(0,len(tvec_d),7) # Downsample
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
sc.datenumformatter(start_date=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
sc.commaticks()
pl.legend(frameon=False)
sc.boxoff()

# Plot D: deaths
pl.subplot(2, 2, 3)
colors = pl.cm.RdPu([0.3,0.6,0.9])
#colors = pl.cm.Greens([0.9,0.6,0.3])
for i,l in enumerate(labels):
    if i==0:
        ds = np.arange(0,len(tvec_d),7) # Downsample
        thissim = msims[l].sims[0]
        datatoplot = thissim.data['n_severe'][date_inds_d[0]:date_inds_d[1]]
        pl.plot(tvec_d[ds], datatoplot[ds], 'd', c='k', markersize=12, alpha=0.75, label='Data')
    toplot = plotdict['n_severe'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    low = plotdict_l['n_severe'][l][date_inds[0]:date_inds[1]]
    high = plotdict_h['n_severe'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
pl.ylabel('Occupancy')
ax = pl.gca()
ax.set_xticks(datemarks)
sc.datenumformatter(start_date=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
sc.commaticks()
pl.legend(frameon=False)
sc.boxoff()

#Plot B alternative: ICUs
pl.subplot(2, 2, 4)
colors = pl.cm.GnBu([0.9,0.6,0.3])
for i,l in enumerate(labels):
    if i==0:
        ds = np.arange(0,len(tvec_d),1) # Downsample
        thissim = msims[l].sims[0]
        datatoplot = thissim.data['new_deaths'][date_inds_d[0]:date_inds_d[1]]
        pl.plot(tvec_d[ds], datatoplot[ds], 'd', c='k', markersize=12, alpha=0.75, label='Data')
    toplot = plotdict['new_deaths'][l][date_inds[0]:date_inds[1]]
    pl.plot(tvec, toplot, c=colors[i], label=l, lw=4, alpha=1.0)
    low = plotdict_l['new_deaths'][l][date_inds[0]:date_inds[1]]
    high = plotdict_h['new_deaths'][l][date_inds[0]:date_inds[1]]
    pl.fill_between(tvec, low, high, facecolor=colors[i], alpha=0.2)
pl.ylabel('Daily Deaths')
pl.axhline(1, linestyle=':', c='k', alpha=0.3)
ax = pl.gca()
ax.set_xticks(datemarks)
sc.datenumformatter(start_date=start_day, ax=ax, dateformat=dateformat)
sc.setylim()
pl.legend(frameon=False)
sc.boxoff()



cv.savefig('figs/uk_vx_scens_presentation.png')


