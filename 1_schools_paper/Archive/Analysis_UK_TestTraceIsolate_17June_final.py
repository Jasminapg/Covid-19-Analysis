'''
UK scenarios
'''

import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
pl.switch_backend('agg')

# Check version
cv.check_version('1.3.3')
cv.git_info('covasim_version.json')

do_plot = 1
do_save = 1
do_show = 1
verbose = 1
seed    = 1

scenario = ['jun-opening-full', 'sep-opening-only', 'phased-june-full-sep', 'phased-june-rota-sep'][2] # Set a number to pick a scenario from the available options
tti_scen = ['current', '40%', '68%'][0] # Ditto

version   = 'v1'
date      = '2020june17'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_june17.xlsx'
fig_path  = f'{file_path}_{scenario}.png'

start_day = '2020-01-21'
end_day   = '2020-06-30'

# Set the parameters
total_pop    = 67.86e6 # UK population size
pop_size     = 100e3 # Actual simulated population
pop_scale    = int(total_pop/pop_size)
pop_type     = 'hybrid'
#kids infectiousness the same as adults
#pop_infected = 1500
#beta         = 0.005938
#s_prob_may   = 0.0198
#s_prob_june  = 0.0198
##kids infectiousness 50% that of adults
pop_infected = 1500
beta         = 0.005938
#
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
ti_day = sim.day('2021-04-17') #schools interventions (ti) start

#change parameters here for different schools opening strategies with society opening

beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-06', ti_day]

#June opening with society opening
if scenario == 'jun-opening-full':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.80, 0.80, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.70, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.80, 0.80, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90]

#September opening with society opening
elif scenario == 'sep-opening-only':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.02, 0.02, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.50, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.50, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90]

#Phased opening with society opening
elif scenario == 'phased-june-full-sep':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90]

#Phased-delayed opening with society opening
elif scenario == 'phased-june-rota-sep':
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.50, 0.00, 0.50, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.70, 0.70, 0.70, 0.70, 0.70, 0.90, 0.70, 0.90, 0.70, 0.90]

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
    #testing in June remains the same as before June under this scenario
    s_prob_march = 0.009
    s_prob_april = 0.012
    s_prob_may   = 0.0198
    #no change in daily symptomatic probability in this scenario
    s_prob_june = 0.0198
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing not on under this scenario
    t_eff_june   = 0.68
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day),
      ]

elif tti_scen == '40%':

# Tracing and enhanced testing strategy of symptimatics from 1st June with tracing at 40%
    #testing in June
    s_prob_march = 0.012
    s_prob_april = 0.012
    s_prob_may   = 0.029
    #s_prob_june_2 is increased to minimum value to avoid secondary wave
    #for phased-june-fully_sep
    #s_prob_june_1 = 0.185
    #for phased-june-rota_sep
    s_prob_june_1 = 0.13
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing in June is 40%
    t_eff_june   = 0.4
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    trace_d_2      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention    
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june_1, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_2, start_day=tti_day),
      ]

elif tti_scen == '68%':

    # Tracing and enhanced testing strategy of symptimatics from 1st June with tracing of 80%
    #testing in June
    s_prob_march = 0.009
    s_prob_april = 0.012
    s_prob_may   = 0.029
    #s_prob_june_2 is increased to minimum value to avoid secondary wave
    #for phased-june-fully_sep
    #s_prob_june_2 = 0.13
    #for phased-june-rota_sep
    s_prob_june_2 = 0.085
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing in june at 80% for this scenario
    t_eff_june   = 0.68
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    trace_d_3      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june_2, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_3, start_day=tti_day),
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
    msim.run(reseed=True, noise=noise, n_runs=10, keep_people=True) # Run with uncertainty

    # Recalculate R_eff with a larger window
    for sim in msim.sims:
        sim.compute_r_eff(smoothing=10)

    msim.reduce() # "Reduce" the sims into the statistical representation

    #to produce mean cumulative infections and deaths for barchart figure
    print('Mean cumulative values:')
    print('Deaths: ',     msim.results['cum_deaths'][-1])
    print('Infections: ', msim.results['cum_infections'][-1])

    # Save the key figures
    plot_customizations = dict(
        interval   = 15, # Number of days between tick marks
        dateformat = '%m/%Y', # Date format for ticks
        fig_args   = {'figsize':(14,8)}, # Size of the figure (x and y)
        axis_args  = {'left':0.15}, # Space on left side of plot
        )

    msim.plot_result('r_eff', **plot_customizations)
    #sim.plot_result('r_eff')
    pl.axhline(1.0, linestyle='--', c=[0.8,0.4,0.4], alpha=0.8, lw=4) # Add a line for the R_eff = 1 cutoff
    pl.title('')
    pl.savefig('R_eff.png')

    msim.plot_result('cum_deaths', **plot_customizations)
    pl.title('')
    cv.savefig('Deaths.png')

    msim.plot_result('new_infections', **plot_customizations)
    pl.title('')
    cv.savefig('Infections.png')

    msim.plot_result('cum_diagnoses', **plot_customizations)
    pl.title('')
    cv.savefig('Diagnoses.png')

##for calibration figures
   #msim.plot_result('cum_deaths', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   #pl.title('')
   #cv.savefig('Deaths.png')

   # msim.plot_result('cum_diagnoses', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   # pl.title('')
   # cv.savefig('Diagnoses.png')

