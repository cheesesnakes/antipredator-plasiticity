import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import bernoulli as bern
    from scipy.stats import dirichlet
    from scipy.stats import beta
    from scipy.special import softmax
    from random import choices
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    sns.set_theme(style="white", palette="pastel")
    return bern, beta, choices, dirichlet, mo, np, pd, plt, sns, softmax


@app.cell
def _(bern, beta, np, pd):
    # experiment definition

    n_protection = 2
    n_treatment = 4
    n_ind = 20
    n_rep = 5

    # treatment and protection levels

    plot_id = list(range(1, (n_protection * n_treatment * n_rep) + 1))
    protection = [p for i in range((n_treatment * n_rep)) for p in range(n_protection)]
    treatment = [t for t in range(n_treatment) for i in range(n_rep) for p in range(n_protection)]
    replicate = [r for r in range(n_rep) for i in range(n_treatment * n_protection)]

    # covariates


    def predator(protection):
        """
        Simulate a predator covariate.
        """
        if protection == 0:
            return bern.rvs(0.3, size=1)
        else:
            return bern.rvs(0.75, size=1)


    def rugosity(protection):
        """
        Simulate a rugosity covariate.
        """

        D_max = 190

        if protection == 0:
            # less rugose

            a = np.random.normal(150, 10, size=1)
        else:
            # more rugose
            a = np.random.normal(100, 20, size=1)

        b = D_max - a

        return beta.rvs(a, b, size=1)


    def resource(protection):
        """
        Simulate a resource covariate.
        """

        points = 100

        if protection == 0:
            # more resource
            a = np.random.normal(20, 2, size=1)
        else:
            # less resource
            a = np.random.normal(10, 2, size=1)

        b = points - a

        return beta.rvs(a, b, size=1)


    def unobserved(predator):
        """
        Simulate an unobserved covariate affecting energy through predator presence.
        """

        if predator == 0:
            return np.random.normal(0, 1, size=1)
        else:
            return np.random.normal(1, 1, size=1)


    predator = [predator(p) for p in protection]
    predator = np.array(predator).flatten()
    rugosity = [rugosity(p) for p in protection]
    rugosity = np.array(rugosity).flatten()
    resource = [resource(p) for p in protection]
    resource = np.array(resource).flatten()
    unobs_pred = [unobserved(predator[i]) for i in range(len(predator))]
    unobs_pred = np.array(unobs_pred).flatten()

    # predictor dataframe

    predictor_df = pd.DataFrame(
        {
            "plot_id": plot_id,
            "protection": protection,
            "treatment": treatment,
            "replicate": replicate,
            "predator": predator,
            "rugosity": rugosity,
            "resource": resource,
            "unobs_pred": unobs_pred,
        }
    )

    predictor_df
    return (
        n_ind,
        n_protection,
        n_rep,
        n_treatment,
        plot_id,
        predator,
        predictor_df,
        protection,
        replicate,
        resource,
        rugosity,
        treatment,
        unobs_pred,
        unobserved,
    )


@app.cell
def _(plt, predictor_df, sns):
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=predictor_df, x="predator", hue="protection", kde=True)
    plt.title("Predator Presence")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.histplot(data=predictor_df, x="rugosity", hue="protection", kde=True)
    plt.title("Rugosity")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.histplot(data=predictor_df, x="resource", hue="protection", kde=True)
    plt.title("Resource Availability")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(n_ind, np, pd, plot_id, predictor_df):
    # unobserved variables


    def energy(resource, unobserved):
        """
        Simulate an energy covariate.
        """

        beta = 10

        beta_unobserved = -1

        alpha = 2

        eta = beta * resource + beta_unobserved * unobserved

        mu = np.exp(eta)

        sigma = np.random.exponential(1)

        shape = (mu / sigma) ** 2
        scale = sigma**2 / mu

        return np.random.gamma(shape, scale, size=1)


    def risk(rugosity, predator, treatment):
        """
        Simulate a risk covariate.
        """

        beta_rugosity = -0.5

        beta_predator = 2

        beta_treatment = [0, 0, 1, 2]

        eta = (beta_rugosity * rugosity) + (beta_predator * predator) + beta_treatment[treatment - 1]

        mu = np.exp(eta)

        sigma = np.random.exponential(1)

        shape = (mu / sigma) ** 2
        scale = sigma**2 / mu

        return np.random.gamma(shape, scale, size=1)


    indiviudals = list(range(1, (len(plot_id) * n_ind) + 1))
    plot_ind = [plot for i in range(n_ind) for plot in plot_id]

    energy = [
        energy(
            predictor_df.loc[predictor_df["plot_id"] == i, "resource"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "unobs_pred"].iloc[0],
        )
        for i in plot_ind
    ]
    energy = np.array(energy).flatten()

    risk = [
        risk(
            predictor_df.loc[predictor_df["plot_id"] == i, "rugosity"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "predator"].iloc[0],
            predictor_df.loc[predictor_df["plot_id"] == i, "treatment"].iloc[0],
        )
        for i in plot_ind
    ]
    risk = np.array(risk).flatten()

    # unobserved variables dataframe
    unobserved_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "energy": energy,
            "risk": risk,
        }
    )

    unobserved_df = unobserved_df.merge(predictor_df, on="plot_id")
    unobserved_df
    return energy, indiviudals, plot_ind, risk, unobserved_df


@app.cell
def _(plt, sns, unobserved_df):
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    sns.histplot(data=unobserved_df, x="energy", hue="protection", kde=True)
    plt.title("Energy")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 2, 2)
    sns.histplot(data=unobserved_df, x="risk", hue="protection", kde=True)
    plt.title("Risk")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(indiviudals, np, pd, plot_ind, predictor_df, unobserved_df):
    # response variable


    def foraging(energy, risk):
        """
        Simulate a behavioural response.
        """

        beta_energy = -0.2

        beta_risk = -0.2

        alpha = 2

        eta = alpha + beta_energy * energy + beta_risk * risk

        mu = np.exp(eta)

        sigma = np.random.exponential(1)

        shape = (mu / sigma) ** 2
        scale = sigma**2 / mu

        return np.random.gamma(shape, scale, size=1)


    def vigilance(energy, risk):
        """
        Simulate a behavioural response.
        """

        beta_energy = 0.01

        beta_risk = 0.1

        alpha = 1

        eta = alpha + beta_energy * energy + beta_risk * risk

        mu = np.exp(eta)

        sigma = np.random.exponential(1)

        if mu < 0:
            mu = 0

        shape = (mu / sigma) ** 2
        scale = sigma**2 / mu

        return np.random.gamma(shape, scale, size=1)


    def movement(energy, risk):
        """
        Simulate a behavioural response.
        """

        beta_energy = 0.091

        beta_risk = -1

        alpha = 1

        eta = alpha + beta_energy * energy + beta_risk * risk

        mu = np.exp(eta)

        sigma = np.random.exponential(1)

        shape = (mu / sigma) ** 2
        scale = sigma**2 / mu

        return np.random.gamma(shape, scale, size=1)


    foraging = [foraging(row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    foraging = np.array(foraging).flatten()
    vigilance = [vigilance(row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    vigilance = np.array(vigilance).flatten()
    movement = [movement(row["energy"], row["risk"]) for _, row in unobserved_df.iterrows()]
    movement = np.array(movement).flatten()

    # response dataframe
    response_df = pd.DataFrame(
        {
            "ind_id": indiviudals,
            "plot_id": plot_ind,
            "foraging": foraging,
            "vigilance": vigilance,
            "movement": movement,
        }
    )

    response_df = response_df.merge(predictor_df, on="plot_id")

    response_df
    return foraging, movement, response_df, vigilance


@app.cell
def _(plt, response_df, sns):
    plt.figure(figsize=(18, 6))
    plt.subplot(1, 3, 1)
    sns.histplot(data=response_df, x="foraging", hue="protection", kde=True)
    plt.title("Foraging")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 2)
    sns.histplot(data=response_df, x="vigilance", hue="protection", kde=True)
    plt.title("Vigilance")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.subplot(1, 3, 3)
    sns.histplot(data=response_df, x="movement", hue="protection", kde=True)
    plt.title("Movement")
    plt.legend(title="Protection", labels=["Outside", "Inside"])
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _(response_df):
    response_df.to_csv("outputs/generated_data.csv", index=False)
    return


if __name__ == "__main__":
    app.run()
