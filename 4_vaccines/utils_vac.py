from covasim import Intervention
import sciris as sc
from covasim import parameters as cvpar
from covasim import utils as cvu
from covasim import immunity as cvi
from covasim import defaults  as cvd
from covasim.interventions import process_days, get_subtargets, find_day
import numpy as np

class vaccinate(Intervention):
    '''
    Apply a vaccine to a subset of the population.

    The main purpose of the intervention is to change the relative susceptibility
    and the probability of developing symptoms if still infected. However, this intervention
    also stores several types of data:

        - ``vaccinated``:        whether or not a person is vaccinated
        - ``vaccinations``:      the number of vaccine doses per person
        - ``vaccination_dates``: list of vaccination dates per person

    Args:
        vaccine (dict/str): which vaccine to use; see below for dict parameters
        label        (str): if vaccine is supplied as a dict, the name of the vaccine
        days     (int/arr): the day or array of days to apply the interventions
        prob       (float): probability of being vaccinated (i.e., fraction of the population)
        subtarget  (dict): subtarget intervention to people with particular indices (see test_num() for details)
        kwargs     (dict): passed to Intervention()

    If ``vaccine`` is supplied as a dictionary, it must have the following parameters:

        - ``nab_eff``:   the waning efficacy of neutralizing antibodies at preventing infection
        - ``nab_init``:  the initial antibody level (higher = more protection)
        - ``nab_boost``: how much of a boost being vaccinated on top of a previous dose or natural infection provides
        - ``doses``:     the number of doses required to be fully vaccinated
        - ``interval``:  the interval between doses
        - entries for efficacy against each of the strains (e.g. ``b117``)

    See ``parameters.py`` for additional examples of these parameters.

    **Example**::

        pfizer = cv.vaccinate(vaccine='pfizer', days=30, prob=0.7)
        cv.Sim(interventions=pfizer, use_waning=True).run().plot()
    '''
    def __init__(self, vaccine, days, label=None, prob=1.0, subtarget=None, **kwargs):
        super().__init__(**kwargs) # Initialize the Intervention object
        self.days      = sc.dcp(days)
        self.prob      = prob
        self.subtarget = subtarget
        self.index     = None # Index of the vaccine in the sim; set later
        self.label     = None # Vacine label (used as a dict key)
        self.p         = None # Vaccine parameters
        self.parse(vaccine=vaccine, label=label) # Populate
        return


    def parse(self, vaccine=None, label=None):
        ''' Unpack vaccine information, which may be given as a string or dict '''

        # Option 1: vaccines can be chosen from a list of pre-defined vaccines
        if isinstance(vaccine, str):

            choices, mapping = cvpar.get_vaccine_choices()
            strain_pars = cvpar.get_vaccine_strain_pars()
            dose_pars = cvpar.get_vaccine_dose_pars()

            label = vaccine.lower()
            for txt in ['.', ' ', '&', '-', 'vaccine']:
                label = label.replace(txt, '')

            if label in mapping:
                label = mapping[label]
                vaccine_pars = sc.mergedicts(strain_pars[label], dose_pars[label])
            else: # pragma: no cover
                errormsg = f'The selected vaccine "{vaccine}" is not implemented; choices are:\n{sc.pp(choices, doprint=False)}'
                raise NotImplementedError(errormsg)

            if self.label is None:
                self.label = label

        # Option 2: strains can be specified as a dict of pars
        elif isinstance(vaccine, dict):

            # Parse label
            vaccine_pars = vaccine
            label = vaccine_pars.pop('label', label) # Allow including the label in the parameters
            if label is None:
                label = 'custom'

        else: # pragma: no cover
            errormsg = f'Could not understand {type(vaccine)}, please specify as a string indexing a predefined vaccine or a dict.'
            raise ValueError(errormsg)

        # Set label and parameters
        self.label = label
        self.p = sc.objdict(vaccine_pars)

        return


    def initialize(self, sim):
        ''' Fix the dates and store the vaccinations '''
        super().initialize()

        # Check that the simulation parameters are correct
        if not sim['use_waning']:
            errormsg = 'The cv.vaccinate() intervention requires use_waning=True. Please enable waning, or else use cv.simple_vaccine().'
            raise RuntimeError(errormsg)

        # Populate any missing keys -- must be here, after strains are initialized
        default_strain_pars = cvpar.get_vaccine_strain_pars(default=True)
        default_dose_pars   = cvpar.get_vaccine_dose_pars(default=True)
        strain_labels       = list(sim['strain_pars'].keys())
        dose_keys           = list(default_dose_pars.keys())

        # Handle dose keys
        for key in dose_keys:
            if key not in self.p:
                self.p[key] = default_dose_pars[key]

        # Handle strains
        for key in strain_labels:
            if key not in self.p:
                if key in default_strain_pars:
                    val = default_strain_pars[key]
                else:
                    val = 1.0
                    if sim['verbose']: print('Note: No cross-immunity specified for vaccine {self.label} and strain {key}, setting to 1.0')
                self.p[key] = val


        self.days = process_days(sim, self.days) # days that group becomes eligible
        self.first_dose_nab_days  = [None]*sim.npts # People who get nabs from first dose
        self.second_dose_nab_days = [None]*sim.npts # People who get nabs from second dose (if relevant)
        self.second_dose_days     = [None]*sim.npts # People who get second dose (if relevant)
        self.vaccinated           = [None]*sim.npts # Keep track of inds of people vaccinated on each day
        self.vaccinations         = np.zeros(sim['pop_size'], dtype=cvd.default_int) # Number of doses given per person
        self.vaccination_dates    = np.full(sim['pop_size'], np.nan) # Store the dates when people are vaccinated
        sim['vaccine_pars'][self.label] = self.p # Store the parameters
        self.index = list(sim['vaccine_pars'].keys()).index(self.label) # Find where we are in the list
        sim['vaccine_map'][self.index]  = self.label # Use that to populate the reverse mapping

        return


    def apply(self, sim):
        ''' Perform vaccination '''

        if sim.t >= np.min(self.days):

            # Vaccinate people with their first dose
            vacc_inds = np.array([], dtype=int) # Initialize in case no one gets their first dose
            for ind in find_day(self.days, sim.t, interv=self, sim=sim):
                vacc_probs = np.zeros(sim['pop_size'])
                unvacc_inds = sc.findinds(~sim.people.vaccinated)
                if self.subtarget is not None:
                    subtarget_inds, subtarget_vals = get_subtargets(self.subtarget, sim)
                    if len(subtarget_vals):
                        vacc_probs[subtarget_inds] = subtarget_vals  # People being explicitly subtargeted
                else:
                    vacc_probs[unvacc_inds] = self.prob  # Assign equal vaccination probability to everyone
                vacc_probs[cvu.true(sim.people.dead)] *= 0.0 # Do not vaccinate dead people
                vacc_inds = cvu.true(cvu.binomial_arr(vacc_probs))  # Calculate who actually gets vaccinated

                if len(vacc_inds):
                    self.vaccinated[sim.t] = vacc_inds
                    sim.people.flows['new_vaccinations'] += len(vacc_inds)
                    sim.people.flows['new_vaccinated']   += len(vacc_inds)
                    if self.p.interval is not None:
                        next_dose_day = sim.t + self.p.interval
                        if next_dose_day < sim['n_days']:
                            self.second_dose_days[next_dose_day] = vacc_inds
                        next_nab_day = sim.t + self.p.nab_interval
                        if next_nab_day < sim['n_days']:
                            self.first_dose_nab_days[next_nab_day] = vacc_inds
                    else:
                        self.first_dose_nab_days[sim.t] = vacc_inds

            # Also, if appropriate, vaccinate people with their second dose
            vacc_inds_dose2 = self.second_dose_days[sim.t]
            if vacc_inds_dose2 is not None:
                next_nab_day = sim.t + self.p.nab_interval
                if next_nab_day < sim['n_days']:
                    self.second_dose_nab_days[next_nab_day] = vacc_inds_dose2
                vacc_inds = np.concatenate((vacc_inds, vacc_inds_dose2), axis=None)
                sim.people.flows['new_vaccinations'] += len(vacc_inds_dose2)

            # Update vaccine attributes in sim
            if len(vacc_inds):
                sim.people.vaccinated[vacc_inds] = True
                sim.people.vaccine_source[vacc_inds] = self.index
                self.vaccinations[vacc_inds] += 1
                self.vaccination_dates[vacc_inds] = sim.t

                # Update vaccine attributes in sim
                sim.people.vaccinations[vacc_inds] = self.vaccinations[vacc_inds]

            # check whose nabs kick in today and then init_nabs for them!
            vaccine_nabs_first_dose_inds = self.first_dose_nab_days[sim.t]
            vaccine_nabs_second_dose_inds = self.second_dose_nab_days[sim.t]

            vaccine_nabs_inds = [vaccine_nabs_first_dose_inds, vaccine_nabs_second_dose_inds]

            for vaccinees in vaccine_nabs_inds:
                if vaccinees is not None:
                    sim.people.date_vaccinated[vaccinees] = sim.t
                    cvi.init_nab(sim.people, vaccinees, prior_inf=False)

        return

