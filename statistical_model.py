# from cmdstanpy import install_cmdstan
import pandas as pd
import os
from functions.model import load_model, run_model, load_data, prep_stan
from functions.analysis import (
    diagnostics,
    counterfactual,
)
from functions.validate import compare_parameters
from standardise import standardise_data


def main(model="test", run=False, chains=4):
    # load data

    print("Loading data...")

    if model == "data":
        standardise_data()
        print("Standardising data...")

    dirs = load_data(model=model)
    predictors = pd.read_csv(dirs[0])
    response = pd.read_csv(dirs[1])
    rugosity = pd.read_csv(dirs[2])
    traits = pd.read_csv(dirs[3])

    # prepare data
    stan_data = prep_stan(predictors, response, rugosity, traits)

    # run model or load existing model

    output_dir = dirs[4]

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
        diagnostics(model_data, directory=dirs[5])
        if model == "test":
            compare_parameters()

    # counterfactual treatments

    counterfactual(model_data, directory=dirs[5])

    return 0


if __name__ == "__main__":
    main(model="data", run=False, chains=4)
