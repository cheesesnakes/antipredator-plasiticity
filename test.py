# testing statistical model based on generated data

import arviz as az
import pandas as pd
from params import params
import numpy as np

output_dir = "outputs/model/generated/"

# Load model data from CmdStan CSV outputs
model_data = az.from_cmdstan(output_dir + "*.csv", posterior_predictive="D_pred")

# Define mapping of parameter names
test_params = {
    "beta_risk": "beta_risk",
    "beta_energy_resource": "beta_res",
    "beta_risk_predator": "beta_predator",
    "beta_risk_treatment": "beta_treatment",
    "alpha": "alpha_D",
}

# Get true parameter values from 'params'
target = {p: params[p] for p in test_params.keys()}

for param in target:
    val = target[param]
    if isinstance(val, list):
        target[param] = val[0]

# Extract posterior samples
post = model_data.posterior

# Initialize a list to store summary results
summary = []

for true_param, stan_param in test_params.items():
    samples = post[stan_param].values.flatten()
    mean_val = samples.mean()
    lower_50 = np.percentile(samples, 25)
    upper_50 = np.percentile(samples, 75)
    true_val = target[true_param]

    # Check if true value is within 95% CI
    pass_fail = "Pass" if lower_50 <= true_val <= upper_50 else "Fail"

    summary.append(
        {
            "Parameter": true_param,
            "True Value": true_val,
            "Mean": mean_val,
            "Lower 95%": lower_50,
            "Upper 95%": upper_50,
            "Pass/Fail": pass_fail,
        }
    )


# Convert summary to DataFrame for easy viewing
summary_df = pd.DataFrame(summary)

# Print the table
print(summary_df)
