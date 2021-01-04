'''
UK scenarios for evaluating effectivness of masks
'''

import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
import matplotlib as mplt

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('2.0.0')
cv.git_info('covasim_version.json')

# Saving and plotting settings
do_plot = 0
do_save = 1
save_sim = 0
do_show = 0
verbose = 1
seed    = 1
n_runs = 200
to_plot = sc.objdict({
    'Cumulative diagnoses': ['cum_diagnoses'],
    'Cumulative infections': ['cum_infections'],
    'New infections': ['new_infections'],
    'Cumulative deaths': ['cum_deaths'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'fullfit',  # Searches over parameters and seeds (10,000 runs) and calculates the mismatch for each. Slow to run: ~1hr
              'finialisefit', # Filters the 10,000 runs from the previous step, selects the best-fitting ones, and runs these
              'scens', # Takes the best-fitting runs and projects these forward under different mask and TTI assumptions
              'tti_sweeps', # Sweeps over future testing/tracing values to create data for heatmaps
              ]
whattorun = runoptions[4] #Select which of the above to run

# Filepaths
data_path = '../UK_Covid_cases_august28.xlsx'
resfolder = 'results'

# Important dates
start_day = '2020-01-21'
end_day = '2021-03-31'
data_end = '2020-08-28' # Final date for calibration


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed, beta, calibration=True, scenario=None, future_symp_test=None, future_t_eff=None, end_day=None, verbose=0):

    # Set the parameters
    total_pop    = 67.86e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1500
    beta         = beta
    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
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
                           '2020-07-22': [1.29, 0.00, 0.425, 0.49, ],
                           })

    if not calibration:
        if scenario == 'masks15':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.765, 1.00, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.63,  0.70, 0.49,  0.35,  0.63,  0.49
        elif scenario == 'masks15_notschools':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.90, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30_notschools':
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.70, 0.49,  0.35,  0.63,  0.49

        beta_scens = sc.odict({'2020-09-02': [1.00, sbv1, wbv1, cbv1],
                               '2020-10-28': [1.00, 0.00, wbv2, cbv2],
                               '2020-11-01': [1.00, sbv1, wbv1, cbv1],
                               '2020-12-23': [1.00, 0.00, wbv2, cbv2],
                               '2021-01-03': [1.00, sbv1, wbv1, cbv1],
                               '2021-02-17': [1.00, 0.00, wbv2, cbv2],
                               '2021-02-21': [1.00, sbv1, wbv1, cbv1],
                               '2021-04-06': [1.00, 0.00, wbv2, cbv2],
                               '2021-04-17': [1.00, sbv2, wbv1, cbv1]
                              })

        beta_dict = sc.mergedicts(beta_past, beta_scens)
    else:
        beta_dict = beta_past

    beta_days = list(beta_dict.keys())
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')

    interventions = [h_beta, w_beta, s_beta, c_beta]

    # ADD TEST AND TRACE INTERVENTIONS
    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep= sim.day('2020-09-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August

    s_prob_april = 0.008
    s_prob_may   = 0.03
    s_prob_june = 0.02
    s_prob_july = 0.02
    s_prob_august = 0.02
    if future_symp_test is None: future_symp_test = s_prob_august
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing level at 42.35% in June; 47.22% in July
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    if future_t_eff is None: future_t_eff = t_eff_july
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    future_t_probs = {k:future_t_eff for k in 'hwsc'}
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
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_sep-1),
        cv.contact_tracing(trace_probs=future_t_probs, trace_time=trace_d_1, start_day=tti_day_sep),
    ]

    # Finally, update the parameters
    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    sim.initialize()

    return sim


########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    betas = [i / 10000 for i in range(72, 77, 1)]

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, beta=0.0075, end_day=data_end)
        sims = []
        for seed in range(6):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        msim.reduce()
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=f'uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)

    # Full parameter/seed search
    elif whattorun=='fullfit':
        fitsummary = []
        for beta in betas:
            sc.blank()
            print('---------------\n')
            print(f'Beta: {beta}... ')
            print('---------------\n')
            s0 = make_sim(seed=1, beta=beta, end_day=data_end)
            sims = []
            for seed in range(n_runs):
                sim = s0.copy()
                sim['rand_seed'] = seed
                sim.set_seed()
                sim.label = f"Sim {seed}"
                sims.append(sim)
            msim = cv.MultiSim(sims)
            msim.run()
            fitsummary.append([sim.compute_fit().mismatch for sim in msim.sims])

        sc.saveobj(f'{resfolder}/fitsummary.obj',fitsummary)

    # Run calibration with best-fitting seeds and parameters
    elif whattorun=='finialisefit':
        sims = []
        fitsummary = sc.loadobj(f'{resfolder}/fitsummary.obj')
        for bn, beta in enumerate(betas):
            goodseeds = [i for i in range(n_runs) if fitsummary[bn][i] < 163]
            sc.blank()
            print('---------------\n')
            print(f'Beta: {beta}, goodseeds: {len(goodseeds)}')
            print('---------------\n')
            if len(goodseeds) > 0:
                s0 = make_sim(seed=1, beta=beta, end_day=data_end)
                for seed in goodseeds:
                    sim = s0.copy()
                    sim['rand_seed'] = seed
                    sim.set_seed()
                    sim.label = f"Sim {seed}"
                    sims.append(sim)

#        msim = cv.MultiSim(sims)
#        msim.run()

#        if save_sim:
#            msim.save(f'{resfolder}/uk_sim.obj')
#        if do_plot:
#            msim.reduce()
#            msim.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk.png',
#                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)


    # Run scenarios with best-fitting seeds and parameters
    elif whattorun=='scens':

        # Define scenario to run
        scenarios = sc.odict({'masks15': 0.15,
                              'masks30': 0.07,
                              'masks15_notschools': 0.17,
                              'masks30_notschools': 0.095})

        for scenname, future_symp_test in scenarios.iteritems():

            print('---------------\n')
            print(f'Beginning scenario: {scenname}')
            print('---------------\n')
            sc.blank()
            sims_cur, sims_opt = [], []
            fitsummary = sc.loadobj(f'{resfolder}/fitsummary.obj')

            for bn, beta in enumerate(betas):
                goodseeds = [i for i in range(n_runs) if fitsummary[bn][i] < 163]
                if len(goodseeds) > 0:
                    s_cur = make_sim(1, beta, calibration=False, scenario=scenname, future_symp_test=None, end_day='2021-12-31')
                    s_opt = make_sim(1, beta, calibration=False, scenario=scenname, future_symp_test=future_symp_test, end_day='2021-12-31')
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
                msim_cur.reduce()
                msim_cur.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_optimal.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)

            print(f'... completed scenario: {scenname}')


    # Run scenarios with best-fitting seeds and parameters
    elif whattorun=='tti_sweeps':

        symp_test_vals = np.linspace(0, 1, 21)
        trace_eff_vals = np.linspace(0, 1, 21)
        scenarios = ['masks30_notschools','masks15','masks30','masks15_notschools']

        # Define scenario to run
        for scenname in scenarios:
            sweep_summary = {'cum_inf':[],'peak_inf':[],'cum_death':[]}
            for future_symp_test in symp_test_vals:
                daily_test = np.round(1 - (1 - future_symp_test) ** (1 / 10), 3) if future_symp_test<1 else 0.4
                cum_inf, peak_inf, cum_death = [], [], []
                for future_t_eff in trace_eff_vals:

                    sc.blank()
                    print('---------------')
                    print(f'Scenario: {scenname}, testing: {future_symp_test}, tracing: {future_t_eff}')
                    print('--------------- ')
                    sims = []
                    fitsummary = sc.loadobj(f'{resfolder}/fitsummary.obj')

                    for bn, beta in enumerate(betas):
                        goodseeds = [i for i in range(n_runs) if fitsummary[bn][i] < 125.5] # Take the best 10
                        if len(goodseeds) > 0:
                            s0 = make_sim(1, beta, calibration=False, scenario=scenname, future_symp_test=daily_test, future_t_eff=future_t_eff, end_day='2021-12-31')
                            for seed in goodseeds:
                                sim = s0.copy()
                                sim['rand_seed'] = seed
                                sim.set_seed()
                                sim.label = f"Sim {seed}"
                                sims.append(sim)

                    msim = cv.MultiSim(sims)
                    msim.run(verbose=-1)
                    msim.reduce()

                    # Store results
                    data_end_day = msim.sims[0].day(data_end)

                    cum_inf.append(msim.results['cum_infections'].values[-1])
                    peak_inf.append(max(msim.results['new_infections'].values[data_end_day:]))
                    cum_death.append(msim.results['cum_deaths'].values[-1])

                sweep_summary['cum_inf'].append(cum_inf)
                sweep_summary['peak_inf'].append(peak_inf)
                sweep_summary['cum_death'].append(cum_death)

            sc.saveobj(f'{resfolder}/uk_tti_sweeps_{scenname}.obj', sweep_summary)
