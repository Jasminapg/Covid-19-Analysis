'''

Script to plot some omicron scenarios.
'''


import numpy as np
import sciris as sc
import covasim as cv
import covasim.parameters as cvpar
import os
import sys
import matplotlib.pyplot as plt
import calibrate_uk as exo
import pandas as pd

do_save = True
do_show = True

d = sc.load(exo.heatmap_file)
df = pd.DataFrame(data=d)
sweep_params = exo.sweep_om_pars()

colormaps = {'cum_infections': 'viridis_r',
             'cum_severe': 'plasma_r',
             'cum_deaths': 'inferno_r'
             }

#################################
# Define plotting functions
# (these could be moved to a utils file at some point??)
#################################

# Heat map interpolation
def gauss2d(x, y, z, xi, yi, eps=1.0, xscale=1.0, yscale=1.0):
    def arr32(arr):
        return np.array(arr, dtype=np.float32)

    def f32(x):
        return np.float32(x)

    x, y, z, xi, yi = arr32(x), arr32(y), arr32(z), arr32(xi), arr32(yi)
    eps, xscale, yscale = f32(eps), f32(xscale), f32(yscale)

    # Actual computation
    nx = len(xi)
    ny = len(yi)
    zz = np.zeros((ny, nx))
    for i in range(nx):
        for j in range(ny):
            dist = np.sqrt(((x - xi[i]) / xscale) ** 2 + ((y - yi[j]) / yscale) ** 2)
            weights = np.exp(-(dist / eps) ** 2)
            weights = weights / np.sum(weights)
            val = np.sum(weights * z)
            zz[j, i] = val

    return np.array(zz, dtype=np.float64)  # Convert back


# Surface plot
def plot_surface(ax, dfr, which='infections', z_range=None):
    x = np.array(dfr['rel_beta'])
    y = np.array(dfr['rel_imm'])
    z = np.array(dfr[which])
    if which == 'cum_infections':
        z = z / 1e6
    elif which in ['cum_severe', 'cum_deaths']:
        z = z / 1e3

    try:
        min_x = min(dfr['rel_beta'])
        min_y = min(dfr['rel_imm'])
        max_x = max(dfr['rel_beta'])
        max_y = max(dfr['rel_imm'])
    except:
        import traceback;
        traceback.print_exc();
        import pdb;
        pdb.set_trace()

    min_z = z_range[0]
    max_z = z_range[1]

    eps = 0.08
    npts = 100
    xi = np.linspace(min_x, max_x, npts)
    yi = np.linspace(min_y, max_y, npts)
    xx, yy = np.meshgrid(xi, yi)
    zz = gauss2d(x, y, z, xi, yi, eps=eps, xscale=max_x - min_x, yscale=max_y - min_y)

    cmap = colormaps[which]
    im = ax.contourf(xx, yy, zz, cmap=cmap, levels=np.linspace(min_z, max_z, 100))
    scolors = sc.vectocolor(z, cmap=cmap, minval=min_z, maxval=max_z)
    ax.scatter(x, y, marker='o', c=scolors, edgecolor=[0.3] * 3, s=50, linewidth=0.1, alpha=0.5)
    ax.contour(xx, yy, zz, levels=10, linewidths=0.5, colors='k')

    ax.set_xlabel('Relative transmissibility')
    ax.set_ylabel('Relative immune escape')
    ax.set_xlim([min_x, max_x])
    ax.set_ylim([min_y, max_y])

    return im


#%% Make the plots
if __name__ == '__main__':

    plt.rcParams['font.size'] = 36
    plt.rcParams['font.family'] = 'Libertinus Sans'

    # Initialize figure
    fig = plt.figure(figsize=(25, 30))
    gs = fig.add_gridspec(3, 8, width_ratios=[8, 1, 3, 8, 1, 3, 8, 1])
    plt.subplots_adjust(hspace=0.25, wspace=0.1, left=0.07, right=0.96, top=0.95, bottom=0.07)

    # Plot severity by row
    for rn,r in enumerate([0.3, 1, 1.3]):
        # Subset dataframe
        dfr = df[df['rel_sev'] == r]

        # A: cumulative infections
        z_min = int(np.floor(min(df['cum_infections'])/1e6))
        z_max = int(np.ceil(max(df['cum_infections'])/1e6))
        axa = fig.add_subplot(gs[rn, 0])
        ima = plot_surface(axa, dfr, which='cum_infections', z_range=[z_min,z_max])
        axa.set_title("Infections (M)")

        # Cumulative infections colorbar
        axac = fig.add_subplot(gs[rn, 1])
        cbara = plt.colorbar(ima, ticks=np.linspace(z_min, z_max, 6), cax=axac)

        # B: cumulative severe
        z_min = int(np.floor(min(df['cum_severe'])/1e3))
        z_max = int(np.ceil(max(df['cum_severe'])/1e3))
        axb = fig.add_subplot(gs[rn, 3])
        imb = plot_surface(axb, dfr, which='cum_severe', z_range=[z_min,z_max])
        axb.set_title("Severe cases (T)")

        # Cumulative severe colorbar
        axbc = fig.add_subplot(gs[rn, 4])
        cbarb = plt.colorbar(imb, ticks=np.linspace(z_min, z_max, 5), cax=axbc)

        # C: cumulative deaths
        z_min = int(np.floor(min(df['cum_deaths'])/1e3))
        z_max = int(np.ceil(max(df['cum_deaths'])/1e3))
        axc = fig.add_subplot(gs[rn, 6])
        imc = plot_surface(axc, dfr, which='cum_deaths', z_range=[z_min,z_max])
        axc.set_title("Deaths (T)")

        # Cumulative deaths colorbar
        axcc = fig.add_subplot(gs[rn, 7])
        cbarc = plt.colorbar(imc, ticks=np.linspace(z_min, z_max, 7), cax=axcc)


    cv.savefig('omicron_heat_map.png', dpi=150)

