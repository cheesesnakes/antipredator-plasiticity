data {
  int<lower=0> N; // number of observations
  int<lower=0> T; // number of treatments
  array[N] real<lower=0> D; // observed durations
  
  // Predictor variables
  array[N] int<lower=0, upper=1> predator; // predator presence (0 or 1)
  array[N] real rugosity; // rugosity (continuous variable)
  array[N] int<lower=1, upper=4> treatment; // treatment group (0, 1, 2, or 3)
  array[N] real resource; // resource availability (continuous variable)
}
parameters {
  // Top-level coefficients
  real beta_risk; // effect of risk on duration
  real beta_energy; // effect of energy on duration
  
  real<lower=0, upper=1> pi; // zero-inflation parameter for duration
  
  // Risk model coefficients
  real alpha_risk; // baseline risk
  real beta_predator; // effect of predator presence on risk
  real beta_rug; // effect of rugosity on risk
  array[T] real beta_treatment; // effect of treatment on risk
  real<lower=0> sigma_risk; // standard deviation of risk
  
  // Energy model coefficients
  real alpha_energy; // baseline energy
  real beta_res; // effect of resource availability on energy
  real<lower=0> sigma_energy; // standard deviation of energy
  
  // Observation model
  real<lower=0> sigma_D; // standard deviation of duration
  
  // Latent variables per observation
  vector<lower=0>[N] risk; // latent risk variable
  vector<lower=0>[N] energy; // latent energy variable
}
transformed parameters {
  vector<lower=0>[N] mu_risk; // mean risk
  vector<lower=0>[N] a_risk; // shape parameter for risk
  vector<lower=0>[N] b_risk; // rate parameter for risk
  
  vector<lower=0>[N] mu_energy; // mean energy
  vector<lower=0>[N] a_energy; // shape parameter for energy
  vector<lower=0>[N] b_energy; // rate parameter for energy
  
  vector<lower=0>[N] mu_D; // mean duration
  vector<lower=0>[N] a_D; // shape parameter for duration
  vector<lower=0>[N] b_D; // rate parameter for duration
  
  for (n in 1 : N) {
    // Risk model parameters
    mu_risk[n] = exp(alpha_risk + beta_predator * predator[n]
                     + beta_rug * rugosity[n] + beta_treatment[treatment[n]]);
    a_risk[n] = square(mu_risk[n] / sigma_risk);
    b_risk[n] = mu_risk[n] / square(sigma_risk);
    
    // Energy model parameters
    mu_energy[n] = exp(alpha_energy + beta_res * resource[n]);
    a_energy[n] = square(mu_energy[n] / sigma_energy);
    b_energy[n] = mu_energy[n] / square(sigma_energy);
    
    // Duration model parameters
    mu_D[n] = exp(beta_risk * risk[n] + beta_energy * energy[n]);
    a_D[n] = square(mu_D[n] / sigma_D);
    b_D[n] = mu_D[n] / square(sigma_D);
  }
}
model {
  // Priors
  beta_risk ~ normal(0, 1);
  beta_energy ~ normal(0, 1);
  pi ~ beta(1, 1); // Uniform prior for zero-inflation
  
  alpha_risk ~ normal(0, 1);
  beta_predator ~ normal(0, 1);
  beta_rug ~ normal(0, 1);
  beta_treatment ~ normal(0, 1);
  sigma_risk ~ exponential(1);
  
  alpha_energy ~ normal(0, 1);
  beta_res ~ normal(0, 1);
  sigma_energy ~ exponential(1);
  
  sigma_D ~ exponential(1);
  
  // Risk and energy latent variables
  for (n in 1 : N) {
    risk[n] ~ gamma(a_risk[n], b_risk[n]);
    energy[n] ~ gamma(a_energy[n], b_energy[n]);
  }
  
  // Observation model
  for (n in 1 : N) {
    if (D[n] == 0) {
      target += bernoulli_lpmf(1 | pi); // zero-inflation
    } else {
      target += bernoulli_lpmf(0 | pi); // non-zero inflation
      target += gamma_lpdf(D[n] | a_D[n], b_D[n]); // duration model
    }
  }
}
generated quantities {
  // Optional: you can compute posterior predictions or other derived quantities here
}
