'''
UK scenarios for evaluating effectivness of masks
'''

import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--test", type=float, default=0.0171, help="testing rate")
parser.add_argument("--trace", type=float, default=0.47, help="tracing rate")
parser.add_argument("--scenario", default="no_masks", help="contact scenario")
parser.add_argument("--tti", default="test-trace", help="tti scenario")
parser.add_argument("--ec", type=float, default=None, help="effective coverage of masks (overrides scenario)")
parser.add_argument("-a", type=float, default=None, help="degree of workplace opening (overrides scenario)")
parser.add_argument("-b", type=float, default=None, help="degree of general community opening (overrides scenario)")
parser.add_argument("--samples", type=int, default=12, help="number of samples")

pl.switch_backend('agg')

# Check version
cv.check_version('1.5.2')
cv.git_info('covasim_version.json')

do_plot = 1
do_save = 1
do_show = 1
verbose = 1
seed    = 1

## define our list of background and tti scenarios
scenarios     = ['no_masks', 'low_comp', 'med_comp', 'high_comp', 'low_comp_notschools', 'med_comp_notschools', 'high_comp_notschools']
tti_scenarios = ['current', 'test-trace']

version   = 'v1'
date      = '2020june17'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_august02.xlsx'

start_day = '2020-01-21'
end_day   = '2021-12-31'

# Set the parameters
total_pop    = 67.86e6 # UK population size
pop_size     = 100e3 # Actual simulated population
pop_scale    = int(total_pop/pop_size)
pop_type     = 'hybrid'
#kids infectiousness the same as adults
#model fitted using optuna to find pop_infected and beta and s_prob_X for months we have data
pop_infected = 1500
beta         = 0.0071967
quar_factor = dict(h=0.7, s=0.0, w=0.2, c=0.2)

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
)

def scenario_beta_changes(sim, args):
    """
    Return sets of changes in beta for different scenarios. Args is command line arguments.
    """
    scenario = args.scenario

    #change parameters here for different schools opening strategies with society opening
    ti_day = sim.day('2021-12-20') #schools interventions end date in December 2021
    beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-08-01', '2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-01', '2021-04-17', '2021-05-31', '2021-06-04', '2021-07-20', '2021-09-01', '2021-10-30', '2021-11-10', ti_day]

    ###no masks and assuming schools go back to 90%; workplaces to 50% and community to 70% of pre-COVID level
    ###calibarted until 28th August 2020
    if scenario == 'no_masks':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00]
        ec, a, b = 0.0, 0.5, 0.7
    
    # Low EC of masks in community and schools
    # Community contacts reduction by 15% means 60% of normal during termtime and 51% during holidays from 24th July 
    # Schools contacts reduction by 15% means 77% of normal during termtime from 1st Sep
    # masks in secondary schools from 1st September
    elif scenario == 'low_comp':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00, 0.77, 0.00]
        ec, a, b = 0.15, 0.5, 0.7
 
    # moderate EC of masks in community and schools
    # Community contacts reduction by 30% means 49% of normal during termtime and 42% during holidays from 24th Jul
    # Schools contacts reduction by 30% means 63% of normal during termtime from 1st Sep
    # masks in secondary schools from 1st September
    elif scenario == 'med_comp':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00]
        ec, a, b = 0.30, 0.5, 0.7
 
    # high EC of masks in community and schools
    # Community contacts reduction by 50% means 35% of normal during termtime and 30% during holidays from 24th Jul
    # Schools contacts reduction by 50% means 45% of normal during termtime from 1st Sep
    # masks in secondary schools from 1st September
    elif scenario == 'high_comp':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00, 0.45, 0.00]
        ec, a, b = 0.50, 0.5, 0.7
    
    # Low EC of masks in community and schools
    # Community contacts reduction by 15% means 60% of normal during termtime and 51% during holidays from 24th July 
    # masks NOT in secondary schools from 1st September
    elif scenario == 'low_comp_notschools':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00]
        ec, a, b = 0.15, 0.5, 0.7
 
    # moderate EC of masks in community and schools
    # Community contacts reduction by 30% means 49% of normal during termtime and 42% during holidays from 24th Jul
    # masks NOT in secondary schools from 1st September
    elif scenario == 'med_comp_notschools':
    ### Community contacts reduction by 30% means 63% of normal during termtime and 53% during holidays from 24th Jul
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00]
        ec, a, b = 0.3, 0.5, 0.7
    
    # high EC of masks in community and schools
    # Community contacts reduction by 50% means 35% of normal during termtime and 30% during holidays from 24th July
    # masks in secondary schools from 1st September
    elif scenario == 'high_comp_notschools':
        h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29]
        s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00]
        ec, a, b = 0.5, 0.5, 0.7
    
    else:
        raise ValueError(f'Scenario {scenario} not recognised')

    if args.ec is not None: ec = args.ec
    if args.a is not None: a = args.a
    if args.b is not None: b = args.b

    ## w and c changes parametrised by "effective coverage" as well as degree of workplace opening, a, and degree of general community opening, b.
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, a, a-0.1, a, a-0.1, a, a-0.1, a, a-0.1, a, a-0.1, a, a-0.1, a, a-0.1, a, a-0.1]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.425, (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1), (1-ec)*b, (1-ec)*(b-0.1)]

    # Define the beta changes
    h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')

    #next line to save the intervention
    interventions = [h_beta, w_beta, s_beta, c_beta]

    return beta_days, h_beta_changes, s_beta_changes, w_beta_changes, c_beta_changes, interventions

def tracing_interventions(sim, args):
    tti_scen = args.tti

    tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
    te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
    tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
    tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
    tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
    tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
    tti_day_sept= sim.day('2020-09-01')

    if tti_scen == 'current':
    
        # Tracing and enhanced testing strategy of symptimatics from 1st June
        #testing in June remains the same as before June under this scenario
        s_prob_march = 0.009
        s_prob_april = 0.013
        s_prob_may   = 0.026
        s_prob_june = 0.02769
        s_prob_july = 0.02769
        s_prob_august = 0.02769
        s_prob_sept = 0.02769
        t_delay       = 1.0
    
        iso_vals = [{k:0.1 for k in 'hswc'}]
    
        #tracing level at 42.35% in June; 47.22% in July
        t_eff_june   = 0.42
        t_eff_july   = 0.47
        t_eff_august = 0.47
        t_eff_sept   = 0.47
        t_probs_june = {k:t_eff_june for k in 'hwsc'}
        t_probs_july = {k:t_eff_july for k in 'hwsc'}
        t_probs_august = {k:t_eff_august for k in 'hwsc'}
        t_probs_sep = {k:t_eff_sept for k in 'hwsc'}
        trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}
    
        #testing and isolation intervention
        interventions = [
            cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, test_delay=t_delay),
            cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
            cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
            cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_august-1),
            cv.contact_tracing(trace_probs=t_probs_august, trace_time=trace_d_1, start_day=tti_day_august, end_day=tti_day_sept-1),
            cv.contact_tracing(trace_probs=t_probs_sept, trace_time=trace_d_1, start_day=tti_day_sept),
          ]
        
        
    elif tti_scen == 'test-trace':
    
    # Tracing and enhanced testing strategy of symptimatics to change for phase plots
        #Phase plots=need to change s_prob_august and t_eff_august and plot R, new infections, deaths and diagnosis for different combinations of s_prob_august and t_eff_august
        
        #testing
        
        s_prob_march = 0.009
        s_prob_april = 0.013
        s_prob_may   = 0.026
        s_prob_june = 0.02769
        s_prob_july = 0.02769
        s_prob_august = 0.02769
        s_prob_sept = args.test
        t_delay       = 1.0
    
        iso_vals = [{k:0.1 for k in 'hswc'}]
    
        #tracing level at 42.35% in June; 47.22% in July
        t_eff_june   = 0.42
        t_eff_july   = 0.47
        t_eff_august = 0.47
        t_eff_sept = args.trace
        t_probs_june = {k:t_eff_june for k in 'hwsc'}
        t_probs_july = {k:t_eff_july for k in 'hwsc'}
        t_probs_august = {k:t_eff_august for k in 'hwsc'}
        t_probs_sept = {k:t_eff_sept for k in 'hwsc'}
        trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}
    
        #testing and isolation intervention
        interventions = [
            cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sept-1, test_delay=t_delay),
            cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sept, test_delay=t_delay),
            cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
            cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
            cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july, end_day=tti_day_august-1),
            cv.contact_tracing(trace_probs=t_probs_august, trace_time=trace_d_1, start_day=tti_day_august, end_day=tti_day_sept-1),
            cv.contact_tracing(trace_probs=t_probs_sept, trace_time=trace_d_1, start_day=tti_day_sept),
          ]
    
    else:
        raise ValueError(f'Scenario {tti_scen} not recognised')

    return interventions 

if __name__ == '__main__':
    ## Parse the command-line arguments
    args = parser.parse_args()

    # Create the baseline simulation
    sim = cv.Sim(pars=pars, datafile=data_path, location='uk')
    sim['prognoses']['sus_ORs'][0] = 1.0 # ages 0-10
    sim['prognoses']['sus_ORs'][1] = 1.0 # ages 10-20

    # Add in interventions
    _, _, _, _, _, contact_interventions = scenario_beta_changes(sim, args)
    tracing_interventions = tracing_interventions(sim, args)
    interventions = contact_interventions + tracing_interventions
    sim.update_pars(interventions=interventions)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    noise = 0.00

    msim = cv.MultiSim(base_sim=sim) # Create using your existing sim as the base
    msim.run(reseed=True, noise=noise, n_runs=args.samples, keep_people=True) # Run with uncertainty

    # Recalculate R_eff with a larger window
    for sim in msim.sims:
        sim.compute_r_eff(smoothing=10)

    msim.reduce() # "Reduce" the sims into the statistical representation

    #to produce mean cumulative infections and deaths for barchart figure
    print('Mean cumulative values:')
    print('Deaths: ',     msim.results['cum_deaths'][-1])
    print('Infections: ', msim.results['cum_infections'][-1])

    try:
        os.makedirs("%s" % args.scenario)
    except:
        pass
    outfile = "%s/test%s-trace%s.obj" % (args.scenario, args.test, args.trace)
    msim.args = args
    sc.saveobj(outfile, sc.objdict((("args", args), ("msim", msim.results), ("sims", list(sim.results for sim in msim.sims)))))

    # Save the key figures
    plot_customizations = dict(
        interval   = 90, # Number of days between tick marks
        dateformat = '%m/%Y', # Date format for ticks
        fig_args   = {'figsize':(14,8)}, # Size of the figure (x and y)
        axis_args  = {'left':0.15}, # Space on left side of plot
        )

    msim.plot_result('r_eff', **plot_customizations)
    #sim.plot_result('r_eff')
    pl.axhline(1.0, linestyle='--', c=[0.8,0.4,0.4], alpha=0.8, lw=4) # Add a line for the R_eff = 1 cutoff
    pl.title('')
    pl.savefig('%s/test%s-trace%s-R.pdf' % (scenario, args.test, args.trace))

    msim.plot_result('cum_deaths', **plot_customizations)
    pl.title('')
    cv.savefig('%s/test%s-trace%s-Deaths.pdf' % (scenario, args.test, args.trace))

    msim.plot_result('new_infections', **plot_customizations)
    pl.title('')
    cv.savefig('%s/test%s-trace%s-Infections.pdf' % (scenario, args.test, args.trace))

    msim.plot_result('cum_diagnoses', **plot_customizations)
    pl.title('')
    cv.savefig('%s/test%s-trace%s-Diagnoses.pdf' % (scenario, args.test, args.trace))

