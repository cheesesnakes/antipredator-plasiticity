import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import numpy as np
    from scipy.stats import bernoulli as bern
    from scipy.stats import dirichlet
    from scipy.special import softmax
    from random import choices
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="white", palette="pastel")
    return bern, choices, dirichlet, mo, np, plt, sns, softmax


@app.cell
def _():
    states = [1, 2, 3]  # fear, hunger, rest
    M = [0, 1]  # protection status
    Q = [0, 1, 2, 3]  # treatments: 0: negative control, 1: positive control, 2: baracuda, 3: grouper

    # transition between states logit(p(s_i | s_{i-1}, M)) = p(s_i | s_{i-1}) + beta_m * M

    T_s = [[0.0, 0.5, 0.5], [0.5, 0.0, 0.5], [0.5, 0.5, 0.0]]

    beta_m = 0.5

    # duration in each state

    alpha_s = [2.0, 2.0, 2.0]  # shape: variance
    theta_s = [1.0, 1.0, 1.0]  # scale: mean

    behaviours = [1, 2, 3]  # foraging, vigilance, moving <-- emmission

    # p(b_i | s_i) states x behaviours

    p_b = [[0.1, 0.8, 0.1], [0.8, 0.1, 0.1], [0.3, 0.3, 0.4]]

    # duration in each behaviour

    alpha_b = [2.0, 2.0, 2.0]  # shape: variance
    theta_b = [1.0, 1.0, 1.0]  # scale: mean
    return (
        M,
        Q,
        T_s,
        alpha_b,
        alpha_s,
        behaviours,
        beta_m,
        p_b,
        states,
        theta_b,
        theta_s,
    )


@app.cell
def _(
    M,
    T_s,
    alpha_b,
    alpha_s,
    behaviours,
    beta_m,
    np,
    p_b,
    softmax,
    states,
    theta_b,
    theta_s,
):
    # Simulation

    T = 120.0  # max duration
    dt = 0.1
    i = 2  # number of individuals

    # outputs
    m = [0, 1]
    x_i = [[] for _ in range(i)]
    t_x_i = [[] for _ in range(i)]
    b_i = [[] for _ in range(i)]
    t_b_i = [[] for _ in range(i)]

    for ind in range(i):
        # initial state
        p_x = [0.4, 0.3, 0.3]
        x_t = np.random.choice(states, p=p_x)

        tao = 0.0

        while tao < T:
            x_i[ind].append(x_t)

            # how much time does the individual spend in this state (x_t)
            d_x_t = np.random.gamma(alpha_s[x_t - 1], theta_s[x_t - 1])
            end_s = tao + d_x_t
            t_x_i[ind].append(min(end_s, 120))

            # make emission

            tao_b = tao

            while tao_b < end_s:
                # pick behaviour
                p_b_t = p_b[x_t - 1]

                b_t = np.random.choice(behaviours, p=p_b_t)
                b_i[ind].append(b_t)

                # how much time does the individual spend in this behaviour (b_t)
                d_b_t = np.random.gamma(alpha_b[x_t - 1], theta_b[x_t - 1])
                end = tao_b + d_b_t
                t_b_i[ind].append(min(end, 120))

                # update time
                tao_b = end

            # pick next state

            p_x_t = softmax(np.log(T_s[x_t - 1]) + beta_m * M[ind])

            x_t = np.random.choice(states, p=p_x_t)

            # update time

            tao = end_s
    return (
        T,
        b_i,
        b_t,
        d_b_t,
        d_x_t,
        dt,
        end,
        end_s,
        i,
        ind,
        m,
        p_b_t,
        p_x,
        p_x_t,
        t_b_i,
        t_x_i,
        tao,
        tao_b,
        x_i,
        x_t,
    )


@app.cell
def _(i):
    list(range(i))
    return


@app.cell
def _(i, plt, sns, t_x_i, x_i):
    plt.figure(figsize=(12, 5))  # Create one figure

    for indi in range(i):
        sns.lineplot(x=t_x_i[indi], y=x_i[indi], drawstyle="steps-post", label=f"{indi + 1}", linewidth=2)

    plt.xlim(0, 120)
    plt.xlabel("Time")
    plt.ylabel("State")
    plt.yticks([1, 2, 3], ["Fear", "Hunger", "Rest"])
    plt.legend(title="Individual")
    plt.title("State Trajectories per Individual")
    plt.tight_layout()
    plt.show()
    return (indi,)


@app.cell
def _(b_i, i, plt, sns, t_b_i):
    plt.figure(figsize=(12, 5))  # Create one figure

    for _ in range(i):
        sns.lineplot(x=t_b_i[_], y=b_i[_], drawstyle="steps-post", label=f"{_ + 1}", linewidth=2)

    plt.xlim(0, 120)
    plt.xlabel("Time")
    plt.ylabel("Behaviour")
    plt.yticks([1, 2, 3], ["Foraging", "Vigilance", "Moving"])
    plt.legend(title="Individual")
    plt.title("Behaviour Trajectories per Individual")
    plt.tight_layout()
    plt.show()
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
