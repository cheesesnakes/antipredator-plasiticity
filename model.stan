functions {

    real hmm_log_likelihood(
        int N, // number of observations
        int K, // number of states
        int M, // number of behaviours
        int I, // number of individuals
        array[] int id, // individual IDs
        array[] int B_t, // observed behaviours
        array[] real D_b, // observed behaviour durations
        vector pi_s0, // initial state probabilities
        array[] vector transition_matrix, // transition matrix
        array[] vector eta, // behaviour probabilities
        array[] vector alpha, // mean duration parameters
        array[] vector theta // scale parameters
    ) {
        real log_likelihood = 0;
        array[K] real prev_log_alpha; // log alpha for the previous observation
        array[K] real curr_log_alpha; // log alpha for the current observation

        for (i in 1:I) {
            int start_idx = 1;
            while (start_idx <= N && id[start_idx] != i) {
                start_idx += 1;
            }
            if (start_idx > N) continue;

            // Initialize for the first observation of the individual
            for (k in 1:K) {
                real emission_prob = log(eta[k][B_t[start_idx]]) +
                                     gamma_lpdf(D_b[start_idx] | alpha[k][B_t[start_idx]], theta[k][B_t[start_idx]]);
                prev_log_alpha[k] = log(pi_s0[k]) + emission_prob;
            }

            // Process subsequent observations
            for (n in (start_idx + 1):N) {
                if (id[n] != i) break;

                for (k in 1:K) {
                    real max_log_alpha = negative_infinity();
                    for (j in 1:K) {
                        real transition_prob = log(transition_matrix[j][k]);
                        max_log_alpha = log_sum_exp(max_log_alpha, prev_log_alpha[j] + transition_prob);
                    }
                    real emission_prob = log(eta[k][B_t[n]]) +
                                         gamma_lpdf(D_b[n] | alpha[k][B_t[n]], theta[k][B_t[n]]);
                    curr_log_alpha[k] = max_log_alpha + emission_prob;
                }
                prev_log_alpha = curr_log_alpha;
            }

            // Add the log-sum-exp of the final alpha values to the total log likelihood
            log_likelihood += log_sum_exp(prev_log_alpha);
        }

        return log_likelihood;
    }
}

data {
    int<lower=0> N; // number of observations
    int<lower=1> M; // number of behaviours
    int<lower=1> K; // number of states
    int<lower=1> I; // number of individuals
    array[N] int<lower=1, upper=I> id; // individual IDs
    array[N] int<lower=1, upper=M> B_t; //observed behaviours
    array[N] real<lower=0> D_b; // observed behaviour durations
}

parameters {
    simplex[K] pi_s0; // initial state probabilities
    array[K] simplex[K] transition_matrix; // transition matrix

    array[K] simplex[M] eta; // behaviour probabilities
    array[K] vector<lower=1e-9>[M] alpha; // mean duration parameters (S_t, B_t)
    array[K] vector<lower=0>[M] theta; // scale parameters (S_t, B_t)
}
model {
    
    // Priors
    
    // Initial state probabilities
    pi_s0 ~ dirichlet(rep_vector(1, K));

    for (k in 1:K) {
        // Transition matrix
    
        transition_matrix[k] ~ dirichlet(rep_vector(1, K));
        
        // Behaviour probabilities
        eta[k] ~ dirichlet(rep_vector(1, M));
        
        // Duration parameters

        for (m in 1:M) {
            alpha[k][m] ~ gamma(2, 2);
            theta[k][m] ~ gamma(2, 2);
        }
    
    }

    
    // Likelihood

    target += hmm_log_likelihood(N, K, M, I, id, B_t, D_b, pi_s0, transition_matrix, eta, alpha, theta);
}

generated quantities {
   vector[N] log_likelihoods;

    for (n in 1:N) {
         log_likelihoods[n] = 0;
         for (k in 1:K) {
              real emission_prob = log(eta[k][B_t[n]]) +
                                  gamma_lpdf(D_b[n] | alpha[k][B_t[n]], theta[k][B_t[n]]);
              log_likelihoods[n] += log(pi_s0[k]) + emission_prob;
         }
    }
}