# from cmdstanpy import install_cmdstan
import arviz as az
from functions.model import load_model
import pandas as pd
import json
import matplotlib.pyplot as plt
import numpy as np
from rpy2 import robjects as ro


def parameter_summary():
    order_categories = json.load(open("outputs/data/order_categoricals.json", "r"))
    response = pd.read_csv("outputs/data/response.csv")
    model_data = load_model(response, "outputs/model/data/")

    vars = list(model_data.posterior.data_vars)
    vars = [
        v
        for v in vars
        if v
        not in [
            "rugosity",
            "phi_rug",
            "lambda",
            "mu",
            "pi",
            "rugosity_std",
            "biomass_std",
        ]
    ]
    vars = list(set([v.split("_")[0] for v in vars]))
    print("Model variables: ", vars, "\n")

    models = {"ZI": "pi", "Duration": "D", "Bites": "bites"}

    params_dim0 = {
        "alpha": order_categories["plot_id"],
        "beta": order_categories["protection"],
        "gamma": None,
        "zeta": None,
        "eta": ["Absent", "Present"],
        "omega": order_categories["size_class"],
        "epsilon": ["Herbivore", "Invertivore", "Piscivore", "Unknown"],
        "delta": ["Grouping", "Solitary"],
        "theta": order_categories["treatment"],
        "sigma": None,
    }

    # Loop through models and variables to assign named coordinates to each posterior variable
    for model in models.keys():
        for var in vars:
            if var not in params_dim0:
                continue  # Skip if no dim0 info

            # Construct variable name based on model type (e.g., "theta_ZI")
            variable = f"{var}_{models[model]}"

            # Ensure the variable exists in the posterior
            if variable not in model_data.posterior:
                continue

            # Prepare dimension coordinate dictionary
            dim_prefix = f"{variable}_dim_"
            dims = {}
            if params_dim0[var] is None:
                # Add second dimension for specific models
                if model in ["ZI", "Duration"]:
                    dims[f"{dim_prefix}0"] = ["Foraging", "Vigilance", "Movement"]
            else:
                dims = {f"{dim_prefix}0": params_dim0[var]}
                # Add second dimension for specific models
                if model in ["ZI", "Duration"]:
                    dims[f"{dim_prefix}1"] = ["Foraging", "Vigilance", "Movement"]

            # Assign named coordinates to the posterior variable
            model_data = model_data.assign_coords(dims)

    vars = [v for v in vars if v != "alpha"]
    # Print summary of the model parameters

    print("\nParameter summary:")
    print("========================================")

    params = az.summary(
        model_data,
        var_names=vars,
        kind="all",
        filter_vars="like",
        round_to=3,
        hdi_prob=0.89,
    )

    params = params.reset_index()
    params = params.rename(columns={"index": "variable"})

    params["parameter"] = params["variable"].str.split("_").str[0]

    params["model"] = params["variable"].str.split("_").str[1]
    params["model"] = params["model"].str.split("[").str[0]
    params["model"] = params["model"].replace("pi", "Zero-Inflation")
    params["model"] = params["model"].replace("D", "Duration")
    params["model"] = params["model"].replace("bites", "Bite Rate")

    params["variable"] = params["variable"].str.split("[").str[1]
    params["behaviour"] = params["variable"].str.split(",").str[1]
    params["behaviour"] = params["behaviour"].str.replace("]", "")
    params.loc[params["behaviour"].isna(), "behaviour"] = "Bite Rate"

    params["variable"] = params["variable"].str.split(",").str[0]
    params["variable"] = params["variable"].str.replace("]", "")

    params.columns = params.columns.str.replace(" ", "_")
    params.columns = params.columns.str.title()

    params = params.rename(
        columns={
            "Sd": "Standard Deviation",
            "Hdi_5.5%": "Lower 89% HDI",
            "Hdi_94.5%": "Upper 89% HDI",
            "Mcse_Mean": "MCSE Mean",
            "Mcse_Sd": "MCSE SD",
            "Ess_Bulk": "ESS Bulk",
            "Ess_Tail": "ESS Tail",
            "R_Hat": "R-Hat",
        }
    )
    params = params[
        [
            "Parameter",
            "Behaviour",
            "Model",
            "Variable",
            "Mean",
            "Standard Deviation",
            "Lower 89% HDI",
            "Upper 89% HDI",
            "MCSE Mean",
            "MCSE SD",
            "ESS Bulk",
            "ESS Tail",
            "R-Hat",
        ]
    ]

    print(params)
    params.to_csv("outputs/parameter_summary.csv", index=False)

    # Prints summary for intercept parameters
    print("\nIntercepts summary:")
    print("========================================")
    intercepts = az.summary(
        model_data,
        var_names=["alpha"],
        kind="all",
        filter_vars="like",
        round_to=3,
        hdi_prob=0.89,
    )

    intercepts = intercepts.reset_index()
    intercepts = intercepts.rename(columns={"index": "variable"})

    intercepts["model"] = intercepts["variable"].str.split("_").str[1]
    intercepts["model"] = intercepts["model"].str.split("[").str[0]
    intercepts["model"] = intercepts["model"].replace("pi", "Zero-Inflation")
    intercepts["model"] = intercepts["model"].replace("D", "Duration")
    intercepts["model"] = intercepts["model"].replace("bites", "Bite Rate")

    intercepts["variable"] = intercepts["variable"].str.split("[").str[1]
    intercepts["variable"] = intercepts["variable"].str.replace("]", "")

    intercepts["Behaviour"] = intercepts["variable"].str.split(",").str[1]
    intercepts.loc[intercepts["Behaviour"].isna(), "Behaviour"] = "Bite Rate"

    intercepts["variable"] = intercepts["variable"].str.split(",").str[0]

    intercepts.columns = intercepts.columns.str.replace(" ", "_")
    intercepts.columns = intercepts.columns.str.title()
    intercepts = intercepts.rename(
        columns={
            "Sd": "Standard Deviation",
            "Hdi_5.5%": "Lower 89% HDI",
            "Hdi_94.5%": "Upper 89% HDI",
            "Mcse_Mean": "MCSE Mean",
            "Mcse_Sd": "MCSE SD",
            "Ess_Bulk": "ESS Bulk",
            "Ess_Tail": "ESS Tail",
            "R_Hat": "R-Hat",
        }
    )
    intercepts.rename(columns={"Variable": "Plot ID"}, inplace=True)

    intercepts = intercepts[
        [
            "Plot ID",
            "Behaviour",
            "Model",
            "Mean",
            "Standard Deviation",
            "Lower 89% HDI",
            "Upper 89% HDI",
            "MCSE Mean",
            "MCSE SD",
            "ESS Bulk",
            "ESS Tail",
            "R-Hat",
        ]
    ]

    print(intercepts)
    intercepts.to_csv("outputs/intercept_summary.csv", index=False)

    # forest plots
    axes = az.plot_forest(
        model_data,
        var_names=vars,
        filter_vars="like",
        kind="forestplot",
        figsize=(6, 48),
        combined=True,
        textsize=12,
    )

    # Add vertical line at x=0 for each axis
    for ax in np.ravel(axes):
        ax.axvline(0, color="black", linestyle="--", linewidth=1)

    plt.savefig("figures/parameters_forestplot.png", dpi=300, bbox_inches="tight")

    axes = az.plot_forest(
        model_data,
        var_names=["alpha"],
        filter_vars="like",
        kind="forestplot",
        figsize=(6, 48),
        combined=True,
        textsize=12,
    )

    for ax in np.ravel(axes):
        ax.axvline(0, color="black", linestyle="--", linewidth=1)

    plt.savefig("figures/intercept_forestplot.png", dpi=300, bbox_inches="tight")

    # save summary tables

    ro.r("source('functions/summary_tables.R')")

    return 0


if __name__ == "__main__":
    parameter_summary()
