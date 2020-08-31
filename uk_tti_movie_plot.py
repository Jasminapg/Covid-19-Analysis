import numpy as np
import pylab   as pl
import sciris  as sc
import covasim as cv

fn = 'uk-tti-movie.msim'
nsims   = 10
seeds   = 10
plot_diagnostic = False
plot_movie = True
n_total = nsims*seeds

T = sc.tic()

msim = cv.load(fn)
s0 = msim.sims[0]

results = np.zeros((nsims, seeds, s0.npts))
count = -1
for i in range(nsims):
    for j in range(seeds):
        count += 1
        vals = msim.sims[count].results['new_infections'].values
        results[i,j,:] = vals

print('Plotting...')
if plot_diagnostic:
    fig = pl.figure(figsize=(26,18))
    for i in range(nsims):
        pl.subplot(nsims//2, 2, i+1)
        data = results[i,:,:]
        for j in range(seeds):
            pl.plot(s0.tvec, results[i,j,:])

xlims = [s0.tvec[0], s0.tvec[-1]]
ylims = [0, results.max()]

mintest = 0.0
maxtest = 0.2
test_vals = np.linspace(mintest, maxtest, nsims) # TODO: remove duplication

if plot_movie:
    fig = pl.figure(figsize=(10,8)) # Create a new figure
    frames = [] # Initialize the frames
    for i in range(nsims): # Loop over the frames
        handles = []
        for j in range(seeds):
            plt = pl.plot(s0.tvec, results[i,j,:])
            handles.append(plt)
        pl.xlim(xlims) # Set x-axis limits
        pl.ylim(ylims) # Set y-axis limits
        test_pct = test_vals[i]*100
        kwargs = {'transform':pl.gca().transAxes, 'horizontalalignment':'center'} # Set the "title" properties
        title = pl.text(0.5, 1.05, f'Testing rate: {test_pct:0.1f}%', **kwargs) # Unfortunately pl.title() can't be dynamically updated
        handles.append(title)
        pl.xlabel('Date')
        pl.ylabel('New infections')
        frames.append(handles) # Store updated artists
    sc.savemovie(frames, 'uk_tti_movie.mp4', fps=3, quality='high') # Save movie as a high-quality mp4



print('Done.')
sc.toc(T)