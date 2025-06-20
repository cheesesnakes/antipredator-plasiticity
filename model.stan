data {
  int<lower=0> N; // number of observations
  int<lower=0> P; // number of protection levels
  int<lower=0> B; // number of behavioral types
  int<lower=0> S; // number of plots
  int<lower=0> C; // number of size classes
  int<lower=0> G; // number of guilds
  int<lower=0> K; // number of species
  int<lower=0> T; // number of treatments
  int<lower=0> Q; // number of deployments
  
  // response variables
  
  array[N, B] real<lower=0> D; // observed durations
  array[N] int<lower=0> bites; // number of bites observed
  
  // index variables
  array[N] int<lower=1, upper=S> plot; // plot index
  array[N] int<lower=1, upper=K> species; // species index
  array[S] int<lower=1, upper=Q> deployment; // deployment index
  
  // plot-level predictors
  array[S] int<lower=1, upper=2> protection; // protection level (0 or 1)
  array[S] int<lower=1, upper=2> predator; // predator presence (0 or 1)
  array[S, 3] real<lower=0, upper=1> rugosity_raw; // rugosity (continuous variable)
  array[S] real<lower=0, upper=1> biomass; // biomass availability (continuous variable)
  array[S] int<lower=0, upper=T> treatment; // treatment index (0 to T)
  
  // individual-level predictors
  array[N] int<lower=1, upper=C> size; // size class of each observation
  array[N] int<lower=1, upper=2> group; // group membership (0 or 1)
  array[K, G] real<lower=0, upper=1> guild; // guild of each observation
}
parameters {
  // Parameters to estimate rugosity
  
  array[S] real<lower=1e-6, upper=(1 - 1e-6)> rugosity; // accounting for multiple rugosity measurements
  array[S] real<lower=1e-6> phi_rug; // standard deviation of rugosity in each plot
  
  // parameters for zero-inflation
  array[S, B] real alpha_pi; // random intercepts for zero-inflation
  array[Q, B] real alpha_dep_pi; // effect of deployment on zero-inflation
  array[P, B] real beta_pi; // effect of protection on zero-inflation
  array[B] real gamma_pi; //effect of rugosity on zero-inflation
  array[B] real zeta_pi; // effect of biomass on zero-inflation
  array[2, B] real eta_pi; // effect of predator presence on zero-inflation
  array[C, B] real omega_pi; // effect of size class on zero-inflation
  array[G, B] real epsilon_pi; // effect of guild on zero-inflation
  array[2, B] real delta_pi; // effect of group on zero-inflation
  array[T, B] real theta_pi; // effect of treatment on zero-inflation
  
  // parameters for duration model
  array[S, B] real alpha_D; // random intercepts for duration
  array[Q, B] real alpha_dep_D; // effect of deployment on duration
  array[P, B] real beta_D; // effect of protection on duration
  array[B] real gamma_D; // effect of rugosity on duration
  array[B] real zeta_D; // effect of biomass on duration
  array[2, B] real eta_D; // effect of predator presence on duration
  array[C, B] real omega_D; // effect of size class on duration
  array[G, B] real epsilon_D; // effect of guild on duration
  array[2, B] real delta_D; // effect of group on duration
  array[B] real<lower=1e-6> sigma_D; // standard deviation of duration
  array[T, B] real theta_D; // effect of treatment on duration
  
  // parameters for bites model
  array[S] real alpha_bites; // random intercepts for risk of bites
  array[Q] real alpha_dep_bites; // effect of deployment on bites
  array[P] real beta_bites; // effect of protection on bites
  real gamma_bites; // effect of rugosity on bites
  real zeta_bites; // effect of biomass on bites
  array[2] real eta_bites; // effect of predator presence on bites
  array[C] real omega_bites; // effect of size class on bites
  array[G] real epsilon_bites; // effect of guild on bites
  array[2] real delta_bites; // effect of group on bites
  array[T] real theta_bites; // effect of treatment on bites
}
transformed parameters {
  // standardize rugosity and biomass
  array[S] real rugosity_std; // standardized rugosity
  array[S] real biomass_std; // standardized biomass
  
  array[N] real lambda; // expected number of bites
  array[N, B] real mu; // expected duration
  array[N, B] real pi; // probability of non-zero duration
  
  for (s in 1 : S) {
    rugosity_std[s] = (rugosity[s] - mean(rugosity)) / sd(rugosity);
    biomass_std[s] = (biomass[s] - mean(biomass)) / sd(biomass);
  }
  
  for (n in 1 : N) {
    int t = treatment[plot[n]]; // treatment for the current plot
    int p = protection[plot[n]]; // protection level for the current plot
    int s = plot[n]; // plot index for the current observation
    int d = deployment[plot[n]]; // deployment index for the current observation
    int k = species[n]; // species index for the current observation
    int c = size[n]; // size class for the current observation
    int g = group[n]; // group for the current observation
    int pred = predator[plot[n]]; // predator presence for the current plot
    
    for (b in 1 : B) {
      // calculate expected duration
      mu[n, b] = alpha_D[s, b] + alpha_dep_D[d, b] + theta_D[t, b]
                 + beta_D[p, b] + gamma_D[b] * rugosity_std[s]
                 + zeta_D[b] * biomass_std[s] + eta_D[pred, b]
                 + omega_D[c, b] + dot_product(epsilon_D[ : , b], guild[k])
                 + delta_D[g, b];
      
      // calculate probability of non-zero duration
      
      pi[n, b] = inv_logit(alpha_pi[s, b] + alpha_dep_pi[d, b]
                           + theta_pi[t, b] + beta_pi[p, b]
                           + gamma_pi[b] * rugosity_std[s]
                           + zeta_pi[b] * biomass_std[s] + eta_pi[pred, b]
                           + omega_pi[c, b]
                           + dot_product(epsilon_pi[ : , b], guild[k])
                           + delta_pi[g, b]);
    }
    
    // calculate expected number of bites
    
    lambda[n] = exp(alpha_bites[s] + alpha_dep_bites[d] + theta_bites[t]
                    + beta_bites[p] + gamma_bites * rugosity_std[s]
                    + zeta_bites * biomass_std[s] + eta_bites[pred]
                    + omega_bites[c] + dot_product(epsilon_bites, guild[k])
                    + delta_bites[g]);
  }
}
model {
  // Priors
  for (s in 1 : S) {
    rugosity[s] ~ beta(1, 1);
    phi_rug[s] ~ exponential(1);
  }
  
  // Zero-inflation parameters
  for (b in 1 : B) {
    alpha_pi[ : , b] ~ normal(0, 0.5);
    alpha_dep_pi[ : , b] ~ normal(0, 0.5);
    beta_pi[ : , b] ~ normal(0, 0.5);
    gamma_pi[b] ~ normal(0, 0.5);
    zeta_pi[b] ~ normal(0, 0.5);
    eta_pi[ : , b] ~ normal(0, 0.5);
    omega_pi[ : , b] ~ normal(0, 0.5);
    epsilon_pi[ : , b] ~ normal(0, 0.5);
    delta_pi[ : , b] ~ normal(0, 0.5);
    theta_pi[ : , b] ~ normal(0, 0.5); // treatment effects for zero-inflation
  }
  
  // Duration parameters
  
  for (b in 1 : B) {
    alpha_D[ : , b] ~ normal(0, 0.5);
    alpha_dep_D[ : , b] ~ normal(0, 0.5);
    beta_D[ : , b] ~ normal(0, 0.5);
    gamma_D[b] ~ normal(0, 0.5);
    zeta_D[b] ~ normal(0, 0.5);
    eta_D[ : , b] ~ normal(0, 0.5);
    omega_D[ : , b] ~ normal(0, 0.5);
    epsilon_D[ : , b] ~ normal(0, 0.5);
    delta_D[ : , b] ~ normal(0, 0.5);
    sigma_D[b] ~ cauchy(0, 1); // using Cauchy prior for scale
    theta_D[ : , b] ~ normal(0, 0.5); // treatment effects for duration
  }
  
  // Bites parameters
  alpha_bites ~ normal(0, 0.5);
  alpha_dep_bites ~ normal(0, 0.5);
  beta_bites ~ normal(0, 0.5);
  gamma_bites ~ normal(0, 0.5);
  zeta_bites ~ normal(0, 0.5);
  eta_bites ~ normal(0, 0.5);
  omega_bites ~ normal(0, 0.5);
  epsilon_bites ~ normal(0, 0.5);
  delta_bites ~ normal(0, 0.5);
  theta_bites ~ normal(0, 0.5); // treatment effects for bites
  
  // rugosity estimation
  
  for (s in 1 : S) {
    rugosity_raw[s, 1] ~ beta(rugosity[s] * phi_rug[s],
                              (1 - rugosity[s]) * phi_rug[s]);
    rugosity_raw[s, 2] ~ beta(rugosity[s] * phi_rug[s],
                              (1 - rugosity[s]) * phi_rug[s]);
    rugosity_raw[s, 3] ~ beta(rugosity[s] * phi_rug[s],
                              (1 - rugosity[s]) * phi_rug[s]);
  }
  
  // Likelihood
  
  for (n in 1 : N) {
    for (b in 1 : B) {
      if (D[n, b] == 0) {
        target += bernoulli_lpmf(1 | pi[n, b]); // zero-inflation
      } else {
        target += bernoulli_lpmf(0 | pi[n, b]); // non-zero duration
        target += lognormal_lpdf(D[n, b] | mu[n, b], sigma_D[b]); // duration likelihood      
      }
    }
    if (D[n, 1] > 0) {
      target += poisson_log_lpmf(bites[n] | log(lambda[n]) + log(D[n, 1])); // bites likelihood for behavior 1
    } else {
      target += poisson_log_lpmf(bites[n] | 1e-10); // no bites for other behaviors
    }
  }
}
generated quantities {
  // posterior predictive checks
  array[N, B] real D_pred; // predicted durations
  array[N] real bites_pred; // predicted bites
  
  for (n in 1 : N) {
    real lambda_pred = exp(lambda[n]);
    for (b in 1 : B) {
      real mu_pred = mu[n, b];
      real pi_pred = pi[n, b];
      if (bernoulli_rng(pi_pred)) {
        D_pred[n, b] = 0;
      } else {
        D_pred[n, b] = lognormal_rng(mu_pred, sigma_D[b]);
      }
    }
    if (D_pred[n, 1] > 0) {
      bites_pred[n] = poisson_rng(lambda_pred * D_pred[n, 1]) / D_pred[n, 1];
    } else {
      // if no duration, set bites to a small value
      bites_pred[n] = 0; // or some other small value
    }
  }
  // counterfactual protection 
  array[P, T, N, B] real D_pred_protection; // predicted durations with protection
  array[P, T, N] real bites_pred_protection; // predicted bites with protection
  
  for (p in 1 : P) {
    for (t in 1 : T) {
      for (n in 1 : N) {
        real rug_std = mean(rugosity_std);
        real bio_std = mean(biomass_std);
        int group_std = 1;
        int predator_std = 1;
        int s = plot[n]; // plot index for the current observation
        int d = deployment[s]; // deployment index for the current plot
        int k = species[n]; // species index for the current observation
        int size_std = size[n]; // size class for the current observation
        int pred = predator[s]; // predator presence for the current plot
        
        for (b in 1 : B) {
          real mu_cf = alpha_D[s, b] + alpha_dep_D[d, b] + theta_D[t, b]
                       + beta_D[p, b] + alpha_pi[s, b] + theta_pi[t, b]
                       + protection[s] * beta_pi[p, b] + gamma_D[b] * rug_std
                       + zeta_D[b] * bio_std + eta_D[predator_std, b]
                       + omega_D[size_std, b]
                       + dot_product(epsilon_D[ : , b], guild[k])
                       + delta_D[group_std, b];
          
          real pi_cf = inv_logit(alpha_pi[s, b] + alpha_dep_pi[d, b]
                                 + theta_pi[t, b] + beta_pi[p, b]
                                 + gamma_pi[b] * rug_std
                                 + zeta_pi[b] * bio_std
                                 + eta_pi[predator_std, b]
                                 + omega_pi[size_std, b]
                                 + dot_product(epsilon_pi[ : , b], guild[k])
                                 + delta_pi[group_std, b]);
          
          if (bernoulli_rng(pi_cf)) {
            D_pred_protection[p, t, n, b] = 0;
          } else {
            D_pred_protection[p, t, n, b] = lognormal_rng(mu_cf, sigma_D[b]);
          }
        }
        
        real lambda_cf = exp(alpha_bites[s] + alpha_dep_bites[d]
                             + theta_bites[t] + beta_bites[p]
                             + gamma_bites * rug_std + zeta_bites * bio_std
                             + eta_bites[predator_std]
                             + omega_bites[size_std]
                             + dot_product(epsilon_bites, guild[k])
                             + delta_bites[group_std]);
        
        bites_pred_protection[p, t, n] = lambda_cf;
      }
    }
  }
}
