'''
UK scenarios for evaluating effectivness of masks
'''

import os
import shutil
import sciris as sc
import covasim as cv
import numpy as np

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('2.0.2')
cv.git_info('covasim_version.json')

# Saving and plotting settings
debug = 0 # Whether to do a small debug run (for sweeps)
do_plot = 1
do_save = 1
save_sim = 1
do_show = 0
verbose = 1
seed    = 1
to_plot = sc.objdict({
    'Cumulative diagnoses': ['cum_diagnoses'],
    'Cumulative infections': ['cum_infections'],
    'New infections': ['new_infections'],
    'Cumulative deaths': ['cum_deaths'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'fullfit', # Sweeps over many seeds to find the best fitting ones
              'finalisefit', # Processes the results of the previous step to produce a calibration with the best seeds
              'scens', # Takes the best-fitting runs and projects these forward under different mask and TTI assumptions
              'tti_sweeps', # Sweeps over future testing/tracing values to create data for heatmaps
              ]
whattorun = runoptions[-1] #Select which of the above to run

# Filepaths
data_path = 'UK_Covid_cases_august28.xlsx'
resfolder = 'results'
cachefolder = 'cache'

# Important dates
start_day = '2020-01-21'
end_day = '2021-03-31'
data_end = '2020-08-28' # Final date for calibration
day_before_scens = '2020-08-31'


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed=None, calibration=True, scenario=None, future_symp_test=None, future_t_eff=None, end_day=None, verbose=0, meta=None):

    print(f'Making sim {meta.inds} ({meta.count} of {meta.n_sims})...')

    # Set the parameters
    beta         = 0.00748 # Calibrated value
    total_pop    = 67.86e6 # UK population size
    pop_size     = [100e3, 5e3][debug] # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1500
    beta         = beta
    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
    # beta_layer   = {'h':3.0, 's':1.0, 'w':0.6, 'c':0.3}
    if end_day is None: end_day = '2021-03-31'

    pars = sc.objdict(
        pop_size     = pop_size,
        pop_infected = pop_infected,
        pop_scale    = pop_scale,
        pop_type     = pop_type,
        start_day    = start_day,
        end_day      = end_day,
        beta         = beta,
        asymp_factor = asymp_factor,
        contacts     = contacts,
        rescale      = True,
        rand_seed    = seed,
        verbose      = verbose,
        #rel_severe_prob = 0.4,
        #rel_crit_prob = 2.3,
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30

    # ADD BETA INTERVENTIONS
    beta_past  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90, ],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80, ],
                           '2020-03-23': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-04-30': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-05-15': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40, ],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50, ],
                           '2020-07-22': [1.29, 0.00, 0.30, 0.50, ],
                           '2020-08-22': [1.29, 0.00, 0.30, 0.50, ]
                           })

    if not calibration:
        if scenario == 'masks15':
            sbv, wbv, cbv = 0.765, 0.595, 0.765
        elif scenario == 'masks30':
            sbv, wbv, cbv = 0.63,  0.49,  0.63
        elif scenario == 'masks15_notschools':
            sbv, wbv, cbv = 0.90,  0.595, 0.765
        elif scenario == 'masks30_notschools':
            sbv, wbv, cbv = 0.90,  0.49,  0.63

        beta_scens = sc.odict({'2020-09-02': [1.25, sbv, wbv, cbv],
                              })

        beta_dict = sc.mergedicts(beta_past, beta_scens)
    else:
        beta_dict = beta_past

    beta_days = list(beta_dict.keys())
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')

    # Add a new change in beta to represent the takeover of the novel variant VOC 202012/01
    # Assume that the new variant is 60% more transmisible (https://cmmid.github.io/topics/covid19/uk-novel-variant.html,
    # Assume that between Nov 1 and Jan 30, the new variant grows from 0-100% of cases
#    voc_days   = np.linspace(sim.day('2020-08-01'), sim.day('2021-01-30'), 31)
#    voc_prop   = 0.6/(1+np.exp(-0.075*(voc_days-sim.day('2020-09-30')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
#    voc_change = voc_prop*1.63 + (1-voc_prop)*1.
#    voc_beta = cv.change_beta(days=voc_days,
#                              changes=voc_change)

    interventions = [h_beta, w_beta, s_beta, c_beta] #, voc_beta]


    # ADD TEST AND TRACE INTERVENTIONS
    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep= sim.day('2020-09-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August

    s_prob_april = 0.009
    s_prob_may   = 0.017
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769

    #s_prob_april = 0.008
    #s_prob_may   = 0.03
    #s_prob_june = 0.02
    #s_prob_july = 0.02
    #s_prob_august = 0.02
    if future_symp_test is None: future_symp_test = s_prob_august
    t_delay       = 1.0

    #isolation may-july
    iso_vals = [{k:0.7 for k in 'hswc'}]
    #isolation august
    iso_vals1 = [{k:0.7 for k in 'hswc'}]
    #isolation september
    iso_vals2 = [{k:0.7 for k in 'hswc'}]

    t_probs_junejuly = {'h': 1, 's': 0.5, 'w': 0.5, 'c': 0.05}
    if future_t_eff is None: future_t_eff = 0.5
    future_t_probs = {'h': 1, 's': future_t_eff, 'w': future_t_eff, 'c': 0.05}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.0075, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=future_symp_test, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_sep, test_delay=t_delay),
        cv.contact_tracing(trace_probs=t_probs_junejuly, trace_time=trace_d_1, start_day='2020-06-01', end_day='2020-08-31', quar_period=10),
        cv.contact_tracing(trace_probs=future_t_probs, trace_time=trace_d_1, start_day=tti_day_sep),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
    ]

    # Finally, update the parameters
    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    # Store metadata
    sim.meta = meta

    return sim


def try_loading_cached_sim(sim, cachefile, statusfile, do_load):
    ''' Load the sim from file, or at least try '''

    # Assign these to variables to prevent accidental changes!
    success = 'success'
    failed = 'failed'

    if os.path.isfile(statusfile):
        status = sc.loadtext(statusfile)
    else:
        status = 'not yet run'

    sim_loaded = False
    if do_load and os.path.isfile(cachefile) and failed not in status:
        try:
            sim_orig = sim.copy()
            sim = cv.Sim.load(cachefile)
            sim.meta = sim_orig.meta
            sim['interventions'] = sim_orig['interventions']
            for interv in sim['interventions']:
                interv.initialize(sim)
            if status != success: # Update the status to note success
                sc.savetext(statusfile, success)
            sim_loaded = True
        except Exception as E:
            errormsg = f'WARNING, {failed} to load cached sim from {cachefile}! Reason: {str(E)}'
            print(errormsg)
            sc.savetext(statusfile, errormsg)

    return sim, sim_loaded


def save_cached_sim(sim, cachefile, statusfile, do_save):
    ''' Save the sim to disk '''

    if do_save:
        print(f'Saving cache file to {cachefile}')
        sim.save(cachefile, keep_people=True)
        sc.savetext(statusfile, 'saved but not yet loaded')

    return


def run_sim(sim, do_load=True, do_save=True, do_shrink=True):
    ''' Run a simulation, loading from cache if possible '''

    # Caching -- WARNING, needs testing!
    seed = sim.meta.vals.seed
    cachefile = f'{cachefolder}/cached_sim{seed}.sim' # File to save the partially run sim to
    statusfile = f'{cachefolder}/status{seed}.tmp'
    sim, sim_loaded = try_loading_cached_sim(sim, cachefile, statusfile, do_load)
    loadstr = 'loaded from cache :)' if sim_loaded else 'could not load from cache'

    print(f'Running sim {sim.meta.count:5g} of {sim.meta.n_sims:5g} {str(sim.meta.vals.values()):40s} -- {loadstr}')
    if not sim_loaded:
        sim.run(until=day_before_scens) # If not loaded, run the partial sim
        save_cached_sim(sim, cachefile, statusfile, do_save) # Save (optionally)

    # Actually run the (rest of the) sim
    sim.run()

    if do_shrink:
        sim.shrink()

    return sim


def make_msims(sims):
    ''' Take a slice of sims and turn it into a multisim '''
    msim = cv.MultiSim(sims)
    msim.reduce()
    i_sc, i_fst, i_fte, i_s = sims[0].meta.inds
    msim.meta = sc.objdict()
    msim.meta.inds = [i_sc, i_fst, i_fte]

    if save_sim: # NB, generates ~2 GB of files for a full run
        id_str = '_'.join([str(i) for i in msim.meta.inds])
        msimfile = f'{cachefolder}/final_msim{id_str}.msim' # File to save the partially run sim to
        msim.save(msimfile)

    return msim


########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, end_day='2020-09-10', verbose=0.1)
        sims = []
        for seed in range(30):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        msim.reduce(quantiles = [0.10,0.90])
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path='Masks.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)


    # Full parameter/seed search
    elif whattorun == 'fullfit':

        n_runs = 3000

        fitsummary = []
        s0 = make_sim(seed=1, end_day='2020-08-25', verbose=-1)
        sims = []
        for seed in range(n_runs):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
#        msim.run(par_args={'n_cpus':24})

        # Figure out the seeds that give a good fit
        mismatches = np.array([sim.compute_fit().mismatch for sim in msim.sims])
        threshold = np.quantile(mismatches, 0.01) # Take the best 1%
        goodseeds = [i for i in range(len(mismatches)) if mismatches[i] < threshold]
        cv.save(f'{resfolder}/goodseeds.obj',goodseeds)


    # Run calibration with best-fitting seeds and parameters
    elif whattorun=='finalisefit':
        goodseeds = cv.load(f'{resfolder}/goodseeds.obj')
        s0 = make_sim(seed=1, end_day='2020-08-25', verbose=-1)
        sims = []
        for seed in goodseeds:
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()

        if save_sim:
            msim.save(f'{resfolder}/uk_sim.obj')
        if do_plot:
            msim.reduce()
            msim.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path='uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)


    # Run scenarios with best-fitting seeds and parameters
    elif whattorun=='scens':

        goodseeds = cv.load(f'{resfolder}/goodseeds.obj')

        # Define scenario to run
        scenarios = sc.odict({
            'masks15': 0.15,
            'masks30': 0.07,
            'masks15_notschools': 0.17,
            'masks30_notschools': 0.095
        })

        for scenname, future_symp_test in scenarios.iteritems():

            print('---------------\n')
            print(f'Beginning scenario: {scenname}')
            print('---------------\n')
            sc.blank()
            sims_cur, sims_opt = [], []
            s_cur = make_sim(seed=1, calibration=False, scenario=scenname, future_symp_test=None, end_day='2020-10-23', verbose=0.1)
            s_opt = make_sim(seed=1, calibration=False, scenario=scenname, future_symp_test=future_symp_test, end_day='2020-10-23', verbose=0.1)
            for seed in goodseeds:
                sim_cur = s_cur.copy()
                sim_cur['rand_seed'] = seed
                sim_cur.set_seed()
                sim_cur.label = f"Sim {seed}"
                sims_cur.append(sim_cur)
                sim_opt = s_opt.copy()
                sim_opt['rand_seed'] = seed
                sim_opt.set_seed()
                sim_opt.label = f"Sim {seed}"
                sims_opt.append(sim_opt)

            msim_cur = cv.MultiSim(sims_cur)
            msim_cur.run()
            msim_opt = cv.MultiSim(sims_opt)
            msim_opt.run()

            if save_sim:
                msim_cur.save(f'{resfolder}/uk_sim_{scenname}_current.obj')
                msim_opt.save(f'{resfolder}/uk_sim_{scenname}_optimal.obj')
            if do_plot:
                msim_cur.reduce()
                msim_cur.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_current.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)
                msim_opt.reduce()
                msim_opt.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_optimal.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)

            print(f'... completed scenario: {scenname}')


    # Run scenarios with best-fitting seeds and parameters
    elif whattorun=='tti_sweeps':

        do_load = False # Whether to load files from cache, if available
        do_save = False # Whether to save files to cache, if rerun
        npts = [41, 3][debug]
        max_seeds = [10, 4][debug]
        symp_test_vals = np.linspace(0, 1, npts)
        trace_eff_vals = np.linspace(0, 1, npts)
        scenarios = ['masks30','masks30_notschools','masks15','masks15_notschools']
        n_scenarios = len(scenarios)
        goodseeds = cv.load(f'{resfolder}/goodseeds.obj')[:max_seeds]
        sims_file = f'{cachefolder}/all_sims.obj'
        T = sc.tic()

        # Optionally remove the cache folder
        if do_load and os.path.exists(cachefolder):
            response = input(f'Do you want to delete the cache folder "{os.path.abspath(cachefolder)}" before starting? y/[n] ')
            if response in ['y', 'yes', 'Yes']:
                print(f'Deleting "{cachefolder}"...')
                shutil.rmtree(cachefolder)
            else:
                print(f'OK, not deleting "{cachefolder}" -- you were warned!')
            sc.timedsleep(2) # Wait for a moment so messages can be seen

        # Make sims
        sc.heading('Making sims...')
        if os.path.isfile(sims_file) and do_load: # Don't run, just load
            sim_configs = cv.load(sims_file)
        else:
            n_sims = n_scenarios*npts**2*max_seeds
            count = 0
            ikw = []
            for i_sc,scenname in enumerate(scenarios):
                for i_fst,future_symp_test in enumerate(symp_test_vals):
                    print(f'Creating arguments for sim {count} of {n_sims}...')
                    daily_test = np.round(1 - (1 - future_symp_test) ** (1 / 10), 3) if future_symp_test<1 else 0.4
                    for i_fte,future_t_eff in enumerate(trace_eff_vals):
                        for i_s,seed in enumerate(goodseeds):
                            count += 1
                            meta = sc.objdict()
                            meta.count = count
                            meta.n_sims = n_sims
                            meta.inds = [i_sc, i_fst, i_fte, i_s]
                            meta.vals = sc.objdict(seed=seed, scenario=scenname, future_symp_test=daily_test, future_t_eff=future_t_eff)
                            ikw.append(sc.dcp(meta.vals))
                            ikw[-1].meta = meta

            # Actually run the sims
            kwargs = dict(calibration=False, end_day='2020-10-23')
            sim_configs = sc.parallelize(make_sim, iterkwargs=ikw, kwargs=kwargs)
            if do_save:
                cv.save(filename=sims_file, obj=sim_configs)

        # Run sims
        all_sims = sc.parallelize(run_sim, iterarg=sim_configs, kwargs=dict(do_load=do_load, do_save=do_save))
        sims = np.empty((n_scenarios, npts, npts, max_seeds), dtype=object)
        for sim in all_sims: # Unflatten array
            i_sc, i_fst, i_fte, i_s = sim.meta.inds
            sims[i_sc, i_fst, i_fte, i_s] = sim

        # Convert to msims
        all_sims_semi_flat = []
        for i_sc in range(n_scenarios):
            for i_fst in range(npts):
                for i_fte in range(npts):
                    sim_seeds = sims[i_sc, i_fst, i_fte, :].tolist()
                    all_sims_semi_flat.append(sim_seeds)
        msims = np.empty((n_scenarios, npts, npts), dtype=object)
        all_msims = sc.parallelize(make_msims, iterarg=all_sims_semi_flat)
        for msim in all_msims: # Unflatten array
            i_sc, i_fst, i_fte = msim.meta.inds
            msims[i_sc, i_fst, i_fte] = msim

        # Do processing and store results
        for i_sc,scenname in enumerate(scenarios):
            sweep_summary = {'cum_inf':[],'peak_inf':[],'cum_death':[]}
            for i_fst,future_symp_test in enumerate(symp_test_vals):
                cum_inf, peak_inf, cum_death = [], [], []
                for i_fte,future_t_eff in enumerate(trace_eff_vals):
                    msim = msims[i_sc, i_fst, i_fte]
                    data_end_day = msim.sims[0].day(data_end)
                    cum_inf.append(msim.results['cum_infections'].values[-1]-msim.results['cum_infections'].values[data_end_day])
                    peak_inf.append(max(msim.results['new_infections'].values[data_end_day:]))
                    cum_death.append(msim.results['cum_deaths'].values[-1]-msim.results['cum_deaths'].values[data_end_day])

                sweep_summary['cum_inf'].append(cum_inf)
                sweep_summary['peak_inf'].append(peak_inf)
                sweep_summary['cum_death'].append(cum_death)

            if not debug:
                cv.save(f'{resfolder}/uk_tti_sweeps_{scenname}.obj', sweep_summary)
        sc.toc(T)


