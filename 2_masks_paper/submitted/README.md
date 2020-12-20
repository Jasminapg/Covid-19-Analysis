# Masks paper code

This folder contains the code and files required to reproduce the results of the submitted masks in schools paper.

## Installation

1. **Important!** Create and activate a virtual environment:
    ```sh
    conda create -n ukmasks python=3.7
    conda activate ukmasks
    ```
    If you do not do this step, attempts to proceed further may corrupt not only this package, but all Python projects on your computer.

2. You can try automatically installing old versions of the packages:
    ```sh
    pip install -r requirements.txt
    ```
    If that doesn't work, delete your virtual environment (`conda activate base; conda env remove -n ukmasks`), redo step 1, and then proceed with steps 3 and 4.

3. Install the old versions of the required dependencies:
    ```sh
    pip install numba==0.48
    pip install xlrd==1.2.0
    pip install sciris==0.17.4
    ```

4. In a separate folder, clone Covasim and install the old version:
    ```sh
    git clone https://github.com/institutefordiseasemodeling/covasim
    cd covasim
    git checkout v1.5.2
    python setup.py develop
    ```

## Usage

To generate the calibration resuls, run

```sh
python UK_Masks_TTI_24August.py
```

To generate different scenarios, change the `scenario` and `tti_scen` options on lines 25-26.