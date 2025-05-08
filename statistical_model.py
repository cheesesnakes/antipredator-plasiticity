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
    predictors = pd.read_csv("outputs/generated_data_predictors.csv")


    predictors
    return (predictors,)


@app.cell
def _(pd):
    response = pd.read_csv("outputs/generated_data_response.csv")

    response
    return (response,)


@app.cell
def _(predictors, response):
    # Prepare Stan data
    stan_data = {
        "N": len(response),
        "T": len(predictors["treatment"].unique()),
        "B": 3,
        "P": predictors["protection"].nunique(),
        "S": predictors["plot_id"].nunique(),
        "D": response["foraging"].values,
        "predator": predictors["predator"].values + 1,
        "plot": response["plot_id"].values,
        "rugosity": predictors["rugosity"].values,
        "protection": predictors["protection"].values + 1,
        "treatment": predictors["treatment"].values + 1,
        "resource": predictors["resource"].values,
    }
    return (stan_data,)


@app.cell
def _(CmdStanModel):
    # stan model

    model = CmdStanModel(stan_file="model.stan")
    return (model,)


@app.cell
def _(az, model, os, response, stan_data):
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

        obs = az.from_dict(observed_data={"D_obs": response["foraging"].values})

        model_data = az.from_cmdstan(output_dir + "*.csv", posterior_predictive="D_pred")

        model_data = az.concat(model_data, obs)


    else:
        print("Running model...")

        # delete model_files
        for filename in model_files:
            os.remove(output_dir + filename)

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

        obs = az.from_dict(observed_data={"D_obs": response["foraging"].values})
        model_data = az.from_cmdstanpy(fit, posterior_predictive="D_pred")
        model_data = az.concat(model_data, obs)
    return chains, filename, fit, model_data, model_files, obs, output_dir, run


@app.cell
def _(az, model_data):
    az.summary(model_data, hdi_prob=0.95, round_to=2)
    return


@app.cell
def _():
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_res"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_predator_energy"], figsize=(16, 12))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_treatment"], figsize=(16, 24))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_rug"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_predator"], figsize=(16, 12))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_energy"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_risk"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data, plt):
    ax = az.plot_ppc(model_data, kind="kde", data_pairs={"D_obs": "D_pred"}, figsize=(8, 6))
    ax.set_xscale("log")
    plt.tight_layout()
    plt.show()
    return (ax,)


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
