'''
UK scenarios for evaluating effectivness of masks
'''

import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--test", type=float, default=0.0171)
parser.add_argument("--trace", type=float, default=0.47)
parser.add_argument("--scenario", type=int, default=0)
args = parser.parse_args()

pl.switch_backend('agg')

# Check version
cv.check_version('1.4.7')
cv.git_info('covasim_version.json')

do_plot = 1
do_save = 1
do_show = 1
verbose = 1
seed    = 1

scenario = ['phased-june-full-sep-masks15', 'phased-june-full-sep-masks30', 'phased-june-full-sep-masks15_notschools', 'phased-june-full-sep-masks30_notschools'][args.scenario] # Set a number to pick a scenario from the available options
tti_scen = ['current', 'test-trace'][1] # Ditt0

version   = 'v1'
date      = '2020june17'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_august02.xlsx'
fig_path  = f'{file_path}_{scenario}.png'

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
beta         = 0.00593

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
ti_day = sim.day('2021-04-17') #schools interventions end date
tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August


#change parameters here for different schools opening strategies with society opening
beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-06', ti_day]

# Fully Schools from Sep opening with society opening
# Phased opening with society opening and masks effective coverage=15% from 24th July
# masks in secondary schools and workplaces and community 
if scenario == 'phased-june-full-sep-masks15':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.765, 0.00, 0.765, 0.00, 0.765, 0.00, 0.765, 0.00, 1.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.49, 0.765, 0.595, 0.765, 0.595, 0.765, 0.595, 0.765, 0.595, 0.765]

#Phased opening with society opening and masks effective coverage=30% from 24th July
elif scenario == 'phased-june-full-sep-masks30':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.70]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.49, 0.35, 0.49, 0.35, 0.49, 0.35, 0.49, 0.35, 0.49]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63]

#Phased opening with society opening and masks effective coverage=15% from 24th July
# masks only in community and workplacs BUT NOT schools
elif scenario == 'phased-june-full-sep-masks15_notschools': 
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595, 0.425, 0.595]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.49, 0.765, 0.595, 0.765, 0.595, 0.765, 0.595, 0.765, 0.595, 0.765]

#Phased opening with society opening and masks effictve coverage=30% from 24th July
# masks only in community and workplacs BUT NOT schools
elif scenario == 'phased-june-full-sep-masks30_notschools':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.70]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.425, 0.49, 0.35, 0.49, 0.35, 0.49, 0.35, 0.49, 0.35, 0.49]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63, 0.49, 0.63]

else:
    print(f'Scenario {scenario} not recognised')

# Define the beta changes
h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')

#next line to save the intervention
interventions = [h_beta, w_beta, s_beta, c_beta]

if tti_scen == 'current':

    # Tracing and enhanced testing strategy of symptimatics from 1st June
    # testing in March, May, June and July fitted during calibration 
    # under current scenario assumed testing level to remain the same as in July
    s_prob_march = 0.012
    s_prob_april = 0.012
    s_prob_may   = 0.0165
    s_prob_june = 0.0171
    s_prob_july = 0.0171
    #under this scenario we assume testing levels in August and beyond are as in July i.e. (1-(1-0.0171)^10)*100=16%
    s_prob_august = 0.0171
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    # tracing level at 42% from June; 47% in July
    # under current scenario assumed tracing level to remain the same as in July i.e 47%
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_eff_august = 0.47
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    t_probs_august = {k:t_eff_august for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.0012, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
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

elif tti_scen == 'test-trace':

# Tracing and enhanced testing strategy of symptimatics to change for phase plots
    #Phase plots=need to change s_prob_august and t_eff_august and plot R, new infections, deaths and diagnosis for different combinations of s_prob_august and t_eff_august
    
    #testing
    s_prob_march = 0.012
    s_prob_april = 0.012
    s_prob_may   = 0.0165
    s_prob_june = 0.0171
    s_prob_july = 0.0171
    #we want to vary s_prob_august to vary testing level
    s_prob_august = args.test
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing level at 68% from June; 50% in July
    #we want to vary t_eff_august to vary tracing level
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_eff_august = args.trace
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    t_probs_august = {k:t_eff_august for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.012, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
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

else:
    print(f'Scenario {tti_scen} not recognised')


# Finally, update the parameters
sim.update_pars(interventions=interventions)
for intervention in sim['interventions']:
    intervention.do_plot = False

if __name__ == '__main__':

    noise = 0.00

    msim = cv.MultiSim(base_sim=sim) # Create using your existing sim as the base
    msim.run(reseed=True, noise=noise, n_runs=12, keep_people=True) # Run with uncertainty

    # Recalculate R_eff with a larger window
    for sim in msim.sims:
        sim.compute_r_eff(smoothing=10)

    msim.reduce() # "Reduce" the sims into the statistical representation

    #to produce mean cumulative infections and deaths for barchart figure
    print('Mean cumulative values:')
    print('Deaths: ',     msim.results['cum_deaths'][-1])
    print('Infections: ', msim.results['cum_infections'][-1])

    try:
        os.makedirs("%s" % scenario)
    except:
        pass
    outfile = "%s/test%s-trace%s.obj" % (scenario, args.test, args.trace)
    sc.saveobj(outfile, sc.objdict((("args", args), ("results", msim.results))))

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

