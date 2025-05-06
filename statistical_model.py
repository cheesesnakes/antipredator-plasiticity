import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    from cmdstanpy import CmdStanModel

    # from cmdstanpy import install_cmdstan
    from cmdstanpy import CmdStanMCMC

    import pandas as pd
    import numpy as np

    import arviz as az
    import matplotlib.pyplot as plt
    import seaborn as sns

    from scipy.special import logsumexp
    from scipy.stats import gamma

    from tqdm import tqdm
    import os

    # Install CmdStan if not already installed
    # install_cmdstan()

    sns.set_theme(style="white", palette="pastel")
    return (
        CmdStanMCMC,
        CmdStanModel,
        az,
        gamma,
        logsumexp,
        mo,
        np,
        os,
        pd,
        plt,
        sns,
        tqdm,
    )


@app.cell
def _(pd):
    df = pd.read_csv("outputs/generated_data.csv")


    df
    return (df,)


@app.cell
def _(CmdStanModel, df):
    # Prepare Stan data
    stan_data = {
        "N": len(df),
        "T": len(df["treatment"].unique()),
        "D": df["foraging"].values,
        "predator": df["predator"].values,
        "rugosity": df["rugosity"].values,
        "treatment": df["treatment"].values + 1,
        "resource": df["resource"].values,
    }


    # stan model

    model = CmdStanModel(stan_file="model.stan")
    return model, stan_data


@app.cell
def _(az, model, os, stan_data):
    run = True
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

        model_data = az.from_cmdstan(output_dir + "*.csv")
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

        model_data = az.from_cmdstanpy(fit)
    return chains, filename, fit, model_data, model_files, output_dir, run


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_treatment"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_rug"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_predator"], figsize=(16, 6))
    return


@app.cell
def _(mo, model_data):
    posterior = model_data.posterior
    n_chains = posterior.sizes["chain"]
    n_draw = posterior.sizes["draw"]
    n_samples = n_chains * n_draw

    mo.md(f"Total number of samples = {n_samples}")
    return n_chains, n_draw, n_samples, posterior


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
