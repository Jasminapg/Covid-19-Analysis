'''
UK scenarios
'''

import sciris as sc
import numpy as np
import covasim as cv
import pylab as pl

# Check version
cv.check_version('0.30.3')
cv.git_info('covasim_version.json')

do_plot = 1
do_save = 1
do_show = 1
verbose = 1
seed    = 1

version   = 'v1'
date      = '2020may25'
folder    = f'results_transmisibility100_TIonly_{date}'
file_path = f'{folder}/phase_{version}' # Completed below
data_path = 'UK_Covid_cases_may21.xlsx'
pop_path  = f'{file_path}.pop'
fig_path  = f'{file_path}.png'
#ig_paths = [f'results/testing_scen_{i}.png' for i in range(3)]


start_day = sc.readdate('2020-01-21') # start_day = sc.readdate('2020-01-21') or start_day = sc.readdate('2020-02-04')
end_day   = sc.readdate('2021-05-31')
n_days    = (end_day -start_day).days

# Set the parameters
#quar_eff = 0.8
#quar_effs = {k:quar_eff for k in 'hwsc'}
total_pop = 67.86e6 # UK population size
pop_size = 100e3 # Actual simulated population
ratio = int(total_pop/pop_size)
pop_scale = ratio
pop_type = 'hybrid'
#100% transmissibility of kids also ps=0.0135 for May and June
pop_infected = 4500 # 4500 or 15000, depending on start date above
beta = 0.00765
cons = {'h':3.0, 's':20, 'w':20, 'c':20}
#50% transmissibility of kids also ps=0.1 for May and June
#pop_infected = 5000
#beta = 0.00525
#cons = {'h':3.0, 's':20, 'w':20, 'c':20}

pars = sc.objdict(
    pop_size     = pop_size,
    pop_infected = pop_infected//pop_scale,
    pop_scale    = pop_scale,
    pop_type     = pop_type,
    start_day    = start_day,
    n_days       = n_days,
    asymp_factor = 1.9,
    beta         = beta,
    contacts     = cons,
)

# Create the baseline simulation
sim = cv.Sim(pars=pars, datafile=data_path, popfile=pop_path, location='uk')
msim = cv.MultiSim(base_sim=sim) # Create using your existing sim as the base

# Interventions

#opening and closing schools intervention changing the h,s,w,c values and ti_start to
#account for changes in Table 1 in the ms
#baseline scenario

# Create the baseline simulation

#interventions = []
#intervention of some testing (tc) starts on 19th March and we run until 1st April when it increases
tc_start = '2020-03-16'
tc_day = (sc.readdate(tc_start)-start_day).days
#intervention of some testing (te) starts on 1st April and we run until 1st May when it increases
te_start = '2020-04-01'
te_day = (sc.readdate(tc_start)-start_day).days
#intervention of some testing (tt) starts on 15th May
tt_start = '2020-05-01'
tt_day = (sc.readdate(tt_start)-start_day).days
#intervention of testing and tracing and isolation (tti) starts on 1st June
tti_start = '2020-06-01'
tti_day= (sc.readdate(tti_start)-start_day).days
#schools interventions (ti) start
ti_start = '2021-04-17'
ti_day   = (sc.readdate(ti_start)-start_day).days
#change parameters here for difefrent schools opening strategies with society opening
#June opening with society opening
beta_days      = ['2020-02-14', '2020-03-16', '2020-03-23', '2020-04-30', '2020-05-15', '2020-06-08', '2020-07-01', '2020-07-22', '2020-09-02', '2020-10-28', '2020-11-01', '2020-12-23', '2021-01-03', '2021-02-17', '2021-02-21', '2021-04-06', ti_start]
beta_days      = [(sc.readdate(day)-start_day).days for day in beta_days]
h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.80, 0.80, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.70, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.80, 0.80, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90]
#June opening with only schools opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.80, 0.80, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]

#September opening with society opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.02, 0.02, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.30, 0.30, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.30, 0.30, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90]
#September opening with only schools opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.02, 0.02, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.30, 0.30, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]

#Phased opening with society opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.25, 0.70, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.70, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90]
#Phased opening with only schools opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.00, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.25, 0.70, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]

#Phased-delayed opening with society opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.02, 0.70, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70, 0.50, 0.70]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.70, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90, 0.50, 0.90]
#Phased-delayed opening with only schools opening
#h_beta_changes = [1.00, 1.00, 1.29, 1.29, 1.29, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00, 1.29, 1.00]
#s_beta_changes = [1.00, 0.90, 0.02, 0.02, 0.02, 0.02, 0.70, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 0.90, 0.00, 1.00]
#w_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]
#c_beta_changes = [0.90, 0.80, 0.20, 0.20, 0.20, 0.20, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40, 0.40]


h_beta = cv.change_beta(days=beta_days, changes=h_beta_changes, layers='h', do_plot=False)
s_beta = cv.change_beta(days=beta_days, changes=s_beta_changes, layers='s', do_plot=False)
w_beta = cv.change_beta(days=beta_days, changes=w_beta_changes, layers='w', do_plot=False)
c_beta = cv.change_beta(days=beta_days, changes=c_beta_changes, layers='c', do_plot=False)

#next two lines to save the intervention
interventions = [h_beta, w_beta, s_beta, c_beta]
sim.update_pars(interventions=interventions)

#Testing interventions
#testng strategy wth daily tests
#tests from data until 14th May
#daily_tests = sim.data['new_tests'] #test from data
#daily_tests = 30000
#symp_test = 1#odds ratio of symptomatic person testing
#tests = cv.test_num(daily_tests=daily_tests, symp_test=10, start_day=tc_day, end_day=tt_day)
#assumption on testing between 14th May and 1st June
#daily_tests2 = 100000
#symp_test2 = 1
#testsMay= cv.test_num(daily_tests=daily_tests2, symp_test=10, start_day=tt_day, end_day=tti_day)
#assumption on testing aftre 1st June
#daily_tests3 = 100000
#symp_test3 = 1
#testsJune= cv.test_num(daily_tests=daily_tests3, symp_test=10, start_day=tt_day, end_day=tti_day)
# testing strategy with probability assignment
#s_prob=% of sympomatic that are tested only as part of TI strategies; we fit s_prob_may to data
s_prob_march = 0.007
s_prob_april = 0.009
s_prob_may = 0.0135
s_prob_june =0.0135
a_prob = 0.0
#a_prob_june =0.0135
q_prob = 0.0
t_delay = 1.0

iso_vals = [{k:0.1 for k in 'hswc'}]

march_tests = cv.test_prob(symp_prob=s_prob_march,
                            asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                            start_day=tc_day, end_day=te_day, test_delay=t_delay)
april_tests = cv.test_prob(symp_prob=s_prob_april,
                           asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                           start_day=te_day, end_day=tt_day, test_delay=t_delay)
may_tests = cv.test_prob(symp_prob=s_prob_may,
                          asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                           start_day=tt_day, end_day=tti_day, test_delay=t_delay)
june_tests_symp = cv.test_prob(symp_prob=s_prob_june,
                          asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                          start_day=tti_day, test_delay=t_delay)
#from the onset (te_day) people with diagnosed positive are assumed likely to transmit as are immediately isolated so their transmission reduced by 90%
isolation = cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}) #starting day tt make diagnosed people d_eff less likely to transmis

#tracing in june
#t_eff_june = 0.0
#t_probs_june = {k:t_eff_june for k in 'hwsc'}
#trace_d = {'h':0, 's':1, 'w':1, 'c':2}
#ttq_june = cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d, start_day=tti_day)

interventions += [
     #h_beta, w_beta, s_beta, c_beta,
     #cv.test_num(daily_tests=daily_tests, symp_test=10, start_day=tc_day, end_day=tt_day),
     #cv.test_num(daily_tests=daily_tests2, symp_test=10, start_day=tt_day, end_day=tti_day),
     #cv.test_num(daily_tests=daily_tests3, symp_test=10, start_day=tti_day),
     cv.test_prob(symp_prob=s_prob_march,
                          asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                           start_day=tc_day, end_day=te_day, test_delay=t_delay),
     cv.test_prob(symp_prob=s_prob_april,
                          asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                           start_day=te_day, end_day=tt_day, test_delay=t_delay),
     cv.test_prob(symp_prob=s_prob_may,
                            asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                            start_day=tt_day, end_day=tti_day, test_delay=t_delay),
     cv.test_prob(symp_prob=s_prob_june,
                          asymp_prob=a_prob, symp_quar_prob=q_prob, asymp_quar_prob=q_prob,
                           start_day=tti_day, test_delay=t_delay),
     cv.dynamic_pars({'iso_factor': {'days': te_day, 'vals': iso_vals}}),
     #cv.dynamic_pars({'asymp_factor': {'days': tt_day, 'vals': 2.0}}),
     #cv.contact_tracing(trace_probs=t_probs_may, trace_time=trace_d, start_day=tt_day),
     #cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d, start_day=tti_day),
     #cv.dynamic_pars({'asymp_factor': {'days': tti_day, 'vals': 1.0}})
     #cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d, start_day=tti_day)
   ]
pars['interventions'] = [march_tests, april_tests, may_tests, june_tests_symp, isolation]
sim.update_pars(interventions=interventions)
for intervention in sim['interventions']:
    intervention.do_plot = False


#population-wide testing and tracing strategy from June
#testing in june
#s_prob_june_2 = 0.0
#a_prob_june_2 = 0.15
#q_prob_june = 0.0
#t_delay = 0.0
#june_tests_extra = cv.test_prob(symp_prob=s_prob_june_2,
 #                        asymp_prob=a_prob_june_2, symp_quar_prob=q_prob_june, asymp_quar_prob=q_prob_june,
  #                         start_day=tti_day, test_delay=t_delay)
#isolation_june_2 = cv.dynamic_pars({'iso_factor': {'days': tti_day, 'vals': iso_vals}}) #starting day tt make diagnosed people d_eff less likely to transmis

#tracing in june
#t_eff_june = 0.4
#t_probs_june = {k:t_eff_june for k in 'hwsc'}
#trace_d = {'h':0, 's':1, 'w':1, 'c':2}
#ttq_june_2 = cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d, start_day=tti_day)

#testing and isolation intervention
#interventions += [
 #    cv.test_prob(symp_prob=s_prob_june_2,
  #                       asymp_prob=a_prob_june_2, symp_quar_prob=q_prob_june, asymp_quar_prob=q_prob_june,
   #                        start_day=tti_day, test_delay=t_delay),
    # cv.contact_tracing(trace_probs=t_probs_june, trace_time=trace_d, start_day=tti_day),
     #cv.dynamic_pars({'iso_factor': {'days': tti_day, 'vals': iso_vals}})
  #]
#pars['interventions'] = [june_tests_extra, ttq_june_2, isolation_june_2]
#sim.update_pars(interventions=interventions)


# Changing kids' transmissability
sim.initialize() # Create the population
reduce_kids = True #set tgis to True to change the transmissibility numbers below
if reduce_kids:
    print('Reducing transmission among kids')
    children = sim.people.age<18 # Find people who are children
    child_inds = sc.findinds(children) # Turn the boolean array into a list of indices
    for lkey in sim.people.layer_keys(): # Loop over each layer
        child_contacts = np.isin(sim.people.contacts[lkey]['p1'], child_inds) # Find contacts where the source is a child
        child_contact_inds = sc.findinds(child_contacts) # Convert to indices
        sim.people.contacts[lkey]['beta'][child_contact_inds] = 1.0 # MODIFY TRANSMISSION
        #sim.people.contacts[lkey]['beta'][:] = 0.0 # MODIFY TRANSMISSION


if __name__ == '__main__':
    #msim = cv.MultiSim(n_runs=10)
    msim.run(n_runs=6) # Run with uncertainty
    msim.reduce() # "Reduce" the 10 sims into the statistical representation
    # results = msim.results # Use this instead of sim.results
    # msim.results['cum_deaths'].values.mean()
    # msim.results['cum_infectious'].values.mean()

    #r0 = msim.results('r_eff')
    #msim.plot() # Use this instead of sim.plot
    #msim.plot_result('cum_deaths', interval=30.5)
    #msim.plot_result('cum_infections',interval=30.5)
    #msim = cv.MultiSim([s1, s2])
    #msim.reduce()



    # Save the key figures

    msim.plot_result('r_eff', interval=60, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
    pl.xlim([10, 400]) # Trim off the beginning and end which are noisy
    pl.axhline(1.0, c=[0.2, 0.1, 0.8], alpha=0.3, lw=3) # Add a line for the R_eff = 1 cutoff
    pl.title('')
    pl.savefig('R_eff.png')

    msim.plot_result('cum_deaths', interval=60, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
    pl.title('')
    pl.savefig('Deaths.png')

    msim.plot_result('new_infections', interval=60, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
    pl.title('')
    pl.savefig('Infections.png')

    msim.plot_result('cum_diagnoses', interval=60, fig_args={'figsize':(12,7)}, axis_args={'left':0.15})
    pl.title('')
    pl.savefig('Diagnoses.png')




    # msim.plot_result('cum_tests')
    # pl.savefig('Test.png')
    ##to_plot[‘Health outcomes’].remove(‘cum_severe’)
    #sim.plot()
    #pl.savefig('Cases.png')
    #sim.to_excel('Baseline.xlsx')
    #msim.plot_result('cum_diagnoses')
    #pl.savefig('Diagnoses.png')

    #if do_plot:
     #   to_plot = cv.get_sim_plots()
      #  to_plot['Health outcomes'].remove('cum_severe')
       # fig = msim.plot(to_plot=to_plot, do_save=do_save, do_show=do_show, fig_path=fig_path, interval=60)


    # if do_save:
    #     msim.save(f'{file_path}.sim', keep_people=True)

    # if do_plot:
    #     for reskey in ['new_infections', 'cum_deaths']:
    #         fig = msim.plot(to_plot=[reskey], fig_args={'figsize':(12,7)}, do_save=do_save, fig_path=fig_path, interval=60)
    #         pl.title('')

    #to_plot = cv.get_sim_plots()
    #to_plot['Health outcomes'].remove('cum_severe')
    #sim.plot(to_plot=to_plot)

   # if do_plot:
        #to_plot = cv.get_sim_plots()
        #to_plot['Health outcomes'].remove('cum_severe')
        #sim.plot(to_plot=to_plot)
    #    fig = msim.plot(to_plot=to_plot,do_save=do_save, do_show=do_show, fig_path=fig_path, interval=60)
