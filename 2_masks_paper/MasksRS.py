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
    'Cumulative deaths': ['cum_deaths'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'fullfit',  # Searches over parameters and seeds (10,000 runs) and calculates the mismatch for each. Slow to run: ~1hr
              'finialisefit', # Filters the 10,000 runs from the previous step, selects the best-fitting ones, and runs these
              'scens', # Takes the best-fitting runs and projects these forward under different mask and TTI assumptions
              'tti_sweeps', # Sweeps over future testing/tracing values to create data for heatmaps
              ]
whattorun = runoptions[0] #Select which of the above to run

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

def make_sim(seed, beta, calibration=True, scenario=None, delta_beta=1.6, future_symp_test=None, future_t_eff=None, end_day=None, verbose=0):

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
        rel_severe_prob = 0.4,
        rel_crit_prob = 2.3,
        #rel_death_prob=1.5,
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30

    # ADD BETA INTERVENTIONS
    beta_past  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80],
                           '2020-03-23': [1.29, 0.02, 0.20, 0.20],
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50],
                           '2020-07-22': [1.29, 0.00, 0.30, 0.50],
                           })

    if not calibration:
        if scenario == 'masks15': # COUNTERFACTUAL 1: if masks had been used but were less effective
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.765, 0.90, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30': # BASELINE, i.e., what happened in reality
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.63,  0.90, 0.49,  0.35,  0.63,  0.49
        elif scenario == 'masks15_notschools': # COUNTERFACTUAL 2: if masks were less effective and were not in schools
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.90, 0.595, 0.425, 0.765, 0.595
        elif scenario == 'masks30_notschools': # COUNTERFACTUAL: if masks were not used in schools
            sbv1, sbv2, wbv1, wbv2, cbv1, cbv2 = 0.90,  0.90, 0.49,  0.35,  0.63,  0.49

        beta_scens = sc.odict({'2020-09-02': [1.25, sbv1, wbv1, cbv1], #BASELINE: 1.25, 0.63, 0.49, 0.63
                               '2020-10-28': [1.25, 0.00, wbv2, cbv2],
                               '2020-11-01': [1.25, sbv1, wbv1, cbv1],
                               '2020-12-23': [1.25, 0.00, wbv2, cbv2],
                               '2021-01-03': [1.25, sbv1, wbv1, cbv1],
                               '2021-02-17': [1.25, 0.00, wbv2, cbv2],
                               '2021-02-21': [1.25, sbv1, wbv1, cbv1],
                               '2021-04-06': [1.25, 0.00, wbv2, cbv2],
                               '2021-04-19': [1.25, sbv2, wbv1, cbv1]
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
    voc_days   = np.linspace(sim.day('2020-08-01'), sim.day('2021-01-30'), 31)
    voc_prop   = 0.6/(1+np.exp(-0.075*(voc_days-sim.day('2020-09-30')))) # Use a logistic growth function to approximate fig 2A of https://cmmid.github.io/topics/covid19/uk-novel-variant.html
    voc_change = voc_prop*1.63 + (1-voc_prop)*1.
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
    tti_day_vac= sim.day('2020-12-20')

    tn = 0.09
    s_prob_april = 0.009
    s_prob_may   = 0.02769
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.03769
    s_prob_sep = 0.08769
    s_prob_oct = 0.08769
    s_prob_nov = 0.08769
    s_prob_dec = 0.08769

    if future_symp_test is None: future_symp_test = s_prob_dec
    t_delay       = 1.0

    #isolation may-july
    iso_vals = [{k:0.1 for k in 'hswc'}]
    #isolation august
    iso_vals1 = [{k:0.7 for k in 'hswc'}]
    #isolation september
    iso_vals2 = [{k:0.5 for k in 'hswc'}]
    #isolation october
    iso_vals3 = [{k:0.5 for k in 'hswc'}]
    #isolation november
    iso_vals4 = [{k:0.5 for k in 'hswc'}]
     #isolation december
    iso_vals5 = [{k:0.5 for k in 'hswc'}]


    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.0075, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sep, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_nov, end_day=tti_day_dec-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_dec, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_dec, end_day=tti_day_jan-1, test_delay=t_delay),
        cv.test_prob(symp_prob=future_symp_test, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_jan, test_delay=t_delay),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.5, 'w': 0.5, 'c': 0.05},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2020-06-01',
                           quar_period=10),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_oct, 'vals': iso_vals3}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_nov, 'vals': iso_vals4}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_dec, 'vals': iso_vals5}})]
        #cv.dynamic_pars({'rel_death_prob': {'days': tti_day_vac, 'vals': 0.9}})]
        #cv.vaccine(days=[0,14], rel_sus=0.4, rel_symp=0.2, cumulative=[0.7, 0.3])]    


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
        s0 = make_sim(seed=1, beta=0.00748, end_day='2020-09-30', verbose=0.1)
        sims = []
        for seed in range(30):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        msim.reduce(quantiles = [0.1,0.90])
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=f'Masks.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50, n_cols=2)

