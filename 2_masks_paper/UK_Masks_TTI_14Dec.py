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
do_show = 0
verbose = 1
seed    = 1
n_runs = 100
to_plot = sc.objdict({
    'Cumulative diagnoses': ['cum_diagnoses'],
    'Cumulative infections': ['cum_infections'],
    'New infections': ['new_infections'],
    'Daily diagnoses': ['new_diagnoses'],
    'Cumulative deaths': ['cum_deaths'],
    'Cumulative critical': ['cum_critical'],
})

# Define what to run
runoptions = ['quickfit', # Does a quick preliminary calibration. Quick to run, ~30s
              'fullfit',  # Searches over parameters and seeds (10,000 runs) and calculates the mismatch for each. Slow to run: ~1hr
              'finialisefit', # Filters the 10,000 runs from the previous step, selects the best-fitting ones, and runs these
              'scens', # Takes the best-fitting runs and projects these forward under different mask and TTI assumptions
              ]
whattorun = runoptions[1] #Select which of the above to run

# Define scenarios
scenario = ['med_comp','2weekcircuit','3weekcircuit','4weekcircuit','trade-offs'][0] # Set a number to pick a scenario from the available options
tti_scen = ['current', 'optimal_med_comp', 'optimal_med_comp_work'][0] # Ditto

# Filepaths
version   = 'v1'
date      = '2020nov29'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = '../UK_Covid_cases_december12.xlsx'
fig_path  = f'{file_path}_{scenario}.png'
resfolder = 'results'

# Important dates
start_day = '2020-01-21'
end_day = '2021-03-31'
data_end = '2020-12-12' # Final date for calibration


########################################################################
# Create the baseline simulation
########################################################################

def make_sim(seed, beta, scenario=None, end_day=None):

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
#        rel_severe_prob = 1.35,
#        rel_crit_prob = 1.35,  # Scale factor for proportion of severe cases that become critical
#        rel_death_prob = 0.5  # Scale factor for proportion of critical cases that result in death
    )

    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30

    # ADD BETA INTERVENTIONS
    beta_dict = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90, ],
                          '2020-03-16': [1.00, 0.90, 0.80, 0.80, ],
                          '2020-03-23': [1.29, 0.02, 0.20, 0.20, ],
                          '2020-04-30': [1.29, 0.02, 0.20, 0.20, ],
                          '2020-05-15': [1.29, 0.02, 0.20, 0.20, ],
                          '2020-06-01': [1.00, 0.23, 0.30, 0.30, ],
                          '2020-06-15': [1.00, 0.38, 0.30, 0.30, ],
                          '2020-07-22': [1.29, 0.00, 0.40, 0.40, ],
                          '2020-08-01': [1.29, 0.00, 0.40, 0.40, ],
                          '2020-09-02': [1.29, 0.63, 0.50, 0.60, ],
                          '2020-10-01': [1.29, 0.63, 0.50, 0.60, ],
                          '2020-10-16': [1.29, 0.63, 0.60, 0.70, ],
                          '2020-10-26': [1.29, 0.00, 0.60, 0.70, ],
                          '2020-11-01': [1.29, 0.63, 0.60, 0.70, ],
                          '2020-11-05': [1.50, 0.63, 0.40, 0.50, ],
                          '2020-11-14': [1.50, 0.63, 0.40, 0.50, ],
                          '2020-11-21': [1.50, 0.63, 0.40, 0.50, ],
                          '2020-11-30': [1.29, 0.63, 0.40, 0.50, ],
                          '2020-12-03': [1.29, 0.63, 0.40, 0.60, ],
                          '2020-12-23': [1.29, 0.00, 0.40, 0.60, ],
                          '2021-12-27': [1.29, 0.63, 0.40, 0.60, ],
                          '2021-01-10': [1.29, 0.00, 0.40, 0.60, ],
                          '2021-01-20': [1.00, 0.63, 0.40, 0.60, ],
                          '2021-02-17': [1.29, 0.63, 0.40, 0.60, ],
                          '2020-02-28': [1.29, 0.00, 0.40, 0.60, ],
                          '2021-04-01': [1.00, 0.63, 0.60, 0.60, ],
                          '2021-04-17': [1.29, 0.00, 0.50, 0.60, ],
                          '2021-05-31': [1.00, 0.63, 0.50, 0.60, ],
                          '2021-06-04': [1.29, 0.00, 0.50, 0.60, ],
                          '2021-07-20': [1.00, 0.63, 0.50, 0.60, ],
                          '2021-09-01': [1.29, 0.00, 0.50, 0.60, ],
                          '2021-10-30': [1.00, 0.63, 0.50, 0.60, ],
                          '2021-11-10': [1.00, 0.63, 0.50, 0.60, ],
                          '2021-03-31': [1.29, 0.00, 0.50, 0.60]
                          })

    h_beta = cv.change_beta(days=beta_dict.keys(), changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_dict.keys(), changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_dict.keys(), changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_dict.keys(), changes=[c[3] for c in beta_dict.values()], layers='c')

    interventions = [h_beta, w_beta, s_beta, c_beta]

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
    ti_day = sim.day('2021-03-31') #schools interventions end date in December 2021

    s_prob_march = 0.012
    s_prob_april = 0.017
    s_prob_may   = 0.02769
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    s_prob_sept = s_prob_august
    s_prob_oct = s_prob_august
    s_prob_nov = s_prob_august
#    s_prob_sept = 0.05769
#    s_prob_oct = 0.05769
#    s_prob_nov = 0.07769
    t_delay       = 1.0

    iso_vals =  [{k:0.1 for k in 'hswc'}]
    iso_vals1 = [{k:0.1 for k in 'hswc'}]
    iso_vals2 = [{k:0.4 for k in 'hswc'}]
    iso_vals3 = [{k:0.8 for k in 'hswc'}]
    iso_vals4 = [{k:0.8 for k in 'hswc'}]

    #tracing level at 42.35% in June; 47.22% in July, 44.4% in August and 49.6% in Septembre (until 16th Sep)
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_eff_august = 0.44
    t_eff_sep    = 0.50
    t_eff_oct    = 0.55
    t_eff_nov    = 0.60
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    t_probs_august = {k:t_eff_august for k in 'hwsc'}
    t_probs_sep = {k:t_eff_sep for k in 'hwsc'}
    t_probs_oct = {k:t_eff_oct for k in 'hwsc'}
    t_probs_nov = {k:t_eff_nov for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay,sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay, sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0275, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_nov, test_delay=t_delay, sensitivity=0.97),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_august-1),
        cv.contact_tracing(trace_probs=t_probs_august, trace_time=trace_d_1, start_day=tti_day_august, end_day=tti_day_sep-1),
        cv.contact_tracing(trace_probs=t_probs_sep, trace_time=trace_d_1, start_day=tti_day_sep, end_day=tti_day_oct-1),
        cv.contact_tracing(trace_probs=t_probs_oct, trace_time=trace_d_1, start_day=tti_day_oct, end_day=tti_day_nov-1),
        cv.contact_tracing(trace_probs=t_probs_nov, trace_time=trace_d_1, start_day=tti_day_nov),
        cv.dynamic_pars({'iso_factor': {'days': tti_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_oct, 'vals': iso_vals3}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_nov, 'vals': iso_vals4}}),
        #cv.dynamic_pars({'rel_death_prob': {'days': tti_day_august, 'vals': 2.0}}),
        #cv.dynamic_pars({'rel_death_prob': {'days': [tti_day_july, tti_day_sep], 'vals': [0.5, 0.5]}}),
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

    noise = 0.00
    betas = [i / 10000 for i in range(75, 85, 2)]

    # Quick calibration
    if whattorun=='quickfit':
        s0 = make_sim(seed=1, beta=0.008, end_day=data_end)
        sims = []
        for seed in range(6):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sims.append(sim)
        msim = cv.MultiSim(sims)
        msim.run()
        msim.reduce()
        if do_plot:
            msim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=f'uk.png',
                      legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=50)

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
                sims.append(sim)
            msim = cv.MultiSim(sims)
            msim.run()
            fitsummary.append([sim.compute_fit().mismatch for sim in msim.sims])

        sc.saveobj(f'{resfolder}/fitsummary.obj',fitsummary)
