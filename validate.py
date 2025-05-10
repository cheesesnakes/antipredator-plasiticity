import arviz as az
from params import params as true_params
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

output_dir = "outputs/model/generated/"

# Load model data from CmdStan CSV outputs

print("Loading model data from CmdStan CSV outputs...")

model_data = az.from_cmdstan(
    output_dir + "*.csv",
    posterior_predictive=[
        "D_pred",
        "D_pred_treatment",
        "mu_risk_treatment",
        "mu_D_treatment",
    ],
)

posterior = model_data.posterior

print("Model data loaded successfully.")


def compare_parameters():
    """
    Compares the posterior distributions from the Stan model to the true
    parameter values from the generative model.

    Parameters:
    posterior:  The Stan `posterior` object.
    true_params: A dictionary containing the true parameter values.
    """

    # Parameters to compare (adjust to match your Stan model and params.py)
    param_names = [
        "beta_risk",
        "alpha_pi",
        "beta_pi_risk",
        "alpha_risk_protection",
        "beta_res",
        "beta_predator",
        "beta_rug",
        "beta_treatment",
        "sigma_D",
    ]

    # Get the true parameter values from the true_params dictionary.
    true_values = [
        true_params.get("beta_risk")[1],
        true_params.get("alpha_pi")[1],
        true_params.get("beta_pi_risk")[1],
        true_params.get("alpha_risk"),
        true_params.get("beta_risk_resource"),
        true_params.get("beta_risk_predator"),
        true_params.get("beta_risk_rugosity"),
        true_params.get("beta_risk_treatment"),
        true_params.get("sigma")[1],
    ]

    # Dynamically calculate the number of rows and columns
    num_params = len(param_names)
    ncols = 3  # Fixed number of columns
    nrows = (num_params + ncols - 1) // ncols  # Calculate rows needed

    # Create a figure and axes
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 18))
    axes = axes.flatten()  # Flatten the 2D array of axes for easier indexing

    for i, param_name in enumerate(param_names):
        ax = axes[i]  # Get the next axis
        if param_name in posterior:
            print(f"Plotting {param_name}")
            samples = posterior[param_name].values
            if samples.ndim > 2:  # Handle parameters with multiple levels
                for level in range(samples.shape[2]):
                    print(f"  Level {level}")
                    sns.histplot(
                        samples[:, level].flatten(),
                        ax=ax,
                        kde=True,
                        label=f"Level {level + 1}",
                    )
                    ax.axvline(
                        x=true_values[i][level],
                        color="red",
                        linestyle="--",
                        label=f"True Value (Level {level + 1})",
                    )
            else:
                sns.histplot(samples.flatten(), ax=ax, kde=True)
                ax.axvline(
                    x=true_values[i],
                    color="red",
                    linestyle="--",
                    label="True Value",
                )
            ax.set_title(param_name)
            ax.legend()
        else:
            ax.text(0.5, 0.5, f"{param_name} not found", ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])

    # Hide any unused axes
    for j in range(len(param_names), len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    # Save the figure
    fig.savefig("figures/parameter_recovery.png")

    # Print some summary statistics
    print("Parameter Recovery Summary:")
    for i, param_name in enumerate(param_names):
        if param_name in posterior:
            samples = posterior[param_name].values
            if samples.ndim > 2:  # Handle parameters with multiple levels
                for level in range(samples.shape[2]):
                    level_samples = samples[:, level].flatten()
                    posterior_mean = level_samples.mean()
                    posterior_median = np.median(level_samples)
                    posterior_95_ci = np.percentile(level_samples, [2.5, 97.5])
                    bias = posterior_mean - true_values[i][level]
                    print(f"\nParameter: {param_name} (Level {level + 1})")
                    print(f"  True Value: {true_values[i][level]:.4f}")
                    print(f"  Posterior Mean: {posterior_mean:.4f}")
                    print(f"  Posterior Median: {posterior_median:.4f}")
                    print(
                        f"  95% CI: [{posterior_95_ci[0]:.4f}, {posterior_95_ci[1]:.4f}]"
                    )
                    print(f"  Bias: {bias:.4f}")
            else:
                samples = samples.flatten()
                posterior_mean = samples.mean()
                posterior_median = np.median(samples)
                posterior_95_ci = np.percentile(samples, [2.5, 97.5])
                bias = posterior_mean - true_values[i]
                print(f"\nParameter: {param_name}")
                print(f"  True Value: {true_values[i]:.4f}")
                print(f"  Posterior Mean: {posterior_mean:.4f}")
                print(f"  Posterior Median: {posterior_median:.4f}")
                print(f"  95% CI: [{posterior_95_ci[0]:.4f}, {posterior_95_ci[1]:.4f}]")
                print(f"  Bias: {bias:.4f}")
        else:
            print(f"\nParameter: {param_name}")
            print("  Not found in posterior samples.")
    return


if __name__ == "__main__":
    # Call the function to compare parameters
    compare_parameters()
