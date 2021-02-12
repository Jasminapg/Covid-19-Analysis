import covasim as cv
import sciris as sc
import numpy as np
from covasim import base as cvb
from covasim import defaults as cvd
from covasim import utils as cvu

from covasim.interventions import process_days, find_day, get_subtargets, process_daily_data


class record_doses(cv.Analyzer):
    def __init__(self, vacc_class=None, **kwargs):
        super().__init__(**kwargs)
        self.vacc_class = vacc_class

    def initialize(self, sim):
        sim.results.update({'new_doses': cvb.Result('New doses', npts=sim['n_days'] + 1,
                                                         scale=True)})
        self.initialized = True
        return

    def apply(self, sim):

        # apply on last day
        if sim.t == sim['n_days']:
            for intv in sim['interventions']:
                if isinstance(intv, self.vacc_class):
                    for entry in intv.vaccination_dates:
                        if len(entry) > 0:
                            for day in entry:
                                if day <= sim['n_days']:
                                    sim.results['new_doses'].values[day] += 1

        return

class record_dose_flows(cv.Analyzer):
    def __init__(self, vacc_class=None, **kwargs):
        super().__init__(**kwargs)
        self.vacc_class = vacc_class

    def initialize(self, sim):
        sim.results.update({'n_dose_0': cvb.Result('No doses', npts=sim['n_days'] + 1,
                                                         scale=True)})
        sim.results.update({'n_dose_1': cvb.Result('1 dose', npts=sim['n_days'] + 1,
                                                         scale=True)})
        sim.results.update({'n_dose_2': cvb.Result('2 dose', npts=sim['n_days'] + 1,
                                                         scale=True)})
        self.initialized = True
        return


    def apply(self, sim):
        # apply on last day
        if sim.t == sim['n_days']:
            for intv in sim['interventions']:
                if isinstance(intv, self.vacc_class):
                    dose_counter = np.zeros((sim['n_days'] + 1, 3), dtype=cv.default_int)
                    dose_counter[0, 0] = sim.n
                    for intv in sim['interventions']:
                        if isinstance(intv, self.vacc_class):
                            for person in intv.vaccination_dates:
                                for ix, entry in enumerate(person):
                                    dose_counter[entry, ix] += -1
                                    dose_counter[entry, ix + 1] += 1
                    dose_counter = np.cumsum(dose_counter, axis=0)

                    sim.results['n_dose_0'].values[:] = dose_counter[:, 0]
                    sim.results['n_dose_1'].values[:] = dose_counter[:, 1]
                    sim.results['n_dose_2'].values[:] = dose_counter[:, 2]

        return

class dose_scheduler(cv.Intervention):
    '''
    Scheduler for doses

    To use update scheduler dictionary with key for each day and value list of {'inds', and 'rel_sys', etc}
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Initialize the Intervention object
        self._store_args()  # Store the input arguments so the intervention can be recreated
        self.scheduler = dict()

    def initialize(self, sim):
        self.initialized = True
        return

    def apply(self, sim):
        if sim.t in self.scheduler.keys():
            for schedule in self.scheduler[sim.t]:
                # pop out inds
                vacc_inds = schedule.pop('inds', np.array([], cvd.default_int))
                # look through rel factors
                for k, v in schedule.items():
                    sim.people[k][vacc_inds] = v
            # clean up
            self.scheduler.pop(sim.t)
        return

class schedule_vaccine_effect(cv.Intervention):
    '''
    Scheduler for vaccine effect

    To use update scheduler dictionary with key for each day and value list of {'inds', and 'rel_sys', etc}
    '''

    def __init__(self, **kwargs):
        super().__init__(**kwargs)  # Initialize the Intervention object
        self._store_args()  # Store the input arguments so the intervention can be recreated
        self.scheduler = dict()

    def initialize(self, sim):
        self.initialized = True
        return

    def apply(self, sim):
        if sim.t in self.scheduler.keys():
            for schedule in self.scheduler[sim.t]:
                # pop out inds
                vacc_inds = schedule.pop('inds', np.array([], cvd.default_int))
                # look through rel factors
                for k, v in schedule.items():
                    sim.people[k][vacc_inds] *= v
            # clean up
            self.scheduler.pop(sim.t)
        return

class two_dose_daily_delayed(cv.Intervention):
    '''Two dose vaccine with dose supply requirement and interval before consideration of next dose'''
    def __init__(self, daily_vaccines, prob=1.0, rel_symp=0.0, rel_trans=1.0, take_prob=1.0, delay=7*7, dose_delay=14,
                 age_priority=75, cumulative=[0.5, 1.0], dose_priority=[1.0, 5.0], start_day=0, end_day=None, **kwargs):
        super().__init__(**kwargs)  # Initialize the Intervention object
        self._store_args()  # Store the input arguments so the intervention can be recreated
        self.daily_vaccines = daily_vaccines # Should be a list of length matching time
        self.prob = prob
        self.rel_symp = rel_symp
        self.rel_trans = rel_trans
        self.take_prob = take_prob
        self.age_priority = age_priority
        self.delay = cvd.default_int(delay)
        self.dose_delay = cvd.default_int(dose_delay)
        self.dose_priority = np.array(dose_priority, dtype=cvd.default_float)
        if cumulative in [0, False]:
            cumulative = [1,0] # First dose has full efficacy, second has none
        elif cumulative in [1, True]:
            cumulative = [1] # All doses have full efficacy
        self.cumulative = np.array(cumulative, dtype=cvd.default_float) # Ensure it's an array
        self.start_day   = start_day
        self.end_day     = end_day

    def initialize(self, sim):
        ''' Fix the dates and store the vaccinations '''
        # Handle days
        self.start_day   = sim.day(self.start_day)
        self.end_day     = sim.day(self.end_day)
        self.days        = [self.start_day, self.end_day]

        # Process daily data
        self.daily_vaccines = process_daily_data(self.daily_vaccines, sim, self.start_day)

        # Ensure we have the dose scheduler
        flag = True
        for intv in sim['interventions']:
            if isinstance(intv, dose_scheduler):
                flag = False
        if flag:
            sim['interventions'] += [dose_scheduler()]

        # Save
        self.orig_rel_trans    = sc.dcp(sim.people.rel_trans) # Keep a copy of pre-vaccination transmission
        self.orig_symp_prob    = sc.dcp(sim.people.symp_prob) # ...and symptom probability

        # Initialize vaccine info
        self.vaccinations = np.zeros(sim.n, dtype=cvd.default_int)
        self.vaccine_take = np.zeros(sim.n, dtype=np.bool)
        self.vaccination_dates = [[] for p in range(sim.n)]  # Store the dates when people are vaccinated
        sim.results['new_doses'] = cvb.Result(name='New Doses', npts=sim['n_days']+1, color='#ff00ff')
        self.initialized = True

        return

    def apply(self, sim):
        ''' Perform vaccination '''

        t = sim.t
        if t < self.start_day:
            return
        elif self.end_day is not None and t > self.end_day:
            return

        # Check that there are still vaccines
        rel_t = t - self.start_day
        if rel_t < len(self.daily_vaccines):
            n_vaccines = sc.randround(self.daily_vaccines[rel_t]/sim.rescale_vec[t]) # Correct for scaling that may be applied by rounding to the nearest number of tests
            if not (n_vaccines and np.isfinite(n_vaccines)): # If there are no doses today, abort early
                return
            else:
                if sim.rescale_vec[t] != sim['pop_scale']:
                    raise RuntimeError('bad rescale time')
        else:
            return

        vacc_probs = np.ones(sim.n) # Begin by assigning equal vaccine weight (converted to a probability) to everyone

        # Remove minors
        ppl = sim.people
        inds0 = cv.true(ppl.age <= 18)
        vacc_probs[inds0] *= 0

        # add age priority
        inds1 = cv.true(ppl.age >= self.age_priority)
        vacc_probs[inds1] *= 10

        # Handle scheduling
        # first dose:
        vacc_probs[self.vaccinations == 0] *= self.dose_priority[0]
        # time between first and second dose:
        no_dose = [sim.t < (d[0] + self.delay) if len(d) > 0 else False for d in self.vaccination_dates]
        vacc_probs[no_dose] *= 0
        # time available for second dose:
        second_dose = [sim.t >= (d[0] + self.delay) if len(d) > 0 else False for d in self.vaccination_dates]
        vacc_probs[second_dose] *= self.dose_priority[1]

        # Don't give dose 2 people who have had more than 1
        vacc_inds = cvu.true(self.vaccinations > 1)
        vacc_probs[vacc_inds] = 0.0

        # Now choose who gets vaccinated and vaccinate them
        n_vaccines = min(n_vaccines, (vacc_probs!=0).sum()) # Don't try to vaccinate more people than have nonzero vaccination probability
        all_vacc_inds = cvu.choose_w(probs=vacc_probs, n=n_vaccines, unique=True) # Choose who actually tests
        sim.results['new_doses'][t] += len(all_vacc_inds)

        # Did the vaccine take?
        vacc_take_inds = all_vacc_inds[np.logical_or(cvu.n_binomial(self.take_prob, len(all_vacc_inds)) & (self.vaccinations[all_vacc_inds] == 0),
                                           self.vaccine_take[all_vacc_inds] & (self.vaccinations[all_vacc_inds] == 1))]
        self.vaccine_take[vacc_take_inds] = True

        # Calculate the effect per person
        vacc_doses = self.vaccinations[vacc_take_inds]  # Calculate current doses
        eff_doses = np.minimum(vacc_doses, len(self.cumulative) - 1)  # Convert to a valid index
        vacc_eff = self.cumulative[eff_doses]  # Pull out corresponding effect sizes
        rel_trans_eff = (1.0 - vacc_eff) + vacc_eff * self.rel_trans
        rel_symp_eff = (1.0 - vacc_eff) + vacc_eff * self.rel_symp

        # Apply the vaccine to people
        # schedule dose effect
        for intv in sim['interventions']:
            if isinstance(intv, dose_scheduler):
                schedule = {'inds': vacc_take_inds, 'rel_trans':self.orig_rel_trans[vacc_take_inds]*rel_trans_eff,
                                                         'symp_prob':self.orig_symp_prob[vacc_take_inds]*rel_symp_eff}
                schedule_day = sim.t + self.dose_delay
                if schedule_day not in intv.scheduler:
                    intv.scheduler.update({schedule_day: [schedule]})
                else:
                    intv.scheduler[schedule_day].append(schedule)

        self.vaccinations[all_vacc_inds] += 1
        for v_ind in all_vacc_inds:
            self.vaccination_dates[v_ind].append(sim.t)

        return

    def shrink(self):
        self.vaccination_dates = None
        self.vaccinations = None
        self.orig_rel_trans = None
        self.orig_symp_prob = None


class two_dose_daily(cv.Intervention):
    '''Two dose vaccine with dose supply requirement and interval before consideration of next dose'''
    def __init__(self, daily_vaccines, prob=1.0, rel_symp=0.0, rel_trans=1.0, take_prob=1.0, delay=21,
                 age_priority=75, cumulative=[0.5, 1.0], dose_priority=[1.0, 5.0], start_day=0, end_day=None, **kwargs):
        super().__init__(**kwargs)  # Initialize the Intervention object
        self._store_args()  # Store the input arguments so the intervention can be recreated
        self.daily_vaccines = daily_vaccines # Should be a list of length matching time
        self.prob = prob
        self.rel_symp = rel_symp
        self.rel_trans = rel_trans
        self.take_prob = take_prob
        self.age_priority = age_priority
        self.delay = cvd.default_int(delay)
        self.dose_priority = np.array(dose_priority, dtype=cvd.default_float)
        if cumulative in [0, False]:
            cumulative = [1,0] # First dose has full efficacy, second has none
        elif cumulative in [1, True]:
            cumulative = [1] # All doses have full efficacy
        self.cumulative = np.array(cumulative, dtype=cvd.default_float) # Ensure it's an array
        self.start_day   = start_day
        self.end_day     = end_day

    def initialize(self, sim):
        ''' Fix the dates and store the vaccinations '''
        # Handle days
        self.start_day   = sim.day(self.start_day)
        self.end_day     = sim.day(self.end_day)
        self.days        = [self.start_day, self.end_day]

        # Process daily data
        self.daily_vaccines = process_daily_data(self.daily_vaccines, sim, self.start_day)

        # Save
        self.orig_rel_trans    = sc.dcp(sim.people.rel_trans) # Keep a copy of pre-vaccination transmission
        self.orig_symp_prob    = sc.dcp(sim.people.symp_prob) # ...and symptom probability

        # Initialize vaccine info
        self.vaccinations = np.zeros(sim.n, dtype=cvd.default_int)
        self.vaccine_take = np.zeros(sim.n, dtype=np.bool)
        self.vaccination_dates = [[] for p in range(sim.n)]  # Store the dates when people are vaccinated
        sim.results['new_doses'] = cvb.Result(name='New Doses', npts=sim['n_days']+1, color='#ff00ff')
        self.initialized = True

        return

    def apply(self, sim):
        ''' Perform vaccination '''

        t = sim.t
        if t < self.start_day:
            return
        elif self.end_day is not None and t > self.end_day:
            return

        # Check that there are still vaccines
        rel_t = t - self.start_day
        if rel_t < len(self.daily_vaccines):
            n_vaccines = sc.randround(self.daily_vaccines[rel_t]/sim.rescale_vec[t]) # Correct for scaling that may be applied by rounding to the nearest number of tests
            if not (n_vaccines and np.isfinite(n_vaccines)): # If there are no doses today, abort early
                return
            else:
                if sim.rescale_vec[t] != sim['pop_scale']:
                    raise RuntimeError('bad rescale time')
        else:
            return

        vacc_probs = np.ones(sim.n) # Begin by assigning equal vaccine weight (converted to a probability) to everyone

        # Remove minors
        ppl = sim.people
        inds0 = cv.true(ppl.age <= 18)
        vacc_probs[inds0] *= 0

        # add age priority
        inds1 = cv.true(ppl.age >= self.age_priority)
        vacc_probs[inds1] *= 10

        # Handle scheduling
        # first dose:
        vacc_probs[self.vaccinations == 0] *= self.dose_priority[0]
        # time between first and second dose:
        no_dose = [sim.t < (d[0] + self.delay) if len(d) > 0 else False for d in self.vaccination_dates]
        vacc_probs[no_dose] *= 0
        # time available for second dose:
        second_dose = [sim.t >= (d[0] + self.delay) if len(d) > 0 else False for d in self.vaccination_dates]
        vacc_probs[second_dose] *= self.dose_priority[1]

        # Don't give dose 2 people who have had more than 1
        vacc_inds = cvu.true(self.vaccinations > 1)
        vacc_probs[vacc_inds] = 0.0

        # Now choose who gets vaccinated and vaccinate them
        n_vaccines = min(n_vaccines, (vacc_probs!=0).sum()) # Don't try to vaccinate more people than have nonzero vaccination probability
        all_vacc_inds = cvu.choose_w(probs=vacc_probs, n=n_vaccines, unique=True) # Choose who actually tests
        sim.results['new_doses'][t] += len(all_vacc_inds)

        # Did the vaccine take?
        vacc_take_inds = all_vacc_inds[np.logical_or(cvu.n_binomial(self.take_prob, len(all_vacc_inds)) & (self.vaccinations[all_vacc_inds] == 0),
                                           self.vaccine_take[all_vacc_inds] & (self.vaccinations[all_vacc_inds] == 1))]
        self.vaccine_take[vacc_take_inds] = True

        # Calculate the effect per person
        vacc_doses = self.vaccinations[vacc_take_inds]  # Calculate current doses
        eff_doses = np.minimum(vacc_doses, len(self.cumulative) - 1)  # Convert to a valid index
        vacc_eff = self.cumulative[eff_doses]  # Pull out corresponding effect sizes
        rel_trans_eff = (1.0 - vacc_eff) + vacc_eff * self.rel_trans
        rel_symp_eff = (1.0 - vacc_eff) + vacc_eff * self.rel_symp

        # Apply the vaccine to people
        sim.people.rel_trans[vacc_take_inds] = self.orig_rel_trans[vacc_take_inds]*rel_trans_eff
        sim.people.symp_prob[vacc_take_inds] = self.orig_symp_prob[vacc_take_inds]*rel_symp_eff

        self.vaccinations[all_vacc_inds] += 1
        for v_ind in all_vacc_inds:
            self.vaccination_dates[v_ind].append(sim.t)

        return

    def shrink(self):
        self.vaccination_dates = None
        self.vaccinations = None
        self.orig_rel_trans = None
        self.orig_symp_prob = None