from cleaning import (
    clean_individuals,
    clean_observations,
    clean_predators,
    clean_sites,
    clean_plots,
    clean_benthic_cover,
    clean_rugosity,
    ind_traits,
    metadata,
    calc_abn,
    calc_abn_size,
    create_predictors,
    clean_samples,
    create_response,
    clean_guilds,
)
import os
import numpy as np
import pandas as pd
import json

# make dummy variables for categorical variables


def check_data(df, name, categoricals, order_categoricals):
    found_issue = False
    for col in df.columns:
        if col in categoricals:
            defined = set(order_categoricals[col])
            observed = set(df[col].dropna().unique())
            unexpected = observed - defined

            if unexpected:
                problem_rows = df[df[col].isin(unexpected)][[col]].copy()
                print(
                    f"\n⚠️ Warning in '{name}' — unexpected values in column '{col}':\n"
                )
                print("Rows with unexpected values:")
                print(problem_rows)
                found_issue = True
                break  # break inner loop
    if found_issue:
        return
    else:
        return print(f"All values in '{name}' are as expected\n")


def set_order(df, categoricals, order_categoricals):
    for col in df.columns:
        if col in categoricals:
            df[col] = pd.Categorical(
                df[col], categories=order_categoricals[col], ordered=True
            )
            df[col] = df[col].cat.codes

            if col == "plot_id":
                df[col] += 1  # > 0

            if (df[col] < 0).any():
                print(f"Column '{col}' contains categories not in order_categoricals.")

    return df


def get_order_categoricals(predictors, individuals, response):
    return {
        "deployment_id": np.sort(predictors["deployment_id"].unique()),
        "treatment": np.array(
            ["negative-control", "positive-control", "barracuda", "grouper"],
            dtype=object,
        ),
        "plot_id": np.sort(predictors["plot_id"].unique()),
        "location": np.sort(predictors["location"].unique()),
        "protection": np.sort(predictors["protection"].unique())[::-1],  # reverse order
        "ind_id": np.sort(individuals["ind_id"].unique()),
        "species": np.sort(response["species"].fillna("Unknown").astype(str).unique()),
        "size_class": np.sort(individuals["size_class"].unique()),
    }


# main function


def standardise_data():
    if not os.path.exists("outputs"):
        os.makedirs("outputs")
    if not os.path.exists("outputs/data"):
        os.makedirs("outputs/data")

    individuals = clean_individuals()
    observations = clean_observations()
    predators = clean_predators()
    sites = clean_sites()
    clean_plots()
    benthic_classes = clean_benthic_cover()
    rug, rugosity = clean_rugosity()
    behaviours = metadata()
    abundance = calc_abn(individuals, predators)
    abundance_size = calc_abn_size(individuals, predators)
    predictors = create_predictors(sites, rug, benthic_classes, abundance)
    samples = clean_samples()
    response = create_response(individuals, observations, behaviours, samples)
    guilds = clean_guilds(response)

    # Export individual traits

    ind_traits(individuals, guilds)

    # Define categorical variables and their order
    categoricals = [
        "deployment_id",
        "treatment",
        "plot_id",
        "location",
        "protection",
        "ind_id",
        "species",
        "size_class",
    ]

    order_categoricals = get_order_categoricals(predictors, individuals, response)

    # Save order_categoricals as JSON
    order_categoricals_serializable = {
        k: v.tolist() if isinstance(v, np.ndarray) else list(v)
        for k, v in order_categoricals.items()
    }
    with open("outputs/data/order_categoricals.json", "w") as f:
        json.dump(order_categoricals_serializable, f, indent=2)

    data = [predictors, abundance, abundance_size, response, rugosity, guilds]

    for name, df in zip(
        ["predictors", "abundance", "abundance_size", "response", "rugosity", "guilds"],
        data,
    ):
        check_data(df, name, categoricals, order_categoricals)
        df = set_order(df, categoricals, order_categoricals)

        # save data
        df.to_csv(f"outputs/data/{name}.csv", index=False)

    print("Data cleaning and standardisation complete\n")

    return 0


if __name__ == "__main__":
    run = standardise_data()

    if run != 0:
        print("Standardisation encountered an issue.")
