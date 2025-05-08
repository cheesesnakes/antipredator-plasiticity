data {
  int<lower=0> N; // number of observations
  int<lower=0> T; // number of treatments
  int<lower=0> P; // number of protection levels
  int<lower=0> S; // number of plots
  array[N] real<lower=0> D; // observed durations
  
  // Predictor variables
  array[S] int<lower=1, upper=2> predator; // predator presence (0 or 1)
  array[N] int<lower=1, upper=S> plot; // plot number
  array[S] real<lower=0, upper=1> rugosity; // rugosity (continuous variable)
  array[S] int<lower=1, upper=2> protection; // protection level (0 or 1)
  array[S] int<lower=1, upper=4> treatment; // treatment group (0, 1, 2, or 3)
  array[S] real<lower=0, upper=1> resource; // resource availability (continuous variable)
}
parameters {
  // Top-level coefficients
  real beta_risk; // effect of risk on duration
  real beta_energy; // effect of energy on duration
  
  real alpha_pi; // baseline zero-inflation
  real beta_pi_risk; // effect of risk on zero-inflation
  real beta_pi_energy; // effect of energy on zero-inflation
  
  // Risk model coefficients
  array[S] real alpha_risk; // baseline risk
  ordered[2] beta_predator; // effect of predator presence on risk
  real beta_rug; // effect of rugosity on risk
  ordered[T] beta_treatment; // effect of treatment on risk
  array[S] real<lower=0> sigma_risk; // standard deviation of risk
  
  // Energy model coefficients
  array[S] real alpha_energy; // baseline energy
  real beta_res; // effect of resource availability on energy
  ordered[2] beta_predator_energy; // effect of predator presence on energy through unobserved variables
  array[S] real<lower=0> sigma_energy; // standard deviation of energy
  
  // Observation model
  real alpha_D; // baseline duration
  real<lower=1e-6, upper=10> sigma_D; // standard deviation of duration, non-zero
  
  // Latent variables non-centred
  array[N] real z_risk; // latent risk variable
  array[N] real z_energy; // latent energy variable
}
transformed parameters {
  array[S] real mu_risk; // mean risk
  array[S] real a_risk; // shape parameter for risk
  array[S] real b_risk; // rate parameter for risk
  
  array[S] real mu_energy; // mean energy
  array[S] real a_energy; // shape parameter for energy
  array[S] real b_energy; // rate parameter for energy
  
  array[N] real mu_D; // mean duration
  
  array[N] real pi; // zero-inflation probability
  
  // Latent variables per observation
  array[N] real risk; // latent risk variable
  array[N] real energy; // latent energy variable
  
  for (s in 1 : S) {
    // Risk model parameters
    mu_risk[s] = alpha_risk[s] + beta_predator[predator[s]]
                 + beta_rug * rugosity[s] + beta_treatment[treatment[s]];
    
    // Energy model parameters
    mu_energy[s] = alpha_energy[s] + beta_res * resource[s]
                   + beta_predator_energy[predator[s]];
  }
  
  for (n in 1 : N) {
    // Latent variables
    risk[n] = mu_risk[plot[n]] + sigma_risk[plot[n]] * z_risk[n];
    energy[n] = mu_energy[plot[n]] + sigma_energy[plot[n]] * z_energy[n];
    
    // Zero-inflation probability
    pi[n] = inv_logit(alpha_pi + beta_pi_risk * risk[n]
                      + beta_pi_energy * energy[n]);
    
    // Duration model parameters
    
    mu_D[n] = alpha_D + beta_risk * risk[n] + beta_energy * energy[n];
  }
}
model {
  // Priors
  beta_risk ~ normal(0, 0.5);
  beta_energy ~ normal(0, 0.5);
  beta_pi_risk ~ normal(0, 0.5);
  beta_pi_energy ~ normal(0, 0.5);
  
  alpha_risk ~ normal(0, 0.5);
  beta_predator ~ normal(0, 0.1);
  beta_rug ~ normal(0, 0.1);
  beta_treatment ~ normal(0, 0.1);
  sigma_risk ~ exponential(1);
  
  beta_predator_energy ~ normal(0, 0.5);
  alpha_energy ~ normal(0, 0.5);
  beta_res ~ normal(0, 0.5);
  sigma_energy ~ exponential(1);
  
  alpha_D ~ normal(0, 0.5);
  sigma_D ~ normal(0, 0.5) T[1e-6, ]; // truncated lognormal scale
  
  z_risk ~ normal(0, 0.5); // latent risk variable
  z_energy ~ normal(0, 0.5); // latent energy variable
  
  // Observation model
  
  for (n in 1 : N) {
    if (D[n] == 0) {
      target += bernoulli_lpmf(1 | pi[n]); // zero-inflation
    } else {
      target += bernoulli_lpmf(0 | pi[n]); // non-zero inflation
      target += lognormal_lpdf(D[n] | mu_D[n], sigma_D); // duration model
    }
  }
}
generated quantities {
  array[N] real D_pred; // predicted durations
  
  // posterior predictive check
  for (n in 1 : N) {
    if (bernoulli_rng(pi[n])) {
      D_pred[n] = 0; // zero-inflation
    } else {
      D_pred[n] = lognormal_rng(mu_D[n], sigma_D);
    }
  }
}
