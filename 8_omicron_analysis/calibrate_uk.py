import sciris as sc
import covasim as cv
import covasim.parameters as cvp
import pylab as pl
import numpy as np
 

########################################################################
# Settings and initialisation
########################################################################
# Check version
cv.check_version('>=3.1.0')
cv.git_info('covasim_version.json')

# Filepaths
data_path1 = 'England_Covid_cases_Nov272021.xlsx'
data_path2 = 'England_Covid_cases_Dec312021.xlsx'
resfolder = 'results'
figfolder = 'figs'
heatmap_file = 'heatmap_data.obj'


# Define what to run
whattorun = ['nov_quickfit',    # STEP 1: run a quick fit to make sure everything works
             'nov_fullfit',     # STEP 2: run the model until November 15 to demonstrate the fit to historical data pre-omicron
             'dec_sweeps',      # STEP 3: run sweeps over properties of omicron. CAUTION: slow to run, needs VMs
             'dec_quickfit',    # STEP 4: using known properites of omicron, run a quick fit to december data to make sure everything works
             'dec_fullfit',     # STEP 5: run the model until December 31 to demonstrate the fit to data after omicron
             'dec_project'      # STEP 6: project forward over school reopening scenarios.
             ][2]

# Saving and plotting settings depend on what you're running
settings = {'nov_quickfit': {'verbose':0.1,  'end_day': '2021-11-15', 'data_path': data_path1},
            'nov_fullfit':  {'verbose':0.01, 'end_day': '2021-11-15', 'data_path': data_path1},
            'dec_sweeps':   {'verbose':0.01, 'end_day': '2021-12-31', 'data_path': None},
            'dec_quickfit': {'verbose':0.1,  'end_day': '2021-12-31', 'data_path': data_path2},
            'dec_fullfit':  {'verbose':0.01, 'end_day': '2021-12-31', 'data_path': data_path2},
            'dec_project':  {'verbose':0.01, 'end_day': '2022-03-10', 'data_path': data_path2},
            }

seed    = 1
debug   = 0
start_day = '2020-01-20'
date_before_scens = settings['nov_fullfit']['end_day']
day_before_scens  = cv.day(date_before_scens, start_date=start_day)

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



########################################################################
# Define the vaccination rollout
########################################################################
# fitting data vaccine rollout in England using info from
# https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2021/07/COVID-19-weekly-announced-vaccinations-01-July-2021.pdf
# The arguments "final_uptake" and "days_to_reach" can be used to define a scale-up function over the
# duration of the vaccination campaign. However, these are currently not used, and a daily probability
# is used instead.
vx_rollout = {
    90: dict(start_age=90, end_age=100, start_day='2020-12-08', final_uptake=0.95, days_to_reach=90),
    85: dict(start_age=85, end_age=89, start_day='2020-12-10', final_uptake=0.95, days_to_reach=90),
    80: dict(start_age=80, end_age=84, start_day='2020-12-16', final_uptake=0.95, days_to_reach=90),
    75: dict(start_age=75, end_age=79, start_day='2021-01-11', final_uptake=0.95, days_to_reach=90),
    70: dict(start_age=70, end_age=74, start_day='2021-01-18', final_uptake=0.95, days_to_reach=90),
    65: dict(start_age=65, end_age=69, start_day='2021-02-15', final_uptake=0.90, days_to_reach=90),
    60: dict(start_age=60, end_age=64, start_day='2021-02-22', final_uptake=0.90, days_to_reach=90),
    55: dict(start_age=55, end_age=60, start_day='2021-03-01', final_uptake=0.88, days_to_reach=90),
    50: dict(start_age=50, end_age=59, start_day='2021-03-05', final_uptake=0.85, days_to_reach=60),
    45: dict(start_age=45, end_age=49, start_day='2021-03-13', final_uptake=0.80, days_to_reach=60),
    40: dict(start_age=40, end_age=44, start_day='2021-04-12', final_uptake=0.75, days_to_reach=60),
    35: dict(start_age=35, end_age=39, start_day='2021-05-03', final_uptake=0.80, days_to_reach=60),
    30: dict(start_age=30, end_age=34, start_day='2021-05-26', final_uptake=0.80, days_to_reach=60),
    25: dict(start_age=25, end_age=29, start_day='2021-06-08', final_uptake=0.80, days_to_reach=60),
    18: dict(start_age=18, end_age=24, start_day='2021-05-18', final_uptake=0.60, days_to_reach=90),
    16: dict(start_age=16, end_age=17, start_day='2021-08-16', final_uptake=0.40, days_to_reach=90),
    12: dict(start_age=12, end_age=15, start_day='2021-10-22', final_uptake=0.40, days_to_reach=90),
}

def set_subtargets(vx_phase):
  return lambda sim: cv.true((sim.people.age >= vx_phase['start_age']) * (sim.people.age < vx_phase['end_age']))

subtarget_dict = {}
for age, vx_phase in vx_rollout.items():
    vx_phase['daily_prob'] = 0.02
    # vx_phase['final_uptake'] / vx_phase['days_to_reach']
    subtarget_dict[age] = {'inds': set_subtargets(vx_phase),
                           'vals': vx_phase['daily_prob']}

########################################################################
# Define omicron parameters and ranges
########################################################################
# Estimates of omicron pars as of Dec 31
om_pars = sc.objdict()
om_pars.rel_beta=6.8
om_pars.rel_severe_prob=0.8
om_pars.rel_imm=0.2

# Omicron sweep parameters
def sweep_om_pars():
    om_pars = sc.objdict()
    om_pars.rel_severe_prob = 0.5 # np.random.choice([0.5, 1, 1.5])
    om_pars.rel_beta = np.random.uniform(2, 4)  # changes the relative transmissibility of omicron
    om_pars.rel_imm = np.random.uniform(0.1, 0.4)  # changes the relative immunity of omicron
    return om_pars


########################################################################
# Create the baseline simulation
########################################################################
 
def make_sim(seed, beta=0.0079, rel_beta=None, rel_severe_prob=None, rel_imm=None,
             verbose=None, end_day=None, data_path=None, meta=None):

    # Rename omicron parameters
    om_rel_beta = rel_beta
    om_rel_sev  = rel_severe_prob
    om_az_eff = om_pf_eff = om_boost_eff = om_rel_imm = rel_imm

    # Set the parameters
    pars = sc.objdict(
        scaled_pop      = 55.98e6,  # UK population size
        n_agents        = 100e3, # Actual simulated population
        pop_type        = 'hybrid',
        pop_infected    = 1000,
        beta            = beta,
        use_waning      = True,
        start_day       = start_day,
        end_day         = end_day,
        asymp_factor    = 2,
        contacts        = {'h':3.0, 's':20, 'w':20, 'c':20},
#        beta_layer   = {'h':3.0, 's':1.0, 'w':1.0, 'c':1.0}
        rescale         = True,
        rand_seed       = seed,
        verbose         = verbose,
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
                           '2021-06-19': [1.05, 0.63, 0.30, 0.70],
                           '2021-06-21': [1.05, 0.63, 0.30, 0.70],
                           #to fit data we need to increase testing and mixing from 22/06/2021                          
                           '2021-06-28': [1.05, 0.63, 0.30, 0.70],
                           '2021-07-05': [1.05, 0.63, 0.30, 0.70],
                           '2021-07-12': [1.05, 0.63, 0.30, 0.70],
                           #cases start to drop from middle of July
                           '2021-07-19': [1.05, 0.00, 0.30, 0.70],
                           #easing of socal distancing measures - delayed step 4
                           '2021-07-26': [1.05, 0.00, 0.30, 0.70],
                           '2021-08-02': [1.05, 0.00, 0.30, 0.70],
                           '2021-08-09': [1.05, 0.00, 0.30, 0.70],
                           '2021-08-16': [1.05, 0.00, 0.30, 0.70],
                           '2021-08-23': [1.05, 0.00, 0.30, 0.70],
                           #reopening schools in Sep 2021
                           '2021-09-07': [1.05, sbv_new, 0.30, 0.60],
                           '2021-09-15': [1.05, sbv_new, 0.30, 0.60],
                           '2021-09-29': [1.05, sbv_new, 0.30, 0.60],
                           '2021-10-15': [1.05, 0.40, 0.30, 0.50],
                           '2021-10-22': [1.05, 0.00, 0.30, 0.50],
                           '2021-10-29': [1.05, 0.00, 0.30, 0.50],
                           '2021-11-05': [1.05, sbv_new, 0.30, 0.50],
                           '2021-11-12': [1.05, sbv_new, 0.30, 0.50],
                           '2021-11-19': [1.05, sbv_new, 0.30, 0.50],
                           '2021-11-26': [1.05, sbv_new, 0.30, 0.50],
                           '2021-12-02': [1.05, sbv_new, 0.30, 0.50],
                           '2021-12-09': [1.05, sbv_new, 0.30, 0.50],
                           '2021-12-16': [1.05, sbv_new, 0.30, 0.50],
                           '2021-12-20': [1.05, 0.00, 0.30, 0.50],
                           '2021-12-31': [1.50, 0.00, 0.20, 0.50],
                           '2022-01-01': [1.50, 0.00, 0.20, 0.50],
                            #4thlockdown starts
                           #'2022-01-04': [1.10, 0.14, 0.20, 0.40],
                           #'2022-01-11': [1.05, 0.14, 0.20, 0.40],
                           #'2022-01-18': [1.05, 0.14, 0.30, 0.40],
                           #'2022-01-25': [1.05, 0.14, 0.30, 0.40],
                           #'2022-02-08': [1.05, 0.14, 0.30, 0.40],
                           #'2022-02-15': [1.05, 0.00, 0.20, 0.30],
                           #'2022-02-22': [1.05, 0.14, 0.30, 0.40],
                           #'2022-03-01': [1.10, 0.14, 0.30, 0.40],
                           #'2022-03-08': [1.05, 0.14, 0.30, 0.40],
                           #'2022-03-15': [1.05, 0.14, 0.30, 0.40],
                           #'2022-03-22': [1.05, 0.14, 0.30, 0.40],
                           #'2022-03-29': [1.05, 0.14, 0.30, 0.40],
                           #PlanB and schools open
                           '2022-01-04': [1.10, sbv_new, 0.30, 0.50],
                           '2022-01-11': [1.05, sbv_new, 0.30, 0.50],
                           '2022-01-18': [1.05, sbv_new, 0.30, 0.50],
                           '2022-01-30': [1.05, sbv_new, 0.30, 0.50],
                           '2022-02-08': [1.05, sbv_new, 0.30, 0.50],
                           '2022-02-15': [1.05, 0.00, 0.20, 0.30],
                           '2022-02-22': [1.05, sbv_new, 0.30, 0.50],
                           '2022-03-01': [1.10, sbv_new, 0.50, 0.50],
                           '2022-03-08': [1.05, sbv_new, 0.50, 0.50],
                           '2022-03-15': [1.05, sbv_new, 0.50, 0.50],
                           '2022-03-22': [1.05, sbv_new, 0.50, 0.50],
                           '2022-03-29': [1.05, sbv_new, 0.50, 0.50],
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
    b16172.p['rel_beta']         = 2.6
    b16172.p['rel_severe_prob']  = 0.2
    variants += [b16172]
    # Add Omicron from mid-November
    var_pars = sc.mergedicts(cvp.get_variant_pars(default=True), {'rel_beta': om_rel_beta,
                                                                  'rel_severe_prob': om_rel_sev})
    omicron = cv.variant(var_pars, label='omicron', days=np.arange(sim.day('2021-11-15'), sim.day('2021-11-30')), n_imports=4000)
    variants += [omicron]

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
    #s_prob_june21 = 0.11769
    s_prob_june21 = 0.19769
    #to match the drop in mid-July from optuna decline ine testing (or switched tracing off as alternative)
    s_prob_july21 = 0.06769
    #s_prob_august21 = 0.08769
    #s_prob_sep21 =0.09769
    #s_prob_oct21 =0.07769
    #s_prob_nov21 =0.11769
    #s_prob_dec21 =0.11769

    ###old
    #s_prob_july21 = 0.05769
    s_prob_august21 = 0.05769
    s_prob_sep21 =0.03769
    s_prob_oct21 =0.03769
    s_prob_nov21 =0.05769
    s_prob_dec21 =0.08769

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
    iso_vals7 = [{k:0.8 for k in 'hswc'}]
    #isolation from 16 July 2021 increased
    ####chnaged to 0.2 for fitting
    iso_vals8 = [{k:0.5 for k in 'hswc'}]
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
                           start_day='2020-06-01', end_day='2021-07-12',
                           quar_period=10),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.8, 'w': 0.8, 'c': 0.3},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2021-07-12', end_day='2021-08-02',
                           quar_period=10),
        cv.contact_tracing(trace_probs={'h': 1, 's': 0.8, 'w': 0.8, 'c': 0.1},
                           trace_time={'h': 0, 's': 1, 'w': 1, 'c': 2},
                           start_day='2021-08-02', end_day='2023-08-02',
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
        if sim.t == tti_day_august21:
            sim['dur']['sev2rec']['par1'] = 5.5


    #def change_hosp2(sim):
    #    if sim.t == tti_day_august21:
    #        sim['dur']['sev2rec']['par1'] = 5.5

    interventions += [change_hosp]

    # Define the vaccines
    dose_pars = cvp.get_vaccine_dose_pars()['az']
    dose_pars['interval'] = 7 * 8
    variant_pars = cvp.get_vaccine_variant_pars()['az']
    variant_pars['omicron'] = om_az_eff # Efficacy of AZ against omicron
    az_vaccine = sc.mergedicts({'label':'az_uk'}, sc.mergedicts(dose_pars, variant_pars))
    
    dose_pars = cvp.get_vaccine_dose_pars()['pfizer']
    dose_pars['interval'] = 7 * 8
    variant_pars = cvp.get_vaccine_variant_pars()['pfizer']
    variant_pars['omicron'] = om_pf_eff # Efficacy of Pfizer against omicron
    pfizer_vaccine = sc.mergedicts({'label':'pfizer_uk'}, sc.mergedicts(dose_pars, variant_pars))

    # Loop over vaccination in different ages
    for age,vx_phase in vx_rollout.items():
        vaccine = az_vaccine if (age > 40 and age < 65) else pfizer_vaccine
        vx_start_day = sim.day(vx_phase['start_day'])
        vx_end_day = vx_start_day + vx_phase['days_to_reach']
        days = np.arange(vx_start_day, vx_end_day)

        vx = cv.vaccinate_prob(vaccine=vaccine, days=days, subtarget=subtarget_dict[age], label=f'Vaccinate {age}')
        interventions += [vx]

    # Define booster as a custom vaccination but with parameters like pfizer and moderna as these are used in England as boostes
    booster = dict(
        nab_eff=sc.dcp(sim['nab_eff']),
        nab_init=None,
        nab_boost=3,
        doses=1,
        interval=None,
        wild=1.0,
        alpha=1 / 2.3,
        beta=1 / 9,
        gamma=1 / 8,
        delta=1 / 3,
        omicron=om_boost_eff  # Efficacy of the booster against omicron
    )

    booster_target = {'inds': lambda sim: cv.true(sim.people.doses != 2),
                      'vals': 0}  # Only give boosters to people who have had 2 doses

    def num_boosters(sim):
        if sim.t < sim.day('2021-10-01'):                      return 0
        if sim.day('2021-10-01') < sim.day('2021-12-01'):      return 130_000
        else:                                                  return 150_000  # Just use a placeholder value

    booster = cv.vaccinate_num(vaccine=booster, label='booster', sequence='age', subtarget=booster_target, num_doses=num_boosters, booster=True)
    interventions += [booster]

    # Finally, update the parameters
    sim.update_pars(interventions=interventions, variants=variants)
    for intervention in sim['interventions']:
        intervention.do_plot = False

    # Initialize then add immunity escape parameters
    sim.meta = meta

    print(f'Initializing sim {sim.meta.count:5g} {str(sim.meta.vals.values()):40s}')
    sim.initialize()
    print(f'Finished initializing sim {sim.meta.count:5g} {str(sim.meta.vals.values()):40s}')

    # Now vary omicron's immunity
    immunity = sim['immunity']
    beta_imm = cvp.get_cross_immunity()['beta'] # Assume that omicron is like beta
    variant_mapping = sim['variant_map']
    for i in range(len(immunity)):
        if i != len(immunity) - 1:
            immunity[len(immunity) - 1, i] = beta_imm[variant_mapping[i]] * om_rel_imm
            immunity[i, len(immunity) - 1] = beta_imm[variant_mapping[i]] * om_rel_imm
    sim['immunity'] = immunity


    return sim


def run_sim(sim, do_shrink=True):
    ''' Run a simulation '''

    print(f'Running sim {sim.meta.count:5g} of {sim.meta.n_sims:5g} {str(sim.meta.vals.values()):40s}')
    sim.run(until=day_before_scens) # Run the partial sim
    sim.run() # Run the rest of the sim
    if do_shrink: sim.shrink()

    return sim


def make_msims(sims):
    ''' Take a slice of sims and turn it into a multisim '''
    msim = cv.MultiSim(sims)
    msim.reduce(use_mean=True)
    draw, seed = sims[0].meta.inds
    for s,sim in enumerate(sims): # Check that everything except seed matches
        assert draw == sim.meta.inds[0]
        assert (s==0) or seed != sim.meta.inds[1]
    msim.meta = sc.objdict()
    msim.meta.inds = [draw]
    msim.meta.vals = sc.dcp(sims[0].meta.vals)
    msim.meta.vals.pop('seed')
    print(f'Processing multisim {msim.meta.vals.values()}...')

    return msim


########################################################################
# Run calibration and scenarios
# whattorun = ['nov_quickfit',    # STEP 1: run a quick fit to make sure everything works
#              'nov_fullfit',     # STEP 2: run the model until November 15 to demonstrate the fit to historical data pre-omicron
#              'dec_sweeps',      # STEP 3: run sweeps over properties of omicron. CAUTION: slow to run, needs VMs
#              'dec_quickfit',    # STEP 4: using known properites of omicron, run a quick fit to december data to make sure everything works
#              'dec_fullfit',     # STEP 5: run the model until December 31 to demonstrate the fit to data after omicron
#              'dec_project'      # STEP 6: project forward over school reopening scenarios.
#              ]
########################################################################
if __name__ == '__main__':

    if whattorun in ['nov_quickfit', 'dec_quickfit']:
        kwargs = sc.mergedicts(om_pars, settings[whattorun])
        sim = make_sim(seed=seed, **kwargs)
        sim.run()
        sim.plot(to_plot=to_plot)

    elif whattorun in ['nov_fullfit', 'dec_fullfit', 'dec_project']:
        kwargs = sc.mergedicts(om_pars, settings[whattorun])
        s0 = make_sim(seed=seed, **kwargs)
        sims = []
        for seed in range(4):
            sim = s0.copy()
            sim['rand_seed'] = seed
            sim.set_seed()
            sim.label = f"Sim {seed}"
            sims.append(sim)

        msim = cv.MultiSim(sims)
        msim.run()
        msim.reduce()
        msim.plot(to_plot=to_plot)

    elif whattorun=='dec_sweeps':
        n_seeds = [5, 1][debug]
        n_draws = [300, 4][debug]
        n_sims = n_seeds * n_draws
        count = 0
        ikw = []
        T = sc.tic()

        # Make sims
        sc.heading('Making sims...')
        for draw in range(n_draws):
            om_pars = sweep_om_pars()
            for seed in range(n_seeds):
                print(f'Creating arguments for sim {count} of {n_sims}...')
                count += 1
                meta = sc.objdict()
                meta.count = count
                meta.n_sims = n_sims
                meta.inds = [draw, seed]
                meta.vals = sc.objdict(sc.mergedicts(om_pars, dict(seed=seed)))
                ikw.append(sc.dcp(meta.vals))
                ikw[-1].meta = meta

        kwargs = settings[whattorun]
        sim_configs = sc.parallelize(make_sim, iterkwargs=ikw, kwargs=kwargs)

        # Run sims
        sc.heading('Finished initializing; should start running NOW!...')
        all_sims = sc.parallelize(run_sim, iterarg=sim_configs, ncpus=48)
        sims = np.empty((n_draws, n_seeds), dtype=object)
        for sim in all_sims:  # Unflatten array
            draw, seed = sim.meta.inds
            sims[draw, seed] = sim

        # Convert to msims
        all_sims_semi_flat = []
        for draw in range(n_draws):
            sim_seeds = sims[draw, :].tolist()
            all_sims_semi_flat.append(sim_seeds)
        msims = np.empty(n_draws, dtype=object)
        all_msims = sc.parallelize(make_msims, iterarg=all_sims_semi_flat)
        for msim in all_msims:  # Unflatten array
            draw = msim.meta.inds
            msims[draw] = msim

        # Do processing and store results
        variables = ['cum_infections', 'cum_severe', 'cum_deaths']
        d = sc.objdict()
        d.rel_beta = []
        d.rel_imm = []
        d.rel_sev = []
        for v in variables: d[v] = []
        for msim in all_msims:
            d.rel_beta.append(msim.meta.vals['rel_beta'])
            d.rel_imm.append(msim.meta.vals['rel_imm'])
            d.rel_sev.append(msim.meta.vals['rel_severe_prob'])
            for v in variables:
                d[v].append(msim.results[v].values[-1] - msim.results[v].values[day_before_scens])
            sc.saveobj(heatmap_file, d)
        sc.toc(T)




