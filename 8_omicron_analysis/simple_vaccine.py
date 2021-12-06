import covasim as cv
import numpy as np
import covasim.parameters as cvp
import sciris as sc

vx_ages = [75, 60, 50, 45, 40, 30, 25, 18, 16, 12]
vx_duration = 14 # Number of days of vaccine rollout
vx_scens = [0,1,2] # Define the vaccination scenarios

# Define ages and start days
vx_rollout = {
    75: dict(start_age=75, end_age=100, start_day='2020-12-20'),
    60: dict(start_age=60, end_age=75,  start_day='2021-01-28'),
    50: dict(start_age=50, end_age=60,  start_day='2021-02-10'),
    45: dict(start_age=45, end_age=50,  start_day='2021-03-20'),
    40: dict(start_age=40, end_age=45,  start_day='2021-04-10'),
    30: dict(start_age=30, end_age=40,  start_day='2021-05-10'),
    25: dict(start_age=25, end_age=30,  start_day='2021-06-10'),
    18: dict(start_age=18, end_age=25,  start_day='2021-06-30'),
    16: dict(start_age=16, end_age=18,  start_day='2021-08-10'),
    12: dict(start_age=12, end_age=15,  start_day='2021-09-01'),
    #5: dict(start_age=5, end_age=11,  start_day='2022-12-01'),
}

# Define vaccination probabilities for each scenario
scendata = {
    # Scen 0     1     2
    75: [0.95, 0.05, 0.95],
    60: [0.95, 0.05, 0.95],
    50: [0.90, 0.05, 0.90],
    45: [0.90, 0.20, 0.90],
    40: [0.80, 0.25, 0.90],
    35: [0.80, 0.45, 0.90],
    30: [0.80, 0.45, 0.90],
    25: [0.50, 0.40, 0.90],
    18: [0.50, 0.40, 0.90],
    16: [0.30, 0.40, 0.90],
    12: [0.30, 0.40, 0.70],
    #5:  [0.00, 0.60, 0.70],
}

def subtarget(sim, age=None, vx_scenario=None):
    rollout = vx_rollout[age]
    inds = cv.true((sim.people.age >= rollout['start_age']) * (sim.people.age < rollout['end_age']))
    key = f'subtarget_{age}'
    if not hasattr(sim, key):
        prob = scendata[age][vx_scenario]
        vx_inds = cv.binomial_filter(prob, inds) 
        setattr(sim, key, vx_inds)
    else:
        vx_inds = getattr(sim, key)
        inds = np.setdiff1d(inds, vx_inds)
    return {'inds': inds, 'vals': 0.65*np.ones(len(inds))}
#output = dict(inds=inds, vals=vals)
        #return output 

# Pre-define all of the subtargeting functions
subtargets = {}
for vx_scen in vx_scens:
    subtargets[vx_scen] = {}
    for age in vx_ages:
        subtargeting_function = lambda sim: subtargets(sim, age=age, vx_scenario=vx_scen) # "Pre-fill" age and scenario data so the sim is the only input
        subtargets[vx_scen][age] = subtargeting_function
#def vaccinate_by_age(sim):
#        young1  = cv.true(sim.people.age < 18) # cv.true() returns indices of people matching this condition, i.e. people under 50
#        young2 = cv.true((sim.people.age >= 18) * (sim.people.age < 25)) # Multiplication means "and" here
#        young3 = cv.true((sim.people.age >= 25) * (sim.people.age < 40)) # Multiplication means "and" here
#        middle1 = cv.true((sim.people.age >= 40) * (sim.people.age < 50)) # Multiplication means "and" here
#        middle2 = cv.true((sim.people.age >= 50) * (sim.people.age < 65)) # Multiplication means "and" here
#        old1 = cv.true((sim.people.age >= 65) * (sim.people.age < 75)) # Multiplication means "and" here
#        old2    = cv.true(sim.people.age > 75)
#        inds = sim.people.uid # Everyone in the population -- equivalent to np.arange(len(sim.people))
#        vals = np.ones(len(sim.people)) # Create the array
#        vals[young1] = 0.3 # 30% probability for people <18
#        vals[young2] = 0.4 # 40% probability for people >18 and <25
#        vals[young3] = 0.6 # 60% probability for people >25 and <40
#        vals[middle1] = 0.7 # 70% probability for people 40-50
#        vals[middle2] = 0.7 # 70% probability for people 50-65
#        vals[old1] = 0.9 # 90% probability for people 65-75
#        vals[old2] = 0.9 # 90% probability for people >75
#        #vaccine[young] = 'pfizer'
#        output = dict(inds=inds, vals=vals)
#        return output 


dose_pars = cvp.get_vaccine_dose_pars()['az']
dose_pars['interval'] = 7 * 8
variant_pars = cvp.get_vaccine_variant_pars()['az']
az_vaccine = sc.mergedicts({'label':'az_uk'}, sc.mergedicts(dose_pars, variant_pars)) 
    
dose_pars = cvp.get_vaccine_dose_pars()['pfizer']
dose_pars['interval'] = 7 * 8
variant_pars = cvp.get_vaccine_variant_pars()['pfizer']
pfizer_vaccine = sc.mergedicts({'label':'pfizer_uk'}, sc.mergedicts(dose_pars, variant_pars))

for age in vx_ages:
        vaccine = az_vaccine if (age > 40 and age < 65) else pfizer_vaccine
        subtarget = subtargets[vx_scen][age]
        vx_start_day = sim.day(vx_rollout[age]['start_day'])
        vx_end_day = vx_start_day + vx_duration
        days = np.arange(vx_start_day, vx_end_day)
        vx = cv.vaccinate_prob(vaccine=vaccine, subtarget=subtarget, days=days, prob=0.01)
        #vx = cv.vaccinate_prob(vaccine=vaccine, days=days, prob=0.01)
        #x = cv.vaccinate(vaccine=vaccine, days=days, rel_sus=0.6, rel_symp=0.8, subtarget=subtarget)

        interventions += [vx]

# Define the vaccine
#vaccine = cv.simple_vaccine(days=20, rel_sus=0.8, rel_symp=0.06, subtarget=vaccinate_by_age)

#vaccine = cv.simple_vaccine(days=20, prob=0.1, subtarget=dict(inds=lambda sim: cv.true(sim.people.age>50), vals=0.9))

# Define the number of boosters
#def num_boosters(sim):
#    if sim.t < 50: # None over the first 50 days
#        return 0
#    else:
#        return 50 # Then 100/day thereafter

# Only give boosters to people who have had 2 doses
#booster_target  = {'inds': lambda sim: cv.true(sim.people.doses != 2), 'vals': 0}
#booster = cv.vaccinate_prob(vaccine=vaccine, subtarget=booster_target, booster=True, num_doses=num_boosters)
#interventions +=[booster]

#update interventions
sim.update_pars(interventions=interventions)

sim = cv.Sim(interventions=interventions, pars=pars)
# Create, run, and plot the simulations
#sim1 = cv.Sim(label='Baseline')
#sim2 = cv.Sim(interventions=vaccine, label='With age-targeted vaccine')
#sim3 = cv.Sim(interventions=booster, label='With age-targeted vaccine and boosters')
#msim = cv.MultiSim([sim1, sim2, sim3])
msim.run()
msim.plot()

# Define sequence based vaccination
#pfizer = cv.vaccinate_num(vaccine='pfizer', sequence=prioritize_by_age, num_doses=100)
#sim = cv.Sim(
#    pars=pars,
#    interventions=pfizer,
#    analyzers=lambda sim: n_doses.append(sim.people.doses.copy())
#)
#sim.run()

#pl.figure()
#n_doses = np.array(n_doses)
#fully_vaccinated = (n_doses == 2).sum(axis=1)
#first_dose = (n_doses == 1).sum(axis=1)
#pl.stackplot(sim.tvec, first_dose, fully_vaccinated)
#pl.legend(['First dose', 'Fully vaccinated'])