'''
Calibration to UK 2nd wave
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
do_plot = 1
do_save = 1
save_sim = 1
do_show = 0
verbose = 1
seed    = 1
n_runs = 200
to_plot = sc.objdict({
    'Cumulative diagnoses': ['cum_diagnoses'],
    'Cumulative infections': ['cum_infections'],
    'New infections': ['new_infections'],
    'New diagnoses': ['new_diagnoses'],
    'Cumulative hospitalisations': ['cum_severe'],
    'Cumulative deaths': ['cum_deaths'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'fullfit',  # Searches over parameters and seeds (10,000 runs) and calculates the mismatch for each. Slow to run: ~1hr
              'finialisefit', # Filters the 10,000 runs from the previous step, selects the best-fitting ones, and runs these
              'scens' # Runs the 3 scenarios
              ]
whattorun = runoptions[2] #Select which of the above to run

# Filepaths
data_path = '../UK_Covid_cases_january03.xlsx'
resfolder = 'results'

# Important dates
start_day = '2020-01-21'
end_day = '2021-03-31'
data_end = '2021-01-03' # Final date for calibration


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed, beta, calibration=True, scenario=None, future_symp_test=None, end_day=None, verbose=0):

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
        rel_severe_prob = 0.5,
        rel_crit_prob = 2,
#        rel_death_prob=1.5,
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30

    # ADD BETA INTERVENTIONS
    sbv = 0.77
    beta_past  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90, ],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80, ],
                           '2020-03-23': [1.29, 0.02, 0.20, 0.20, ],
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40, ],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50, ],
                           '2020-07-22': [1.29, 0.00, 0.30, 0.50, ],
                           '2020-09-02': [1.00, sbv,  0.60, 0.90, ],
                           '2020-10-26': [1.25, 0.00, 0.60, 0.90, ],
                           '2020-11-01': [1.25, sbv,  0.20, 0.40, ],
                           '2020-12-03': [1.25, sbv,  0.60, 0.90, ],
                           '2020-12-20': [1.25, 0.00, 0.40, 0.90, ],
                           '2020-12-25': [1.50, 0.00, 0.30, 0.90, ],
                           })

    if not calibration:
        if scenario == 'FNL':
            beta_s_jan4, beta_s_jan11, beta_s_jan18 = 0.02, 0.02, 0.02
        elif scenario == 'primaryPNL':
            beta_s_jan4, beta_s_jan11, beta_s_jan18 = sbv/2, sbv/2, sbv
        elif scenario == 'staggeredPNL':
            beta_s_jan4, beta_s_jan11, beta_s_jan18 = sbv/2, 0.45, sbv

        beta_scens = sc.odict({'2021-01-04': [1.00, beta_s_jan4,  0.20, 0.30],
                               '2021-01-11': [1.00, beta_s_jan11, 0.20, 0.30],
                               '2021-01-18': [1.00, beta_s_jan18, 0.20, 0.30],
                               '2021-02-08': [1.00, sbv, 0.50, 0.70],
                               '2021-02-15': [1.00, 0.00, 0.50, 0.70],
                               '2021-02-21': [1.00, 0.00, 0.50, 0.70],
                               '2021-03-01': [1.00, sbv, 0.50, 0.70],
                               '2021-03-20': [1.00, sbv, 0.50, 0.70],
                               '2021-04-01': [1.00, sbv, 0.50, 0.70],
                               '2021-04-17': [1.00, 0.00, 0.50, 0.70]
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
    voc_days   = np.linspace(sim.day('2020-09-01'), sim.day('2021-01-30'), 31)
    voc_prop   = 1/(1+np.exp(-.1*(voc_days-sim.day('2020-11-16')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
    voc_change = voc_prop*1.6 + (1-voc_prop)*1.
    voc_beta = cv.change_beta(days=voc_days,
                              changes=voc_change)

    interventions = [h_beta, w_beta, s_beta, c_beta, voc_beta]

    # ADD TEST AND TRACE INTERVENTIONS
    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sep= sim.day('2020-09-01')
    tti_day_oct= sim.day('2020-10-01')
    tti_day_nov= sim.day('2020-11-01')
    tti_day_dec= sim.day('2020-12-01')
    tti_day_jan= sim.day('2021-01-01')

    s_prob_april = 0.008
    s_prob_may   = 0.03
    s_prob_june = 0.01
    s_prob_july = 0.01
    s_prob_august = 0.01
    tn = 0.09
    s_prob_sep = 0.06
    s_prob_oct = 0.07
    s_prob_nov = 0.09
    s_prob_dec = 0.1
    if future_symp_test is None: future_symp_test = s_prob_dec
    t_delay       = 1.0

    #isolation may-july
    iso_vals = [{k:0.1 for k in 'hswc'}]
    #isolation august-dec
    iso_vals1 = [{k:0.7 for k in 'hswc'}]

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.0075, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sep, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_nov, end_day=tti_day_dec-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_dec, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_dec, end_day=tti_day_jan-1, test_delay=t_delay),
        cv.test_prob(symp_prob=future_symp_test, asymp_prob=0.00075, symp_quar_prob=0.0, start_day=tti_day_jan, test_delay=t_delay),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.5, 'w': 0.5, 'c': 0.05},
                           trace_time={'h': 0, 's': 1, 'w': 2, 'c': 7},
                           start_day='2020-06-01',
                           quar_period=10),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}})]

    # Change death and critical probabilities
#    interventions += [cv.dynamic_pars({'rel_death_prob':{'days':sim.day('2020-07-01'), 'vals':0.6}})]


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

    #betas = [i / 10000 for i in range(72, 77, 1)]

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, beta=0.0077, end_day=data_end, verbose=0.1)
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
            goodseeds = [i for i in range(n_runs) if fitsummary[bn][i] < 275] #351.5=100, 275=10
            sc.blank()
            print('---------------\n')
            print(f'Beta: {beta}, goodseeds: {len(goodseeds)}')
            print('---------------\n')
            if len(goodseeds) > 0:
                s0 = make_sim(seed=1, beta=beta, end_day=data_end, verbose=0.1)
                for seed in goodseeds:
                    sim = s0.copy()
                    sim['rand_seed'] = seed
                    sim.set_seed()
                    sim.label = f"Sim {seed}"
                    sims.append(sim)

        msim = cv.MultiSim(sims)
        msim.run()

        if save_sim:
            msim.reduce()
            msim.save(f'{resfolder}/uk_sim.obj')
        if do_plot:
            msim.reduce()
            msim.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)


    # Run scenarios with best-fitting seeds and parameters
    elif whattorun=='scens':

        scenarios = ['FNL', 'primaryPNL', 'staggeredPNL']

        for scenname in scenarios:

            print('---------------\n')
            print(f'Beginning scenario: {scenname}')
            print('---------------\n')
            sc.blank()
            sims_cur = []
            fitsummary = sc.loadobj(f'{resfolder}/fitsummary.obj')

            for bn, beta in enumerate(betas):
                goodseeds = [i for i in range(n_runs) if fitsummary[bn][i] < 351.5]
                if len(goodseeds) > 0:
                    s_cur = make_sim(1, beta, calibration=False, scenario=scenname, end_day='2021-02-28')
                    for seed in goodseeds:
                        sim_cur = s_cur.copy()
                        sim_cur['rand_seed'] = seed
                        sim_cur.set_seed()
                        sim_cur.label = f"Sim {seed}"
                        sims_cur.append(sim_cur)

            msim_cur = cv.MultiSim(sims_cur)
            msim_cur.run()

            if save_sim:
                msim_cur.save(f'{resfolder}/uk_sim_{scenname}.obj')
            if do_plot:
                msim_cur.reduce()
                msim_cur.plot(to_plot=to_plot, do_save=do_save, do_show=False, fig_path=f'uk_{scenname}_current.png',
                          legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)

            print(f'... completed scenario: {scenname}')


