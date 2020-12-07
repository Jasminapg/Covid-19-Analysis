'''
UK scenarios for evaluating effectivness of masks
'''

import sciris as sc
import covasim as cv
import pylab as pl
import numpy as np
import matplotlib as mplt
# pl.switch_backend('agg')

# Check version
cv.check_version('1.7.4')
cv.git_info('covasim_version.json')

mplt.rcParams['font.family'] = 'Roboto'


do_plot = 1
do_save = 1
do_show = 0
verbose = 1
seed    = 1


scenario = ['med_comp','2weekcircuit','3weekcircuit','4weekcircuit','trade-offs'][0] # Set a number to pick a scenario from the available options
tti_scen = ['current', 'optimal_med_comp', 'optimal_med_comp_work'][0] # Ditt0

version   = 'v1'
date      = '2020nov29'
folder    = f'results_FINAL_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_december6.xlsx'
fig_path  = f'{file_path}_{scenario}.png'

start_day = '2020-01-21'
end_day = '2021-03-31'

# Set the parameters
total_pop    = 67.86e6 # UK population size
pop_size     = 100e3 # Actual simulated population
#pop_size = 2e3
pop_scale    = int(total_pop/pop_size)
pop_type     = 'hybrid'
#kids infectiousness the same as adults
#model fitted using optuna to find pop_infected and beta and s_prob_X for months we have data
# pop_infected = 1500
pop_infected = 1500
#beta         = 0.00736967
beta         = 0.007633

asymp_factor = 2
contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
#quar_factor = dict(h=0.7, s=0.0, w=0.2, c=0.2)

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
sim['prognoses']['sus_ORs'][0] = 1.0 # ages 20-30
sim['prognoses']['sus_ORs'][1] = 1.0 # ages 20-30
sim['rel_severe_prob'] = 1.35
sim['rel_crit_prob']  = 1.35  # Scale factor for proportion of severe cases that become critical
sim['rel_death_prob']  = 0.5 # Scale factor for proportion of critical cases that result in death

#sim['prognoses']['trans_ORs'][2] = 1.5 # ages 20-30
#sim['prognoses']['trans_ORs'][3] = 1.5 # ages 20-30

#def more_young_infections(sim):
    
 #  if sim.t == sim.day('2020-09-01'):
      #sim.people.rel_trans[sim.people.age<30] *= 2.0
        #sim.people.rel_trans[3] *= 1.0
  #      sim['prognoses']['trans_ORs'][2] = 1.5 # ages 20-30
   #     sim['prognoses']['trans_ORs'][3] = 1.5 # ages 20-30
#sim = cv.Sim(interventions=more_young_infections)
#sim = cv.Sim(pars=pars, datafile=data_path, location='uk', interventions=more_young_infections)   

#def more_young_infections(sim):
 #   if sim.t == sim.day('2020-07-01'):
  #      sim.people.rel_trans[sim.people.age<30] *= 2
#sim = cv.Sim(interventions=more_young_infections)

#%% Interventions


# Create the baseline simulation

tc_day = sim.day('2020-03-16') #intervention of some testing (tc) starts on 16th March and we run until 1st April when it increases
te_day = sim.day('2020-04-01') #intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
tt_day = sim.day('2020-05-01') #intervention of increased testing (tt) starts on 1st May
tti_day= sim.day('2020-06-01') #intervention of tracing and enhanced testing (tti) starts on 1st June
ti_day = sim.day('2021-03-31') #schools interventions end date in December 2021
tti_day_july= sim.day('2020-07-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st July
tti_day_august= sim.day('2020-08-01') #intervention of tracing and enhanced testing (tti) at different levels starts on 1st August
tti_day_sep= sim.day('2020-09-01')
tti_day_oct= sim.day('2020-10-01')
tti_day_nov= sim.day('2020-11-01')

#change parameters here for different schools opening strategies with society opening
beta_days = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-01', '2020-06-15', '2020-07-22', '2020-08-01', '2020-09-02', '2020-10-01', '2020-10-16', '2020-10-26', '2020-11-01', '2020-11-05', '2020-11-14', '2020-11-21', '2020-11-30', '2020-12-03', '2020-12-23', '2021-12-27', '2021-01-10', '2021-01-20', '2021-02-17', '2020-02-28', '2021-04-01', '2021-04-17', '2021-05-31', '2021-06-04', '2021-07-20', '2021-09-01', '2021-10-30', '2021-11-10', ti_day]
# moderate EC of masks in community and schools
# Community contacts reduction by 30% means 49% of normal during termtime and 42% during holidays from 24th Jul
# Schools contacts reduction by 30% means 63% of normal during termtime from 1st Sep
# masks in secondary schools from 1st September
if scenario == 'med_comp':
    #colmun 10=seo 2020, column 15=05 Nov 2020, column 19=01 dec 2020, column 20=23 dec 2020, column 21= 27 dec 2020, column 22=10 Jan 2021
   
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.50, 1.50, 1.50, 1.29, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.00, 1.29]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.63, 0.63, 0.00, 0.63, 0.00, 0.63, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.00, 0.63, 0.63, 0.00]
    #w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.50,sep,  oct , 0.60, 0.50,       nov5                   dec01 dec23 dec27 10jan  23jan
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.50, 0.50, 0.60, 0.60, 0.60, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.60, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.60, 0.60, 0.70, 0.70, 0.70, 0.50, 0.50, 0.50, 0.50, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60, 0.60]
#8th from the back is 1st Nov; circuits end 14h, 21st 30th Nov
if scenario == '2weekcircuit':
   
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.00, 0.63]
    #w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.60, 0.60, 0.60, 0.60, 0.60, 0.20, 0.20, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.60, 0.60, 0.70, 0.70, 0.70, 0.20, 0.20, 0.50, 0.50, 0.50, 0.50, 0.60, 0.60, 0.60, 0.60]
#8th from the back is 1st Nov; 

if scenario == '3weekcircuit':
   
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.00, 0.63]
    #w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.60, 0.60, 0.60, 0.60, 0.60, 0.20, 0.20, 0.20, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.60, 0.60, 0.70, 0.70, 0.70, 0.20, 0.20, 0.20, 0.50, 0.50, 0.50, 0.60, 0.60, 0.60, 0.60]
#8th from the back is 1st Nov; 

if scenario == '4weekcircuit':
   
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.00, 0.63]
    #w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.60, 0.60, 0.60, 0.60, 0.60, 0.20, 0.20, 0.20, 0.20, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.60, 0.60, 0.70, 0.70, 0.70, 0.20, 0.20, 0.20, 0.20, 0.50, 0.50, 0.60, 0.60, 0.60, 0.60]
#8th from the back is 1st Nov; 

if scenario == 'trade-offs':
   
    h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.29, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.00, 1.00, 1.29, 1.00, 1.00, 1.29, 1.00]
    s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.23, 0.38, 0.00, 0.00, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.63, 0.63, 0.00, 0.63, 0.63, 0.00, 0.63]
    #w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.50, 0.50, 0.60, 0.50, 0.60, 0.50, 0.60]
    w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.60, 0.60, 0.60, 0.60, 0.60, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50]
    c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.50, 0.60, 0.60, 0.70, 0.70, 0.70, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.60, 0.60, 0.60, 0.60]


else:
    print(f'Scenario {scenario} not recognised')

# Define the beta changes
h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h')
s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s')
w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w')
c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c')

#next line to save the intervention
interventions = [h_beta, w_beta, s_beta, c_beta]


# to fit data in September better
#def more_young_infections(sim):
#if sim.t == sim.day('2020-08-01'):
#        sim.people.rel_trans[sim.people.age<30] *= 2
#interventions = [more_young_infections]
#sim = cv.Sim(interventions=more_young_infections)

if tti_scen == 'current':

    # Tracing and enhanced testing strategy of symptimatics from 1st June
    s_prob_march = 0.012
    s_prob_april = 0.017
    s_prob_may   = 0.02769
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    s_prob_sept = 0.05769
    s_prob_oct = 0.05769
    s_prob_nov = 0.07769
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]
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
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay,test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0175, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay, test_sensitivity=0.97),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0275, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_nov, test_delay=t_delay, test_sensitivity=0.97),
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

elif tti_scen == 'optimal_med_comp':

# Tracing and enhanced testing strategy of symptimatics from 1st June 
    #OLD
    #s_prob_march = 0.012
    #s_prob_april = 0.012
    #s_prob_may   = 0.0165
    #s_prob_june = 0.0171
    #s_prob_july = 0.0171
    #optimal masks in schools, workplaces and community EC=15; 67%
    #s_prob_august = 0.12
    #t_delay       = 1.0
    #NEW
    s_prob_march = 0.009
    s_prob_april = 0.013
    s_prob_may   = 0.026
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    
    ##for no masks p_s=0.13; for 15% EC in schools p_s=0.11; for 15% EC and not in schools p_2=
    s_prob_sept = 0.02769
    t_delay       = 1.0

    iso_vals = [{k:0.7 for k in 'hswc'}]

    #tracing level at 42 from June; 47% in July
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.0075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.02769, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july),
      ]

elif tti_scen == 'optimal_med_comp_work':
    
    # Tracing and enhanced testing strategy of symptimatics from 1st June 
    s_prob_march = 0.007
    s_prob_april = 0.013
    s_prob_may   = 0.026
    s_prob_june = 0.02769
    s_prob_july = 0.02769
    s_prob_august = 0.02769
    #EC=30% ps_s=0.06 or 46%
    s_prob_sept = 0.06
    t_delay       = 1.0

    iso_vals = [{k:0.1 for k in 'hswc'}]

    #tracing level at 42% from June; 47% in July
    t_eff_june   = 0.42
    t_eff_july   = 0.47
    t_probs_june = {k:t_eff_june for k in 'hwsc'}
    t_probs_july = {k:t_eff_july for k in 'hwsc'}
    trace_d_1      = {'h':0, 's':1, 'w':1, 'c':2}

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sept, asymp_prob=0.00075, symp_quar_prob=0.0, asymp_quar_prob=0.0, start_day=tti_day_sep, test_delay=t_delay),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d_1, start_day=tti_day, end_day=tti_day_july-1),
        cv.contact_tracing(trace_probs=t_probs_july, trace_time=trace_d_1, start_day=tti_day_july),
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
    
    tt = sim.make_transtree()
    source_inds = [s for s in tt.sources if s is not None] # Remove Nones
    ages = sim.people.age[source_inds] # Get ages
    pl.hist(ages, bins=20) # Plot histogram
    pl.savefig('Histogram.pdf')

    #to produce mean cumulative infections and deaths for barchart figure
    print('Mean cumulative values:')
    print('Deaths: ',     msim.results['cum_deaths'][-1])
    print('Infections: ', msim.results['cum_infections'][-1])

    # Save the key figures
    plot_customizations = dict(
        interval   = 60, # Number of days between tick marks
        dateformat = '%m/%Y', # Date format for ticks
        fig_args   = {'figsize':(14, 6)}, # Size of the figure (x and y)
        axis_args  = {'left':0.10, 'right': 0.95, 'top': 0.88, 'bottom': 0.12}, # Space on left side of plot
        font_family = 'Roboto Condensed',
        font_size = 26,
        do_show=do_show,
        color = 'k'
        # scatter_args={'c': 'k'}
        )

    plot_customizations['color'] = mplt.colors.to_rgba('#333333')
    msim.plot_result('r_eff', **plot_customizations)
    #sim.plot_result('r_eff')
    pl.axhline(1.0, linestyle='--', c=[0.8,0.4,0.4], alpha=0.8, lw=4) # Add a line for the R_eff = 1 cutoff
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('R.pdf')

    plot_customizations['color'] = mplt.colors.to_rgba('black')
    msim.plot_result('cum_deaths', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Cumulative Deaths.pdf')
    
    plot_customizations['color'] = mplt.colors.to_rgba('black')
    msim.plot_result('new_deaths', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Daily Deaths.pdf')

    plot_customizations['color'] = mplt.colors.to_rgba('#c21945')
    msim.plot_result('new_infections', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Infections.pdf')

    plot_customizations['color'] = mplt.colors.to_rgba('#2c00b5')
    msim.plot_result('cum_diagnoses', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Diagnoses.pdf')
    
    plot_customizations['color'] = mplt.colors.to_rgba('#2c00b5')
    msim.plot_result('cum_critical', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Hospitalisations.pdf')
    
    plot_customizations['color'] = mplt.colors.to_rgba('#2c00b5')
    msim.plot_result('cum_tests', **plot_customizations)
    pl.xticks(fontsize=22)
    pl.yticks(fontsize=22)
    pl.title('')
    pl.savefig('Tests.pdf')
    
    
     # Save the key figures


##for calibration figures
   #msim.plot_result('cum_deaths', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   #pl.title('')
   #cv.savefig('Deaths.png')

   # msim.plot_result('cum_diagnoses', interval=20, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
   # pl.title('')
   # cv.savefig('Diagnoses.png')
