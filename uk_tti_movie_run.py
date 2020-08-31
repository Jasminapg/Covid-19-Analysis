'''
This file generates the simulations for plotting as a movie. For 2000 sims,
generates a file of about 140 MB.
'''

import numpy as np
import sciris as sc
import covasim as cv

# Check version
cv.check_version('1.5.2')
cv.git_info('covasim_version.json')

def create_sim(test=0.0171, trace=0.47, seed=1):

    start_day = '2020-01-21'
    end_day   = '2021-12-31'
    data_path = 'UK_Covid_cases_august02.xlsx'

    # Set the parameters
    total_pop    = 67.86e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1500
    beta         = 0.00593*1.2

    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}

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
    )

    # Create the baseline simulation
    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 0-10
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 10-20

    #%% Interventions


    # Create the baseline simulation

    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    ti_day = sim.day('2021-12-20') #schools interventions end date in December 2021
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August


    #change parameters here for different schools opening strategies with society opening
    beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-01', '2021-04-17', '2021-05-31', '2021-06-04', '2021-07-20', '2021-09-01', '2021-10-30', '2021-11-10', ti_day]

    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62, 0.80, 0.62]

    # Define the beta changes
    h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')

    #next line to save the intervention
    interventions = [h_beta, w_beta, s_beta, c_beta]


    # Tracing and enhanced testing strategy of symptimatics to change for phase plots
    #testing
    s_prob_march = 0.012
    s_prob_april = 0.012
    s_prob_may   = 0.0165
    s_prob_june = 0.0171
    s_prob_july = 0.0171
    #we want to vary s_prob_august to vary testing level
    s_prob_august = test
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing level at 68% from June; 50% in July
    #we want to vary t_eff_august to vary tracing level
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_eff_august = trace
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    t_probs_august = {k:t_eff_august for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=s_prob_march, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_august-1),
        cv.contact_tracing(trace_probs=t_probs_august, trace_time=trace_d_1, start_day=tti_day_august),
      ]



    # Finally, update the parameters
    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    return sim

if __name__ == '__main__':

    do_save = True

    sims = []

    mintest = 0.0
    maxtest = 0.2
    nsims   = 201
    seeds   = 10

    for test in np.linspace(mintest, maxtest, nsims):
        for seed in range(seeds):
            sim = create_sim(test=test, seed=seed)
            sim.label = f'Test_prob={test}, seed={seed}'
            sims.append(sim)

    msim = cv.MultiSim(sims) # Create using your existing sim as the base
    msim.run() # Run with uncertainty

    if do_save:
        msim.save('uk-tti-movie.msim')

    # Save the key figures
    plot_customizations = dict(
        interval   = 90, # Number of days between tick marks
        dateformat = '%m/%Y', # Date format for ticks
        fig_args   = {'figsize':(14,8)}, # Size of the figure (x and y)
        axis_args  = {'left':0.15}, # Space on left side of plot
        )

    for key in ['new_infections']: # r_eff, cum_deaths, new_infections, cum_diagnoses
        for sim in msim.sims:
            sim.plot_result(key, **plot_customizations)

