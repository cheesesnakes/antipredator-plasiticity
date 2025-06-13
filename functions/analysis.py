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


# Effect of treatment on behaviour


def effects_treatment(df_effect, directory="figures/"):
    # Summarise the effect size
    summary_effect = (
        df_effect.groupby(["Treatment", "Behaviour"])["Effect Size"]
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

    # Calculate P(> 0)
    test_effects = (
        df_effect.groupby(["Treatment", "Behaviour"])["Effect Size"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_effect = summary_effect.merge(test_effects, on=["Treatment", "Behaviour"])

    # Reorder and rename columns for readability
    summary_effect.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv

    summary_effect.to_csv("outputs/analysis/summary_effects_treatment.csv", index=False)

    # --- Compare Effects Table ---

    compare_effects = df_effect.pivot_table(
        index=["sample", "Behaviour"],
        columns="Treatment",
        values="Effect Size",
        aggfunc="mean",
    ).reset_index()

    compare_effects = (
        compare_effects.groupby("Behaviour")
        .apply(
            lambda x: pd.Series(
                {
                    "Grouper > Barracuda": np.mean(x["Grouper"] > x["Barracuda"]),
                    "Grouper > Positive Control": np.mean(
                        x["Grouper"] > x["Positive Control"]
                    ),
                    "Barracuda > Positive Control": np.mean(
                        x["Barracuda"] > x["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_effects.to_csv(
        "outputs/analysis/compare_effects_treatment.csv", index=False
    )

    # plot the effect size

    print("\nPlotting effect size...\n")
    plt.figure(figsize=(10, 6))

    # make ridgeplot
    sns.boxplot(
        x="Behaviour",
        y="Effect Size",
        hue="Treatment",
        data=df_effect,
        palette="pastel",
        width=0.5,
        gap=0.1,
        whis=(5, 95),
        showfliers=False,
    )

    plt.axhline(0, color="black", linestyle="--", linewidth=1)
    plt.ylabel("Effect size (log-fold change)")
    plt.xlabel("Behaviour")
    plt.legend(
        title="Treatment", loc="upper center", bbox_to_anchor=(0.5, 1.05), ncol=3
    )
    plt.savefig(f"{directory}/effects_treatment.png", dpi=300)
    plt.close()


# difference in response across protection levels


def response_protection(df_effect, directory="figures/"):
    # Summarise the response
    summary_response = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour"])["Effect Size"]
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

    # Calculate P(> 0)
    test_response = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour"])["Effect Size"]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response = summary_response.merge(
        test_response, on=["Treatment", "Protection", "Behaviour"]
    )

    # Reorder and rename columns for readability
    summary_response.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response.to_csv(
        "outputs/analysis/summary_response_protection.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response = df_effect.pivot_table(
        index=["sample", "Behaviour"],
        columns=["Protection", "Treatment"],
        values="Effect Size",
        aggfunc="mean",
    ).reset_index()

    compare_response = (
        compare_response.groupby("Behaviour")
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response.to_csv(
        "outputs/analysis/compare_response_protection.csv", index=False
    )

    # plot the difference in response across protection levels
    print("\nPlotting difference in response across protection levels...\n")

    plt.figure(figsize=(10, 6))

    # Create the faceted violin plot
    g = sns.catplot(
        x="Treatment",
        y="Effect Size",
        hue="Protection",
        col="Behaviour",
        kind="box",
        data=df_effect,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        sharey=False,
        legend="full",
        whis=(5, 95),
        showfliers=False,
        gap=0.1,
    )

    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)

    # Set titles and labels
    g.set_titles("{col_name}")
    g.set_axis_labels("Treatment", "Log-fold change")

    # Adjust legend
    g._legend.set_title("Protection")

    # legend outside the plot on top
    g._legend.set_bbox_to_anchor((0.5, 1.05))
    g._legend.set_loc("upper center")
    g._legend.set_ncol(2)
    g._legend.set_frame_on(False)
    g._legend.set_title("Protection")

    # Save figure
    g.figure.savefig(
        f"{directory}/response_protection.png", dpi=300, bbox_inches="tight"
    )

    # Close to prevent display in non-interactive environments
    plt.close()


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
    summary_response_size = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour", "size_class"])[
            "Effect Size"
        ]
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
    # Calculate P(> 0)
    test_response_size = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour", "size_class"])[
            "Effect Size"
        ]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response_size = summary_response_size.merge(
        test_response_size,
        on=["Treatment", "Protection", "Behaviour", "size_class"],
    )

    # Reorder and rename columns for readability
    summary_response_size.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response_size.to_csv(
        "outputs/analysis/summary_response_size.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_size = df_effect.pivot_table(
        index=["sample", "Behaviour", "size_class"],
        columns=["Protection", "Treatment"],
        values="Effect Size",
        aggfunc="mean",
    ).reset_index()

    compare_response_size = (
        compare_response_size.groupby(["Behaviour", "size_class"])
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response_size.to_csv(
        "outputs/analysis/compare_response_size.csv", index=False
    )

    # plot the difference in response across size classes
    print("\nPlotting difference in response across size classes...\n")
    plt.figure(figsize=(10, 6))
    # Create the faceted violin plot
    g = sns.catplot(
        x="size_class",
        y="Effect Size",
        hue="Protection",
        col="Behaviour",
        row="Treatment",
        kind="box",
        data=df_effect,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        legend="full",
        showfliers=False,
        whis=(5, 95),
        gap=0.1,
    )
    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
    # Set titles and labels
    g.set_titles("{row_name} | {col_name}")
    g.set_axis_labels("Size Class", "Log-fold change")
    # Adjust legend
    g._legend.set_title("Protection")
    # legend outside the plot on top
    g._legend.set_bbox_to_anchor((0.5, 1.05))
    g._legend.set_loc("upper center")
    g._legend.set_ncol(2)
    g._legend.set_frame_on(False)
    g._legend.set_title("Protection")
    # Save figure
    g.figure.savefig(f"{directory}/response_size.png", dpi=300, bbox_inches="tight")
    # Close to prevent display in non-interactive environments
    plt.close()


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
    summary_response_guild = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour", "guild"])[
            "Effect Size"
        ]
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

    # Calculate P(> 0)
    test_response_guild = (
        df_effect.groupby(["Treatment", "Protection", "Behaviour", "guild"])[
            "Effect Size"
        ]
        .apply(lambda x: np.mean(x > 0))
        .reset_index(name="P(> 0)")
    )

    # Merge summaries
    summary_response_guild = summary_response_guild.merge(
        test_response_guild,
        on=["Treatment", "Protection", "Behaviour", "guild"],
    )

    # Reorder and rename columns for readability
    summary_response_guild.rename(
        columns={"p5": "5th", "p25": "25th", "p75": "75th", "p95": "95th"},
        inplace=True,
    )

    # save as csv
    summary_response_guild.to_csv(
        "outputs/analysis/summary_response_guild.csv", index=False
    )

    # --- Compare Responses Table ---
    compare_response_guild = df_effect.pivot_table(
        index=["sample", "Behaviour", "guild"],
        columns=["Protection", "Treatment"],
        values="Effect Size",
        aggfunc="mean",
    ).reset_index()

    compare_response_guild = (
        compare_response_guild.groupby(["Behaviour", "guild"])
        .apply(
            lambda x: pd.Series(
                {
                    "Outside PA > Inside PA (Grouper)": np.mean(
                        x["Outside PA"]["Grouper"] > x["Inside PA"]["Grouper"]
                    ),
                    "Outside PA > Inside PA (Barracuda)": np.mean(
                        x["Outside PA"]["Barracuda"] > x["Inside PA"]["Barracuda"]
                    ),
                    "Outside PA > Inside PA (Positive Control)": np.mean(
                        x["Outside PA"]["Positive Control"]
                        > x["Inside PA"]["Positive Control"]
                    ),
                }
            )
        )
        .reset_index()
    )

    # save as csv
    compare_response_guild.to_csv(
        "outputs/analysis/compare_response_guild.csv", index=False
    )

    # plot the difference in response across guilds
    print("\nPlotting difference in response across guilds...\n")
    plt.figure(figsize=(10, 6))
    # Create the faceted box plot
    g = sns.catplot(
        x="guild",
        y="Effect Size",
        hue="Protection",
        col="Behaviour",
        row="Treatment",
        kind="box",
        data=df_effect,
        palette="pastel",
        height=4,
        aspect=1.2,
        width=0.5,
        legend="full",
        gap=0.1,
        whis=(5, 95),
        showfliers=False,
    )
    # Add horizontal line at y = 0 to each facet
    for ax in g.axes.flat:
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
    # Set titles and labels
    g.set_titles("{row_name} | {col_name}")
    g.set_axis_labels("Foraging Guild", "Log-fold change")
    # Adjust legend
    g._legend.set_title("Protection")
    # legend outside the plot on top
    g._legend.set_bbox_to_anchor((0.5, 1.05))
    g._legend.set_loc("upper center")
    g._legend.set_ncol(2)
    g._legend.set_frame_on(False)
    g._legend.set_title("Protection")
    # Save figure
    g.figure.savefig(f"{directory}/response_guild.png", dpi=300, bbox_inches="tight")
    # Close to prevent display in non-interactive environments
    plt.close()


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

    return response_df


# Counterfactual analysis function


def counterfactual(model_data, directory="figures/counterfactual/"):
    if not os.path.exists(directory):
        os.makedirs(directory)

    # counterfactual predictions

    print("Creating counterfactual predictions...\n")

    response = clean_effects(model_data)

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
