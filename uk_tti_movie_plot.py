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

if plot_movie:
    nframes = 100 # Set the number of frames
    ndots = 100 # Set the number of dots
    axislim = 5*pl.sqrt(nframes) # Pick axis limits
    dots = pl.zeros((ndots, 2)) # Initialize the dots
    frames = [] # Initialize the frames
    old_dots = sc.dcp(dots) # Copy the dots we just made
    fig = pl.figure(figsize=(10,8)) # Create a new figure
    for i in range(nframes): # Loop over the frames
        dots += pl.randn(ndots, 2) # Move the dots randomly
        color = pl.norm(dots, axis=1) # Set the dot color
        old = pl.array(old_dots) # Turn into an array
        plot1 = pl.scatter(old[:,0], old[:,1], c='k') # Plot old dots in black
        plot2 = pl.scatter(dots[:,0], dots[:,1], c=color) # Note: Frames will be separate in the animation
        pl.xlim((-axislim, axislim)) # Set x-axis limits
        pl.ylim((-axislim, axislim)) # Set y-axis limits
        kwargs = {'transform':pl.gca().transAxes, 'horizontalalignment':'center'} # Set the "title" properties
        title = pl.text(0.5, 1.05, f'Iteration {i+1}/{nframes}', **kwargs) # Unfortunately pl.title() can't be dynamically updated
        pl.xlabel('Latitude') # But static labels are fine
        pl.ylabel('Longitude') # Ditto
        frames.append((plot1, plot2, title)) # Store updated artists
        old_dots = pl.vstack([old_dots, dots]) # Store the new dots as old dots
    sc.savemovie(frames, 'fleeing_dots.mp4', fps=20, quality='high') # Save movie as a high-quality mp4



print('Done.')
sc.toc(T)