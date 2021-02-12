Modelling the transmisson and spread of Covid-19 in the UK
=======

Background
=============
This repository contains a collection of code and data used to model the transmission and spread of COVID-19 in the UK, using the Covasim model.
The UK Covasim model has been used for numerous analyses to inform policy decisions in the UK:

1. **Determining the optimal strategy for reopening schools, the impact of test and trace interventions, and the risk of occurrence of a second COVID-19 epidemic wave in the UK: a modelling study**. Panovska-Griffiths J, Kerr CC, Stuart RM, Mistry D, Klein DJ, Viner R, Bonnell C (2020-08-03). *Lancet Child and Adolescent Health* S2352-4642(20) 30250-9. doi: https://doi.org/10.1016/S2352-4642(20)30250-9

2. **The potential contribution of face coverings to the control of SARS-CoV-2 transmission in schools and broader society in the UK: a modelling study**. Panovska-Griffiths J, Kerr CC, Waites W, Stuart RM, Mistry D, Foster D, Klein DJ, Viner R, Bonnell C (under review; posted 2020-10-08). *medRxiv* 2020.09.28.20202937; doi: https://doi.org/10.1101/2020.09.28.20202937

3. **Mathematical modelling and data analysis as a tool for policy decision making: application to COVID-19 pandemic**. Panovska-Griffiths J, Kerr CC, Waites W, Stuart RM (2021-02-03). *Handbook of Statistics, Vol 44*; doi https://doi.org/10.1016/bs.host.2020.12.001

4. **Modelling the impact of reopening schools in early 2021 in the presence of the new SARS-CoV-2 variant and with roll-out of vaccination against COVID-19**. Panovska-Griffiths J, Stuart RM, Kerr CC, Rosenfeld K, Mistry D, Waites W, Klein DJ, Bonnell C, Viner R (under review; posted 2021-02-08). *medRxiv*; doi https://doi.org/10.1101/2021.02.07.21251287 


Navigating this repository
=============
* 0_misc: contains miscellaneous scripts that do not belong elsewhere

* 1_schools_paper: contains code and data for the paper **Determining the optimal strategy for reopening schools, the impact of test and trace interventions, and the risk of occurrence of a second COVID-19 epidemic wave in the UK: a modelling study**. Panovska-Griffiths J, Kerr CC, Stuart RM, Mistry D, Klein DJ, Viner R, Bonnell C (2020-08-03). *Lancet Child and Adolescent Health* S2352-4642(20) 30250-9. doi: https://doi.org/10.1016/S2352-4642(20)30250-9

* 2_masks_paper: contains code and data for the paper **The potential contribution of face coverings to the control of SARS-CoV-2 transmission in schools and broader society in the UK: a modelling study**. Panovska-Griffiths J, Kerr CC, Waites W, Stuart RM, Mistry D, Foster D, Klein DJ, Viner R, Bonnell C (under review; posted 2020-10-08). *medRxiv* 2020.09.28.20202937; doi: https://doi.org/10.1101/2020.09.28.20202937

* 3_chapter: contains code and data for the book chapter **Mathematical modelling and data analysis as a tool for policy decision making: application to COVID-19 pandemic**. Panovska-Griffiths J, Kerr CC, Waites W, Stuart RM (2021-02-03). *Handbook of Statistics, Vol 44*; doi https://doi.org/10.1016/bs.host.2020.12.001

* 4_vaccines: preliminary vaccination scenarios

* 5_tradeoffs: preliminary traseoff analyses

* 6_schools2: preliminary schools analyses

* 7_schools3: contains code and data for the paper **Modelling the impact of reopening schools in early 2021 in the presence of the new SARS-CoV-2 variant and with roll-out of vaccination against COVID-19**. Panovska-Griffiths J, Stuart RM, Kerr CC, Rosenfeld K, Mistry D, Waites W, Klein DJ, Bonnell C, Viner R (under review; posted 2021-02-08). *medRxiv*; doi https://doi.org/10.1101/2021.02.07.21251287 


About Covasim
=============

Covasim is a stochastic agent-based simulator for performing COVID-19 analyses. These include projections of indicators such as numbers of infections and peak hospital demand. Covasim can also be used to explore the potential impact of different interventions, including social distancing, school closures, testing, contact tracing, quarantine, and vaccination.

The scientific paper describing Covasim is available at http://paper.covasim.org. The recommended citation is:

    **Covasim: an agent-based model of COVID-19 dynamics and interventions**. Kerr CC, Stuart RM, Mistry D, Abeysuriya RG, Rosenfeld R, Hart G, Núñez RC, Cohen JA, Selvaraj P, Hagedorn B, George L, Jastrzębski M, Izzo A, Fowler G, Palmer A, Delport D, Scott N, Kelly S, Bennette C, Wagner B, Chang S, Oron AP, Wenger E, Panovska-Griffiths J, Famulare M, Klein DJ (under review; posted 2020-05-15). *medRxiv* 2020.05.10.20097469; doi: https://doi.org/10.1101/2020.05.10.20097469.

The Covasim webapp is available at http://app.covasim.org, and the repository for it is available `here <https://github.com/institutefordiseasemodeling/covasim_webapp>`__.

Covasim was developed by the `Institute for Disease Modeling <https://idmod.org/>`__, with additional contributions from the `University of Copenhagen <https://www.math.ku.dk/english>`__, the `Burnet Institute <https://www.burnet.edu.au/>`__, `GitHub <https://github.com/>`__, and `Microsoft <https://www.microsoft.com/en-us/ai/ai-for-health-covid-data>`__.
