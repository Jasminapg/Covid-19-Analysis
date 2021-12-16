import sciris as sc
import covasim as cv
import covasim.parameters as cvpar
import pylab as pl
import numpy as np
 

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('>=3.1.0')
cv.git_info('covasim_version.json')

# Saving and plotting settings
do_plot = 1
do_save = 1
save_sim = 1
plot_hist = 0 # Whether to plot an age histogram
do_show = 0
verbose = 1
seed    = 1
to_plot = sc.objdict({
    'Daily infections': ['new_diagnoses'],
    'Daily hospitalisations': ['new_severe'],
    'Daily ICUs': ['new_critical'],
    'Daily deaths': ['new_deaths'],
    'Occupancy': ['n_severe'],
    'Prevalence': ['prevalence'],
    'Incidence': ['incidence'],
    'R': ['r_eff'],
    'proportion vaccinated': ['frac_vaccinated'],
    'Vaccinated': ['cum_vaccinated'],
})

# Filepaths
data_path = 'England_Covid_cases_Nov272021.xlsx'
resfolder = 'results'
figfolder = 'figs'

# Important dates
start_day = '2020-01-20'
data_end  = '2021-10-31' # Final date for calibration -- set this to a date before boosters started

seed = 1
beta = 0.0079

########################################################################
# Define the vaccination rollout
########################################################################

vx_rollout = {
    75: dict(start_age=75, end_age=100, start_day='2020-12-20', final_uptake=0.95, days_to_reach=14),
    60: dict(start_age=60, end_age=75,  start_day='2021-01-28', final_uptake=0.95, days_to_reach=14),
    50: dict(start_age=50, end_age=60,  start_day='2021-02-10', final_uptake=0.95, days_to_reach=14),
    45: dict(start_age=45, end_age=50,  start_day='2021-03-20', final_uptake=0.90, days_to_reach=14),
    40: dict(start_age=40, end_age=45,  start_day='2021-04-10', final_uptake=0.90, days_to_reach=14),
    30: dict(start_age=30, end_age=40,  start_day='2021-05-10', final_uptake=0.80, days_to_reach=14),
    25: dict(start_age=25, end_age=30,  start_day='2021-06-10', final_uptake=0.80, days_to_reach=14),
    18: dict(start_age=18, end_age=25,  start_day='2021-06-30', final_uptake=0.80, days_to_reach=14),
    16: dict(start_age=16, end_age=18,  start_day='2021-08-10', final_uptake=0.75, days_to_reach=14),
    12: dict(start_age=12, end_age=15,  start_day='2021-09-01', final_uptake=0.70, days_to_reach=14),
}
# For simplicity, we assume linear scale-up for each age group, from 0% vax coverage to the final
# uptake value over the duration of the vaccination campaign
def set_subtargets(vx_phase):
  return lambda sim: cv.true((sim.people.age >= vx_phase['start_age']) * (sim.people.age < vx_phase['end_age']))

subtarget_dict = {}
for age, vx_phase in vx_rollout.items():
    vx_phase['daily_prob'] = vx_phase['final_uptake'] / vx_phase['days_to_reach']
    subtarget_dict[age] = {'inds': set_subtargets(vx_phase),
                           'vals': vx_phase['daily_prob']}

########################################################################
# Create the baseline simulation
########################################################################
 
def make_sim(seed, beta, verbose=0.1):

    # Set the parameters
    #total_pop    = 67.86e6 # UK population size
    total_pop    = 55.98e6 # UK population size
    pop_size     = 100e3 # Actual simulated population
    pop_scale    = int(total_pop/pop_size)
    pop_type     = 'hybrid'
    pop_infected = 1000
    beta         = beta
    asymp_factor = 2
    contacts     = {'h':3.0, 's':20, 'w':20, 'c':20}
    beta_layer   = {'h':3.0, 's':1.0, 'w':0.6, 'c':0.3}
    end_day = data_end

    pars = sc.objdict(
        use_waning   = True,
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

   # ADD BETA INTERVENTIONS
    #sbv is transmission in schools and assumed to be 63%=0.7*90% assuming that masks are used and redyce it by 30%
    #from June 2021 we will asume that it is 50% as a combination of large scale isolation of bubbles - found via seeking optimal value
    sbv = 0.63
    sbv_new = 0.63
    beta_dict  = sc.odict({'2020-02-14': [1.00, 1.00, 0.90, 0.90],
                           '2020-03-16': [1.00, 0.90, 0.80, 0.80],
                           #first lockdown starts
                           '2020-03-23': [1.00, 0.02, 0.20, 0.20],
                           #first lockdown ends
                           '2020-06-01': [1.00, 0.23, 0.40, 0.40],
                           '2020-06-15': [1.00, 0.38, 0.50, 0.50],
                           '2020-07-22': [1.15, 0.00, 0.30, 0.50],
                           '2020-07-29': [1.15, 0.00, 0.30, 0.70],
                           '2020-08-12': [1.15, 0.00, 0.30, 0.70],
                           '2020-07-19': [1.15, 0.00, 0.30, 0.70],
                           '2020-07-26': [1.15, 0.00, 0.30, 0.70],
                           #schools start in Sep 2020
                           '2020-09-02': [1.15, sbv, 0.50, 0.70],
                           '2020-10-01': [1.15, sbv, 0.40, 0.70],
                           '2020-10-16': [1.15, sbv, 0.40, 0.70],
                           #schools holiday Oct 2020
                           '2020-10-26': [1.15, 0.00, 0.30, 0.60],
                           #2nd lockdown starts
                           '2020-11-05': [1.15, sbv, 0.30, 0.40],
                           '2020-11-14': [1.15, sbv, 0.30, 0.40],
                           '2020-11-21': [1.15, sbv, 0.30, 0.40],
                           '2020-11-30': [1.15, sbv, 0.30, 0.40],
                           '2020-12-05': [1.15, sbv, 0.30, 0.40],
                           #2nd lockdown ends and opening for Christmas
                           '2020-12-10': [1.50, sbv, 0.40, 0.80],
                           '2020-12-17': [1.50, sbv, 0.40, 0.80],
                           '2020-12-24': [1.50, 0.00, 0.40, 0.60],
                           '2020-12-26': [1.50, 0.00, 0.40, 0.70],
                           '2020-12-31': [1.50, 0.00, 0.20, 0.70],
                           '2021-01-01': [1.50, 0.00, 0.20, 0.70],
                           #3rd lockdown starts
                           '2021-01-04': [1.10, 0.14, 0.20, 0.40],
                           '2021-01-11': [1.05, 0.14, 0.20, 0.40],
                           '2021-01-18': [1.05, 0.14, 0.30, 0.30],
                           '2021-01-30': [1.05, 0.14, 0.30, 0.30],
                           '2021-02-08': [1.05, 0.14, 0.30, 0.30],
                           '2021-02-15': [1.05, 0.00, 0.20, 0.20],
                           '2021-02-22': [1.05, 0.14, 0.30, 0.30],
                           #3rd lockdown ends and reopening starts in 4 steps
                           #schools open in March 2021 - step 1 part 1
                           '2021-03-08': [1.05, sbv, 0.30, 0.40],
                           '2021-03-15': [1.05, sbv, 0.30, 0.40],
                           '2021-03-22': [1.05, sbv, 0.30, 0.40],
                           #stay at home rule finishes - step 1 part 2
                           '2021-03-29': [1.05, 0.00, 0.40, 0.50],
                           '2021-04-01': [1.05, 0.00, 0.30, 0.50],
                           #further relaxation measures - step 2
                           '2021-04-12': [1.05, 0.00, 0.30, 0.40],
                           '2021-04-19': [1.05, sbv, 0.30, 0.40],
                           '2021-04-26': [1.05, sbv, 0.30, 0.40],
                           '2021-05-03': [1.05, sbv, 0.30, 0.40],
                           '2021-05-10': [1.05, sbv, 0.30, 0.40],
                           #some further relaxation  - step 3
                           '2021-05-17': [1.05, sbv, 0.30, 0.50],
                           '2021-05-21': [1.05, sbv, 0.30, 0.50],
                           #May half-term
                           '2021-05-31': [1.05, 0.00, 0.30, 0.40],
                           #slight relaxation after Spring half-term
                           '2021-06-07': [1.05, sbv, 0.30, 0.50],
                           '2021-06-14': [1.05, sbv, 0.30, 0.50],
                           #full relaxing of social distancing - step 4 - delayed to 19/07/2021 
                           #but we needed to increase in the model to fit data
                           #note sporting events open and at the end of June
                           #large surge in cases from middle of June
                           #need these social mixing values to match the data
                           ###OPTION 1=sociaty reopens but big isolation in schools
                           '2021-06-19': [1.05, 0.63, 0.30, 0.80],
                           '2021-06-21': [1.05, 0.63, 0.30, 0.80],
                           #to fit data we need to increase testing and mixing from 22/06/2021                          
                           '2021-06-28': [1.05, 0.63, 0.30, 0.80],
                           '2021-07-05': [1.05, 0.63, 0.30, 0.80],
                           '2021-07-12': [1.05, 0.63, 0.30, 0.80],
                           #cases start to drop from middle of July
                           '2021-07-19': [1.05, 0.00, 0.30, 0.80],
                           #easing of socal distancing measures - delayed step 4
                           '2021-07-26': [1.05, 0.00, 0.30, 0.50],
                           '2021-08-02': [1.05, 0.00, 0.30, 0.50],
                           '2021-08-09': [1.05, 0.00, 0.30, 0.50],
                           '2021-08-16': [1.05, 0.00, 0.30, 0.50],
                           '2021-08-23': [1.05, 0.00, 0.30, 0.50],
                           #reopening schools in Sep 2021
                           '2021-09-07': [1.05, sbv_new, 0.50, 0.80],
                           '2021-09-15': [1.05, sbv_new, 0.50, 0.80],
                           '2021-09-29': [1.05, sbv_new, 0.50, 0.80],
                           '2021-10-15': [1.05, 0.40, 0.30, 0.60],
                           '2021-10-22': [1.05, 0.00, 0.30, 0.60],
                           '2021-11-01': [1.05, sbv_new, 0.50, 0.80],
                           })

    beta_days = list(beta_dict.keys())
    h_beta = cv.change_beta(days=beta_days, changes=[c[0] for c in beta_dict.values()], layers='h')
    s_beta = cv.change_beta(days=beta_days, changes=[c[1] for c in beta_dict.values()], layers='s')
    w_beta = cv.change_beta(days=beta_days, changes=[c[2] for c in beta_dict.values()], layers='w')
    c_beta = cv.change_beta(days=beta_days, changes=[c[3] for c in beta_dict.values()], layers='c')
    interventions = [h_beta, w_beta, s_beta, c_beta]

    # adding different variants: B.1.177 in September 2020, Alpha slightly later and Delta from April 2021
    # Add B.1.177 strain from September 2020 and assume it's like b1351 (no vaccine at this time in England)
    variants = []
    b1177 = cv.variant('b1351', days=np.arange(sim.day('2020-08-10'), sim.day('2020-08-20')), n_imports=3000)
    b1177.p['rel_beta']        = 1.2
    b1177.p['rel_severe_prob'] = 0.4
    variants += [b1177]
    # Add Alpha strain from October 2020
    b117 = cv.variant('b117', days=np.arange(sim.day('2020-10-20'), sim.day('2020-10-30')), n_imports=3000)
    b117.p['rel_beta']        = 1.8
    b117.p['rel_severe_prob'] = 0.4
    variants += [b117]
    # Add Delta strain starting middle of April
    b16172 = cv.variant('b16172', days=np.arange(sim.day('2021-04-15'), sim.day('2021-04-20')), n_imports=4000)
    b16172.p['rel_beta']         = 3.1
    b16172.p['rel_severe_prob']  = 0.2
    variants += [b16172]

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
    tti_day_feb= sim.day('2021-02-01')
    tti_day_march= sim.day('2021-03-08')
    tti_day_june21= sim.day('2021-06-20')
    tti_day_july21= sim.day('2021-07-19')
    tti_day_august21= sim.day('2021-08-02')
    tti_day_sep21= sim.day('2021-09-01')
    tti_day_oct21= sim.day('2021-10-22')
    tti_day_nov21= sim.day('2021-11-07')
    tti_day_dec21= sim.day('2021-12-01')

    s_prob_april = 0.012
    s_prob_may   = 0.012
    s_prob_june = 0.04769
    s_prob_july = 0.04769
    s_prob_august = 0.04769
    # tn = 0.09
    s_prob_sep = 0.07769
    s_prob_oct = 0.07769
    s_prob_nov = 0.07769
    s_prob_dec = 0.07769
    s_prob_jan = 0.08769
    s_prob_march = 0.08769
    #to match the increase in June-mid July from optuna increased testing is necessary
    s_prob_june21 = 0.19769
    #to match the drop in mid-July from optuna decline ine testing (or switched tracing off as alternative)
    s_prob_july21 = 0.08769
    s_prob_august21 = 0.08769
    s_prob_sep21 =0.09769
    s_prob_oct21 =0.07769
    s_prob_nov21 =0.11769
    s_prob_dec21 =0.09769

    t_delay       = 1.0

    #isolation may-june
    iso_vals = [{k:0.2 for k in 'hswc'}]
    #isolation july
    iso_vals1 = [{k:0.4 for k in 'hswc'}]
    #isolation september
    iso_vals2 = [{k:0.6 for k in 'hswc'}]
    #isolation october
    iso_vals3 = [{k:0.6 for k in 'hswc'}]
    #isolation november
    iso_vals4 = [{k:0.2 for k in 'hswc'}]
     #isolation december
    iso_vals5 = [{k:0.5 for k in 'hswc'}]
    #isolation March 2021
    ####chnaged to 0.2 for fitting
    iso_vals6 = [{k:0.5 for k in 'hswc'}]
    #isolation from 20 June 2021 reduced
    iso_vals7 = [{k:0.7 for k in 'hswc'}]
    #isolation from 16 July 2021 increased
    ####chnaged to 0.2 for fitting
    iso_vals8 = [{k:0.3 for k in 'hswc'}]
    #isolation from August 2021
    iso_vals9 = [{k:0.5 for k in 'hswc'}]
    #isolation from Sep 2021
    iso_vals10 = [{k:0.5 for k in 'hswc'}]

    #testing and isolation intervention
    interventions += [
        cv.test_prob(symp_prob=0.009, asymp_prob=0.0, symp_quar_prob=0.0, start_day=tc_day, end_day=te_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_april, asymp_prob=0.0, symp_quar_prob=0.0, start_day=te_day, end_day=tt_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_may, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tt_day, end_day=tti_day-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day, end_day=tti_day_july-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july, asymp_prob=0.00076, symp_quar_prob=0.0, start_day=tti_day_july, end_day=tti_day_august-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_august, end_day=tti_day_sep-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sep, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_sep, end_day=tti_day_oct-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_oct, asymp_prob=0.0028, symp_quar_prob=0.0, start_day=tti_day_oct, end_day=tti_day_nov-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_nov, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_nov, end_day=tti_day_dec-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_dec, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_dec, end_day=tti_day_jan-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_jan, asymp_prob=0.0063, symp_quar_prob=0.0, start_day=tti_day_jan, end_day=tti_day_feb-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_jan, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_feb, end_day=tti_day_march-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_march, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_march, end_day=tti_day_june21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_june21, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_june21, end_day=tti_day_july21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_july21, asymp_prob=0.004, symp_quar_prob=0.0, start_day=tti_day_july21, end_day=tti_day_august21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_august21, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_august21, end_day=tti_day_sep21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_sep21, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_sep21, end_day=tti_day_oct21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_oct21, asymp_prob=0.004, symp_quar_prob=0.0, start_day=tti_day_oct21, end_day=tti_day_nov21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_nov21, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_nov21, end_day=tti_day_dec21-1, test_delay=t_delay),
        cv.test_prob(symp_prob=s_prob_dec21, asymp_prob=0.008, symp_quar_prob=0.0, start_day=tti_day_dec21, test_delay=t_delay),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.8, 'w': 0.8, 'c': 0.1},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2020-06-01', end_day='2023-07-12',
                           quar_period=10),
        cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_july, 'vals': iso_vals1}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep, 'vals': iso_vals2}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_oct, 'vals': iso_vals3}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_nov, 'vals': iso_vals4}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_dec, 'vals': iso_vals5}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_march, 'vals': iso_vals6}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_june21, 'vals': iso_vals7}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_july21, 'vals': iso_vals8}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_august21, 'vals': iso_vals9}}),
        cv.dynamic_pars({'iso_factor': {'days': tti_day_sep21, 'vals': iso_vals10}})]
    
    def change_hosp(sim):
        if sim.t == tti_day_dec21:
            sim['dur']['sev2rec']['par1'] = 7
    interventions += [change_hosp]

    # Define the vaccines
    dose_pars = cvpar.get_vaccine_dose_pars()['az']
    dose_pars['interval'] = 7 * 8
    variant_pars = cvpar.get_vaccine_variant_pars()['az']
    variant_pars['omicron'] = 1/7 # PLACEHOLDER
    az_vaccine = sc.mergedicts({'label':'az_uk'}, sc.mergedicts(dose_pars, variant_pars)) 
    
    dose_pars = cvpar.get_vaccine_dose_pars()['pfizer']
    dose_pars['interval'] = 7 * 8
    variant_pars = cvpar.get_vaccine_variant_pars()['pfizer']
    variant_pars['omicron'] = 1/7 # PLACEHOLDER
    pfizer_vaccine = sc.mergedicts({'label':'pfizer_uk'}, sc.mergedicts(dose_pars, variant_pars))

    # Loop over vaccination in different ages
    for age,vx_phase in vx_rollout.items():
        vaccine = az_vaccine if (age > 40 and age < 65) else pfizer_vaccine
        vx_start_day = sim.day(vx_phase['start_day'])
        vx_end_day = vx_start_day + vx_phase['days_to_reach']
        days = np.arange(vx_start_day, vx_end_day)
        vx = cv.vaccinate_prob(vaccine=vaccine, days=days, subtarget=subtarget_dict[age], label=f'Vaccinate {age}')
        interventions += [vx]

    # Finally, update the parameters
    sim.update_pars(interventions=interventions, variants=variants)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    return sim


########################################################################
# Run calibration and scenarios
########################################################################
if __name__ == '__main__':

    # Make sim
    sim = make_sim(seed,beta)

    # Add analyzers
    n_doses = []
    dose_analyzer   = lambda sim: n_doses.append(sim.people.doses.copy())
    age_stats       = cv.daily_age_stats(states=['vaccinated', 'exposed', 'severe', 'dead'])
    analyzers       = [dose_analyzer, age_stats]
    sim.update_pars(analyzers=analyzers)
    sim.initialize()
    sim.run()

    # Do plotting
    if do_plot:
        sim.plot(to_plot=to_plot, do_save=True, do_show=False, fig_path=figfolder+'/England_test_01Dec_omic.png',
                  legend_args={'loc': 'upper left'}, axis_args={'hspace': 0.4}, interval=75, n_cols=2)
        sim.plot('variants', do_save=True, do_show=False, fig_path=figfolder+'/uk_strain_test_01Dec_omic.png')

        pl.figure()
        n_doses = np.array(n_doses)
        fully_vaccinated = (n_doses == 2).sum(axis=1)
        first_dose = (n_doses == 1).sum(axis=1)
#        boosted = (n_doses > 2).sum(axis=1)
        pl.stackplot(sim.tvec, first_dose, fully_vaccinated)#, boosted)
        pl.legend(['First dose', 'Fully vaccinated']) #, 'Boosted']);
        pl.savefig(figfolder+'/doses.png')

        daily_age = sim.get_analyzer(1)
        daily_age.plot(do_show=False)
        pl.savefig(figfolder+'/age_stats.png')
        daily_age.plot(total=True, do_show=False)
        pl.savefig(figfolder+'/age_stats_total.png')


