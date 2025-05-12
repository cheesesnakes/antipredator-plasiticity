import marimo

__generated_with = "0.13.6"
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
    # ArviZ ships with style sheets!
    az.style.use("arviz-whitegrid")

    status = "test"

    if status == "test":
        dirs = [
            "outputs/generated_data_predictors.csv",
            "outputs/generated_data_response.csv",
            "outputs/model/generated/",
            "outputs/generated_data_rugosity.csv",
        ]
    else:
        dirs = ["outputs/predictors.csv", "outputs/response.csv", "outputs/model/data/", "outputs/rugosity_raw.csv"]
    return CmdStanModel, az, dirs, mo, os, pd, plt


@app.cell
def _(dirs, pd):
    predictors = pd.read_csv(dirs[0])

    predictors
    return (predictors,)


@app.cell
def _(dirs, pd):
    response = pd.read_csv(dirs[1])

    response
    return (response,)


@app.cell
def _(dirs, pd):
    rugosity = pd.read_csv(dirs[3])

    rugosity
    return (rugosity,)


@app.cell
def _(predictors, response, rugosity):
    # Prepare Stan data
    stan_data = {
        "N": len(response),
        "T": len(predictors["treatment"].unique()),
        "B": 3,
        "P": predictors["protection"].nunique(),
        "S": predictors["plot_id"].nunique(),
        "D": response[["foraging", "vigilance", "movement"]].values,
        "bites": response["bites"].values,
        "predator": predictors["predator"].values + 1,
        "plot": response["plot_id"].values,
        "rugosity_raw": rugosity[["sample_1", "sample_2", "sample_3"]].values,
        "protection": predictors["protection"].values + 1,
        "treatment": predictors["treatment"].values + 1,
        "biomass": predictors["biomass"].values,
    }
    return (stan_data,)


@app.cell
def _(CmdStanModel):
    # stan model

    model = CmdStanModel(stan_file="model.stan")
    return (model,)


@app.cell
def _(az, dirs, model, os, response, stan_data):
    run = False
    chains = 4

    output_dir = dirs[2]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # check if csv file exists

    model_files = []

    for filename in os.listdir(output_dir):
        if filename.endswith(".csv"):
            model_files.append(filename)

    if not run and len(model_files) == chains:
        print("Loading samples from existing files...")

        obs = az.from_dict(
            observed_data={
                "D_obs": response["vigilance"].values,
                "bites_obs": response["bites"].values,
            }
        )

        model_data = az.from_cmdstan(
            output_dir + "*.csv",
            posterior_predictive=[
                "D_pred",
                "bites_pred",
            ],
        )

        model_data = az.concat(model_data, obs)

    else:
        print("Running model...")

        # delete model_files
        for file in os.listdir(output_dir):
            os.remove(output_dir + file)

        fit = model.sample(
            data=stan_data,
            chains=chains,
            iter_warmup=1000,
            iter_sampling=1000,
            seed=123,
            parallel_chains=4,
            threads_per_chain=8,
            output_dir=output_dir,
            # max_treedepth=15,
            # adapt_delta=0.99,
        )

        obs = az.from_dict(
            observed_data={
                "D_obs": response["vigilance"].values,
                "bites_obs": response["bites"].values,
            }
        )
        model_data = az.from_cmdstanpy(
            fit,
            posterior_predictive=[
                "D_pred",
                "bites_pred",
            ],
        )
        model_data = az.concat(model_data, obs)
    return fit, model_data, run


@app.cell
def _(fit, mo, run):
    if run:
        mo.md(fit.diagnose())  # if divergence is observed
    return


@app.cell
def _(az, model_data):
    az.summary(model_data, hdi_prob=0.95, round_to=2)
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_res"], figsize=(16, 6))
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
    az.plot_trace(model_data, compact=False, var_names=["beta_predator"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data):
    az.plot_trace(model_data, compact=False, var_names=["beta_risk"], figsize=(16, 6))
    return


@app.cell
def _(az, model_data, plt):
    az.plot_ppc(model_data, kind="kde", data_pairs={"D_obs": "D_pred","bites_obs": "bites_pred"}, figsize=(10, 6))
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(mo, model_data):
    posterior = model_data.posterior
    n_chains = posterior.sizes["chain"]
    n_draw = posterior.sizes["draw"]
    n_samples = n_chains * n_draw

    mo.md(f"Total number of samples = {n_samples}")
    return


@app.cell(disabled=True)
def _(az, model_data):
    D_pred_treatment = az.extract(model_data.posterior_predictive, var_names="D_pred_treatment")

    D_pred_treatment = D_pred_treatment.values

    Diff_negative_positive = D_pred_treatment[1,] - D_pred_treatment[0,]

    Diff_negative_positive = Diff_negative_positive.mean(axis=3)

    Diff_negative_1 = D_pred_treatment[2,] - D_pred_treatment[0,]

    Diff_negative_1 = Diff_negative_1.mean(axis=3)

    Diff_negative_2 = D_pred_treatment[3,] - D_pred_treatment[0,]

    Diff_negative_2 = Diff_negative_2.mean(axis=3)
    return Diff_negative_1, Diff_negative_2, Diff_negative_positive


@app.cell(disabled=True)
def _(Diff_negative_1, Diff_negative_2, Diff_negative_positive, az, plt):
    # Combine posteriors

    B = ["Foraging", "Vigilance", "Movement"]

    fig, ax1 = plt.subplots(1, 3, figsize=(18, 6))
    ax1 = ax1.flatten()

    for b in range(3):
        posterior_data = {
            "Positive Control (Outside)": Diff_negative_positive[0, :, b],
            "Treatment 1 (Outside)": Diff_negative_1[0, :, b],
            "Treatment 2 (Outside)": Diff_negative_2[0, :, b],
            "Positive Control (Inside)": Diff_negative_positive[1, :, b],
            "Treatment 1 (Inside)": Diff_negative_1[1, :, b],
            "Treatment 2 (Inside)": Diff_negative_2[1, :, b],
        }

        # Create forest plot
        az.plot_forest(
            posterior_data,
            kind="forestplot",  # Classic forest plot style
            combined=True,  # Treat each array as one group
            hdi_prob=0.87,  # 87% HDI shown by default
            quartiles=True,  # Adds 50% interval inside 87%
            markersize=8,
            linewidth=4,
            colors="black",
            ax=ax1[b],
        )

    plt.tight_layout()
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
