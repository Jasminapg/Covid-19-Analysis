import os
import sciris as sc
import covasim as cv
import pandas as pd

import matplotlib.pyplot as plt
import seaborn as sns

# Set general figure options
font_size = 12
plt.rcParams['font.size'] = font_size
plt.rcParams['figure.dpi'] = 400

result_dir = 'results_delay'
files = os.listdir(result_dir)
print(files)

# load data
df = {}
for file in files:
    print(file)
    if len(df) == 0:
        df.update({'reff_apr19': []})
        df.update({'reff_mar08': []})
        df.update({'scenario': []})
        df.update({'index': []})

    scenario = file.split('.')[0]
    msim = cv.load(os.path.join(result_dir, file))
    mar08 = msim.sims[0].day('2021-03-08')
    apr30 = msim.sims[0].day('2021-04-19')
    for ix, sim in enumerate(msim.sims):
        df['reff_mar08'].append(sim.results['r_eff'].values[mar08])
        df['reff_apr19'].append(sim.results['r_eff'].values[mar08:apr30 + 1].mean())
        df['scenario'].append(scenario)
        df['index'].append(ix)
df = pd.DataFrame(df)

# make figure
labs = {'uk_sim_FNL':'FNL', 'uk_sim_fullPNL':'Full PNL', 'uk_sim_primaryPNL':'Primary PNL', 'uk_sim_rotasecondaryPNL':'Part-Rota PNL', 'uk_sim_staggeredPNL':'Staggered PNL'}
#labs = {'uk_sim_FNL':'FNL', 'uk_sim_fullPNL':'Full PNL', 'uk_sim_primaryPNL':'Primary PNL'}
tmp = sc.dcp(df)
tmp['scenario'] = tmp['scenario'].apply(lambda x: labs[x])
fig, axes = plt.subplots()
sns.violinplot(x='scenario',y='reff_apr19',data=tmp, ax=axes)
xlim = axes.get_xlim()
axes.hlines(1, xlim[0], xlim[1], linestyle='--', zorder=0)
axes.set_xlim(xlim)
axes.set_ylabel('$R_{eff}$ [Mar 8 - Apr 30]')
fig.tight_layout()
plt.savefig('Reff_violin.png')