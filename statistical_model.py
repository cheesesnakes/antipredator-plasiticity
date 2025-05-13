# from cmdstanpy import install_cmdstan
import pandas as pd
import os

from functions.data import load_data, prep_stan
from functions.model import load_model, run_model
from functions.plot import (
    diagnostic_plots,
    counterfactual_treatments,
    counterfactual_treatments_protection,
)
from functions.validate import compare_parameters

# Install CmdStan if not already installed
# install_cmdstan()


def main(model="test", run=False, chains=4):
    # load data

    print("Loading data...")
    dirs = load_data(model=model)
    predictors = pd.read_csv(dirs[0])
    response = pd.read_csv(dirs[1])
    rugosity = pd.read_csv(dirs[3])

    # prepare data
    stan_data = prep_stan(predictors, response, rugosity)

    # run model or load existing model

    output_dir = dirs[2]

    print("Checking for existing model files...")

    if os.path.exists(output_dir):
        # check if csv file exists

        model_files = []

        for filename in os.listdir(output_dir):
            if filename.endswith(".csv"):
                model_files.append(filename)
    else:
        os.makedirs(output_dir)
        model_files = []

    if not run and len(model_files) == chains:
        model_data = load_model(response, output_dir)
    else:
        model_data = run_model(output_dir, stan_data, response, chains=chains)

    # diagnostic plots

    if run:
        diagnostic_plots(model_data, directory=dirs[4])
        compare_parameters()

    # counterfactual treatments

    counterfactual_treatments(model_data, directory=dirs[4])

    # counterfactual treatments by protection

    counterfactual_treatments_protection(model_data, directory=dirs[4])

    return 0


if __name__ == "__main__":
    main(model="data", run=True, chains=4)
