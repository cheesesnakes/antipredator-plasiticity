import arviz as az
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os
import json
from rpy2 import robjects as ro

# set the plot style
sns.set_theme(style="white", palette="pastel")
az.style.use("arviz-whitegrid")

# Bayesian model diagnostics and plotting functions


def diagnostics(model_data, directory="figures/generative/"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # traceplot
    print("Creating traceplot...")
    az.plot_trace(
        model_data,
        compact=False,
        var_names=["theta_pi", "theta_D", "theta_bites", "beta_D"],
        figsize=(16, 24),
    )

    plt.savefig(f"{directory}/traceplot.png", dpi=300)

    # posterior predictive check
    print("Creating posterior predictive check...")
    az.plot_ppc(
        model_data,
        kind="cumulative",
        data_pairs={"D_obs": "D_pred", "bites_obs": "bites_pred"},
        figsize=(10, 6),
    )
    plt.savefig(f"{directory}/ppc.png", dpi=300)


# plotting helper function


def plot_effect_size(
    df,
    directory,
    filename="effects_treatment.png",
    columns=None,
    rows=None,
    hue="Treatment",
    x="Behaviour",
):
    print("\nPlotting...\n")

    # Common plotting kwargs
    plot_kwargs = {
        "palette": "pastel",
        "markers": "s",
        "linestyles": "none",
        "dodge": 0.3,
        "markersize": 10,
        "capsize": 0.05,
        "errorbar": lambda x: (x.quantile(0.11), x.quantile(0.89)),
    }

    if columns is None and rows is None:
        # Single plot using pointplot
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.pointplot(
            x=x,
            y="Effect Size",
            hue=hue,
            data=df,
            ax=ax,
            **plot_kwargs,
        )

        ax.axhline(0, color="black", linestyle="--", linewidth=1)
        ax.set_xlabel("Behaviour", fontsize=14)
        ax.set_ylabel("Log-fold change (89% HDI)", fontsize=14)
        ax.legend(title="Treatment", fontsize=12, title_fontsize=14)

        fig.savefig(f"{directory}/{filename}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    else:
        # Faceted plot using catplot
        g = sns.catplot(
            x=x,
            y="Effect Size",
            hue=hue,
            col=columns,
            row=rows,
            data=df,
            kind="point",
            height=6,
            aspect=1.2,
            **plot_kwargs,
        )

        # Add horizontal lines to each facet
        for ax in g.axes.flatten():
            ax.axhline(0, color="black", linestyle="--", linewidth=1)

        g.set_axis_labels("Behaviour", "Log-fold change (89% HDI)")
        g._legend.set_title("Treatment")

        g.savefig(f"{directory}/{filename}", dpi=300, bbox_inches="tight")

        plt.close()


# summary helper function


def summary_effects(df_effect, vars=["Treatment", "Behaviour"]):
    """
    Summarise the effect size for a given DataFrame.
    If vars is None, summarises all variables.
    """

    summary = (
        df_effect.groupby(vars)["Effect Size"]
        .agg(
            Mean="mean",
            Median="median",
            p5=lambda x: x.quantile(0.05),
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
    )

    test = (
        df_effect.groupby(vars)["Effect Size"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary = summary.merge(test, on=vars)

    # Reorder and rename columns for readability
    summary.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    return summary


# Compare effects helper function
def compare_effects(df_effect, index=[], vars=[]):
    """
    Compare the effects for a given DataFrame.
    If vars is empty, compares across all specified groupings.
    """

    # Pivot the data so each Treatment is a column
    compare = df_effect.pivot_table(
        index=["sample", "Behaviour"] + index,
        columns=["Treatment"],
        values="Effect Size",
        aggfunc="mean",
    ).reset_index()

    compare["Grouper > Barracuda"] = np.mean(compare["Grouper"] > compare["Barracuda"])

    compare["Grouper > Positive Control"] = np.mean(
        compare["Grouper"] > compare["Positive Control"]
    )

    compare["Barracuda > Positive Control"] = np.mean(
        compare["Barracuda"] > compare["Positive Control"]
    )

    return compare


# Effect of treatment on behaviour


def effects_treatment(df_effect, directory="figures/"):
    # Summarise the effect size
    summary_effect = summary_effects(df_effect, vars=["Treatment", "Behaviour"])

    # save as csv

    summary_effect.to_csv("outputs/analysis/summary_effects_treatment.csv", index=False)

    # --- Compare Effects Table ---

    comparison = compare_effects(df_effect, vars=[])

    # save as csv
    comparison.to_csv("outputs/analysis/compare_effects_treatment.csv", index=False)

    # plot the effect size

    plot_effect_size(df_effect, directory)


# difference in response across protection levels


def response_protection(df_effect, directory="figures/"):
    # Summarise the response
    summary_response = summary_effects(
        df_effect, vars=["Treatment", "Protection", "Behaviour"]
    )

    # save as csv
    summary_response.to_csv(
        "outputs/analysis/summary_response_protection.csv", index=False
    )

    # --- Compare Responses Table ---

    compare_response = compare_effects(df_effect, index=["Protection"])

    # save as csv
    compare_response.to_csv(
        "outputs/analysis/compare_response_protection.csv", index=False
    )

    # plot the difference in response across protection levels

    plot_effect_size(
        df_effect,
        directory,
        filename="response_protection.png",
        columns="Treatment",
        hue="Protection",
    )


# response to treatments across size classes
def response_size(df_effect, directory="figures/"):
    # load individual traits

    individual_traits = pd.read_csv("outputs/data/individual_traits.csv", index_col=0)
    if "ind_id" not in individual_traits.columns:
        individual_traits = individual_traits.reset_index()

    # load order of categories
    order_categories = json.load(open("outputs/data/order_categoricals.json", "r"))

    # code ind_id using the order of categories
    individual_traits["ind_id"] = pd.Categorical(
        individual_traits["ind_id"],
        categories=order_categories["ind_id"],
        ordered=True,
    )
    individual_traits["ind_id"] = individual_traits["ind_id"].cat.codes
    individual_traits.rename(columns={"ind_id": "Individuals"}, inplace=True)

    # Merge with individual traits
    df_effect = df_effect.merge(
        individual_traits[["Individuals", "size_class"]], on="Individuals", how="left"
    )

    # Summarise the response size
    summary_response_size = summary_effects(
        df_effect, vars=["Treatment", "Protection", "Behaviour", "size_class"]
    )

    # save as csv
    summary_response_size.to_csv(
        "outputs/analysis/summary_response_size.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_size = compare_effects(
        df_effect, index=["size_class", "Protection"]
    )

    # save as csv
    compare_response_size.to_csv(
        "outputs/analysis/compare_response_size.csv", index=False
    )

    # plot the difference in response across size classes

    plot_effect_size(
        df_effect,
        directory,
        filename="response_size.png",
        columns="Treatment",
        rows="Behaviour",
        x="size_class",
        hue="Protection",
    )


# response to treatments across guilds


def response_guild(df_effect, directory="figures/"):
    # load individual traits
    individual_traits = pd.read_csv("outputs/data/individual_traits.csv", index_col=0)
    if "ind_id" not in individual_traits.columns:
        individual_traits = individual_traits.reset_index()

    # load order of categories
    order_categories = json.load(open("outputs/data/order_categoricals.json", "r"))

    # code ind_id using the order of categories
    individual_traits["ind_id"] = pd.Categorical(
        individual_traits["ind_id"],
        categories=order_categories["ind_id"],
        ordered=True,
    )
    individual_traits["ind_id"] = individual_traits["ind_id"].cat.codes
    individual_traits.rename(columns={"ind_id": "Individuals"}, inplace=True)

    # Merge with individual traits to get guild info
    df_effect = df_effect.merge(
        individual_traits[["Individuals", "guild"]], on="Individuals", how="left"
    )

    # Summarise the response by guild
    summary_response_guild = summary_effects(
        df_effect, vars=["Treatment", "Protection", "Behaviour", "guild"]
    )

    # save as csv
    summary_response_guild.to_csv(
        "outputs/analysis/summary_response_guild.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_guild = compare_effects(df_effect, index=["guild", "Protection"])

    # save as csv
    compare_response_guild.to_csv(
        "outputs/analysis/compare_response_guild.csv", index=False
    )

    # plot the difference in response across guilds

    plot_effect_size(
        df_effect,
        directory,
        filename="response_guild.png",
        columns="Treatment",
        rows="Behaviour",
        x="guild",
        hue="Protection",
    )


def clean_effects(model_data):
    def extract_df(predictive, var, dims, behaviour=None):
        df = (
            az.extract(predictive, var_names=[var])
            .rename(**{f"{var}_dim_{i}": dim for i, dim in enumerate(dims)})
            .to_dataframe()
        )
        df.drop(columns=["chain", "draw"], inplace=True)
        df.reset_index(inplace=True)
        df["sample"] = (df["draw"] + 1) * (df["chain"] + 1)
        df.drop(columns=["chain", "draw"], inplace=True)
        df.rename(columns={var: "Response"}, inplace=True)
        df["Response"] = np.log(df["Response"] + 1)
        if behaviour is not None:
            df["Behaviour"] = behaviour
        return df

    def map_categories(df):
        df["Protection"] = (
            df["Protection"].astype(str).map({"0": "Outside PA", "1": "Inside PA"})
        )
        df["Treatment"] = (
            df["Treatment"]
            .astype(str)
            .map(
                {
                    "0": "Negative Control",
                    "1": "Positive Control",
                    "2": "Barracuda",
                    "3": "Grouper",
                }
            )
        )
        df["Individuals"] += 1
        if "Behaviour" in df:
            if df["Behaviour"].dtype == "int64":
                df["Behaviour"] = (
                    df["Behaviour"]
                    .astype(str)
                    .map({"0": "Foraging", "1": "Vigilance", "2": "Movement"})
                )
        return df

    D_df = extract_df(
        model_data.posterior_predictive,
        "D_pred_protection",
        ["Protection", "Treatment", "Individuals", "Behaviour"],
    )
    D_df = map_categories(D_df)

    bites_df = extract_df(
        model_data.posterior_predictive,
        "bites_pred_protection",
        ["Protection", "Treatment", "Individuals"],
        behaviour="Bite Rate",
    )
    bites_df = map_categories(bites_df)

    response_df = pd.concat([D_df, bites_df], ignore_index=True)

    del D_df, bites_df

    response_df = response_df.pivot_table(
        index=["sample", "Protection", "Individuals", "Behaviour"],
        columns="Treatment",
        values="Response",
    ).reset_index()

    for col in ["Positive Control", "Barracuda", "Grouper"]:
        response_df[col] -= response_df["Negative Control"]
    response_df.drop(columns=["Negative Control"], inplace=True)

    response_df = response_df.melt(
        id_vars=["sample", "Protection", "Individuals", "Behaviour"],
        value_vars=[
            "Positive Control",
            "Barracuda",
            "Grouper",
        ],
        var_name="Treatment",
        value_name="Effect Size",
    ).reset_index()

    response_df.to_csv("outputs/effects.csv", index=False)

    return response_df


# Counterfactual analysis function


def counterfactual(model_data, directory="figures/counterfactual/"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # counterfactual predictions

    print("Creating counterfactual predictions...\n")

    if not os.path.exists("outputs/effects.csv"):
        response = clean_effects(model_data)
    else:
        response = pd.read_csv("outputs/effects.csv")

    print("Cleaned response data shape:", response.shape)
    print("Response data columns:", response.columns.tolist())

    # plot the counterfactual predictions
    print("\nCalculating effects of treatment on behaviour...\n")

    effects_treatment(response, directory=directory)

    # plot the difference in response across protection levels
    print("\nCalculating difference in response across protection levels...\n")
    response_protection(response, directory=directory)

    # plot the difference in response across size classes
    print("\nCalculating difference in response across size classes...\n")
    response_size(response, directory=directory)

    # plot the difference in response across guilds
    print("\nCalculating difference in response across guilds...\n")
    response_guild(response, directory=directory)

    # save tables

    print("\nSaving summary tables...\n")

    ro.r(
        """
       source("functions/analysis_tables.R")
       """
    )

    print("\nDone.\n")

    return 0
