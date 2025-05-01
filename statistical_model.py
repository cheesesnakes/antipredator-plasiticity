import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    from cmdstanpy import CmdStanModel
    import pandas as pd
    import numpy as np
    from cmdstanpy import install_cmdstan
    from cmdstanpy import CmdStanMCMC
    import arviz as az
    import os
    import matplotlib.pyplot as plt
    # Install CmdStan if not already installed
    install_cmdstan()
    return CmdStanMCMC, CmdStanModel, az, install_cmdstan, mo, np, os, pd, plt


@app.cell
def _(pd):
    df = pd.read_csv("outputs/generated_data.csv")

    # calculate duration

    df.sort_values(by=["ind_id", "start_time"], inplace=True)

    df["duration"] = df.groupby("ind_id")["start_time"].shift(-1) - df["start_time"]

    # fill NaN values with 0

    df.fillna({"duration": 1e-10}, inplace=True)

    df.loc[df["duration"] == 0, "duration"] = 1e-10
    return (df,)


@app.cell
def _(CmdStanModel, df):
    # Prepare Stan data
    stan_data = {
        "N": len(df),
        "M": df["behaviour"].nunique(),
        "K": 3,  # Number of latent states to infer
        "I": df["ind_id"].nunique(),
        "id": df["ind_id"].values + 1,  # Stan is 1-indexed
        "B_t": df["behaviour"].values,
        "D_b": df["duration"].values,
    }

    # stan model

    model = CmdStanModel(stan_file="model.stan")
    return model, stan_data


@app.cell
def _(az, model, os, stan_data):
    run = False
    chains = 4

    output_dir = "outputs/model/generated/"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # check if csv file exists

    model_files = []

    for filename in os.listdir(output_dir):
        if filename.endswith(".csv"):
            model_files.append(filename)


    if not run and len(model_files) == chains:
        print("Loading samples from existing files...")

        fit = az.from_cmdstan(output_dir + "*.csv")
    else:
        print("Running model...")

        fit = model.sample(
            data=stan_data,
            chains=chains,
            iter_warmup=1000,
            iter_sampling=1000,
            seed=123,
            parallel_chains=4,
            threads_per_chain=4,
            output_dir=output_dir,
        )
    return chains, filename, fit, model_files, output_dir, run


@app.cell
def _(az, fit):
    az.plot_trace(fit, compact=False, var_names=["eta"], figsize=(15, 30))
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
