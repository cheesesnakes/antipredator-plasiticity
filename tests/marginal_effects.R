# =============================================================================
# tests/test_marginal_effects.R
#
# Unit test for functions/marginal_effects.R using a STUB predictor instead of a
# fitted brms model. The stub has known true coefficients, so every number that
# me_compute() returns can be checked against a brute-force calculation.
#
# Run from the project root:   Rscript tests/test_marginal_effects.R
# (needs only base R; ggplot2 is optional and only used for the plot smoke test)
# See docs/testing-with-stubs.md for a walk-through.
# =============================================================================

source(file.path("functions", "marginal_effects.R"))

# ---- 1. fake data: same columns as the model data ----------------------------
set.seed(1)
N <- 300
d <- data.frame(
  protection    = factor(sample(c("Unprotected", "Protected"), N, TRUE), levels = c("Unprotected", "Protected")),
  treatment     = factor(sample(c("positive-control", "negative-control", "grouper", "barracuda"), N, TRUE),
                         levels = c("positive-control", "negative-control", "grouper", "barracuda")),
  rugosity_mean = rnorm(N),
  biomass       = rnorm(N),
  group         = rbinom(N, 1, 0.4),
  guild         = sample(c("Herbivore", "Invertivore"), N, TRUE),
  size_class    = sample(c("0-10", "10-20", "20-30"), N, TRUE),
  stringsAsFactors = FALSE
)

# ---- 2. true coefficients (logit scale), incl. an interaction ----------------
truth_b <- list(prot = 0.3, grouper = -0.5, barracuda = 0.2, neg = 0.4, inv = -0.2, grp = 0.3,
                s1 = 0.1, s2 = -0.3, rug = -0.4, bio = 0.15, int_gp = 0.6, intercept = -1)

# deterministic expected value for any data frame (the "oracle")
true_mean <- function(df) {
  b <- truth_b
  plogis(b$intercept + b$prot * (df$protection == "Protected") + b$grouper * (df$treatment == "grouper") +
           b$barracuda * (df$treatment == "barracuda") + b$neg * (df$treatment == "negative-control") +
           b$inv * (df$guild == "Invertivore") + b$grp * (df$group == 1) +
           b$s1 * (df$size_class == "10-20") + b$s2 * (df$size_class == "20-30") +
           b$rug * df$rugosity_mean + b$bio * df$biomass +
           b$int_gp * (df$protection == "Protected" & df$treatment == "grouper"))
}

# ---- 3. the stub: returns a draws x rows matrix like posterior_epred() -------
S <- 500
make_stub <- function(scale = 1) {
  function(model, newdata, draw_ids = NULL, re_formula = NULL) {
    set.seed(99)                                     # same jitter every call => draws stay PAIRED
    B <- lapply(truth_b, function(x) x + rnorm(S, 0, 0.05))   # posterior spread around the truth
    nd <- newdata
    eta <- B$intercept + outer(B$prot, as.numeric(nd$protection == "Protected")) +
      outer(B$grouper, as.numeric(nd$treatment == "grouper")) +
      outer(B$barracuda, as.numeric(nd$treatment == "barracuda")) +
      outer(B$neg, as.numeric(nd$treatment == "negative-control")) +
      outer(B$inv, as.numeric(nd$guild == "Invertivore")) +
      outer(B$grp, as.numeric(nd$group == 1)) +
      outer(B$s1, as.numeric(nd$size_class == "10-20")) + outer(B$s2, as.numeric(nd$size_class == "20-30")) +
      outer(B$rug, nd$rugosity_mean) + outer(B$bio, nd$biomass) +
      outer(B$int_gp, as.numeric(nd$protection == "Protected" & nd$treatment == "grouper"))
    m <- scale * plogis(eta)
    ids <- if (is.null(draw_ids)) seq_len(S) else draw_ids
    m[ids, , drop = FALSE]
  }
}

# ---- 4. helpers --------------------------------------------------------------
failures <- 0
pick <- function(res, term, comparison = NULL, scale = "response", protection = NA, guild = NA, treatment = NA) {
  ok <- res$term == term & res$scale == scale &
    (if (is.null(comparison)) TRUE else res$comparison == comparison) &
    (if (is.na(protection)) is.na(res$protection) else res$protection %in% protection) &
    (if (is.na(guild)) is.na(res$guild) else res$guild %in% guild) &
    (if (is.na(treatment)) is.na(res$treatment) else res$treatment %in% treatment)
  r <- res[ok, ]
  if (nrow(r) != 1) stop("expected exactly 1 row for ", term, " / ", comparison, " but found ", nrow(r))
  r
}
check <- function(label, est, truth, tol = 0.01) {
  ok <- isTRUE(abs(est - truth) < tol)
  if (!ok) failures <<- failures + 1
  cat(sprintf("%-52s estimate = %8.4f   truth = %8.4f   %s\n", label, est, truth, if (ok) "ok" else "FAIL"))
}
setv <- function(df, var, value) {
  if (is.factor(df[[var]])) df[[var]] <- factor(value, levels = levels(df[[var]])) else df[[var]] <- value
  df
}
odds2 <- function(p) log2(p / (1 - p))

# ---- 5. run the function under test -----------------------------------------
res <- me_compute(list(data = d), "Test", "proportion", predict_fun = make_stub(), verbose = FALSE)
cat("rows returned:", nrow(res), "\n\n")

# ---- 6. compare to brute force ----------------------------------------------
# a) overall treatment contrast (average of differences over all rows)
r <- pick(res, "treatment", "grouper - control model")
check("grouper - control, all rows", r$estimate,
      mean(true_mean(setv(d, "treatment", "grouper")) - true_mean(setv(d, "treatment", "positive-control"))))

# b) subgroup defined on OBSERVED protection
r <- pick(res, "treatment", "grouper - control model", protection = "Protected")
dd <- d[d$protection == "Protected", ]
check("grouper - control, Protected rows", r$estimate,
      mean(true_mean(setv(dd, "treatment", "grouper")) - true_mean(setv(dd, "treatment", "positive-control"))))

# c) log2 odds ratio of the AVERAGE predictions in a protection x guild cell
r <- pick(res, "treatment", "barracuda - control model", scale = "log2", protection = "Unprotected", guild = "Herbivore")
dd <- d[d$protection == "Unprotected" & d$guild == "Herbivore", ]
a <- mean(true_mean(setv(dd, "treatment", "barracuda"))); b <- mean(true_mean(setv(dd, "treatment", "positive-control")))
check("barracuda - control, Unprot x Herb (log2 OR)", r$estimate, odds2(a) - odds2(b))

# d) control model vs negative control
r <- pick(res, "treatment", "control model - negative control")
check("control - negative control, all rows", r$estimate,
      mean(true_mean(setv(d, "treatment", "positive-control")) - true_mean(setv(d, "treatment", "negative-control"))))

# e) protection, overall and with treatment set counterfactually
r <- pick(res, "protection", "Protected - Unprotected")
check("Protected - Unprotected, all rows", r$estimate,
      mean(true_mean(setv(d, "protection", "Protected")) - true_mean(setv(d, "protection", "Unprotected"))))
r <- pick(res, "protection", "Protected - Unprotected", treatment = "grouper")
dg <- setv(d, "treatment", "grouper")
check("Protected - Unprotected, grouper set", r$estimate,
      mean(true_mean(setv(dg, "protection", "Protected")) - true_mean(setv(dg, "protection", "Unprotected"))))

# f) other categorical variables
r <- pick(res, "guild", "Invertivore - Herbivore")
check("Invertivore - Herbivore", r$estimate,
      mean(true_mean(setv(d, "guild", "Invertivore")) - true_mean(setv(d, "guild", "Herbivore"))))
r <- pick(res, "group", "in group - solitary")
check("in group - solitary", r$estimate, mean(true_mean(setv(d, "group", 1)) - true_mean(setv(d, "group", 0))))
r <- pick(res, "size_class", "20-30 - 0-10")
check("size 20-30 - 0-10", r$estimate, mean(true_mean(setv(d, "size_class", "20-30")) - true_mean(setv(d, "size_class", "0-10"))))

# g) marginal slopes (central difference with a tiny step as the oracle)
e <- 1e-6
dp <- d; dp$rugosity_mean <- dp$rugosity_mean + e; dm <- d; dm$rugosity_mean <- dm$rugosity_mean - e
r <- pick(res, "rugosity_mean", scale = "slope")
check("slope per SD: rugosity", r$estimate, mean((true_mean(dp) - true_mean(dm)) / (2 * e)))
dd <- d[d$protection == "Protected", ]
dp <- dd; dp$biomass <- dp$biomass + e; dm <- dd; dm$biomass <- dm$biomass - e
r <- pick(res, "biomass", scale = "slope", protection = "Protected")
check("slope per SD: biomass, Protected rows", r$estimate, mean((true_mean(dp) - true_mean(dm)) / (2 * e)))

# ---- 7. structural checks ----------------------------------------------------
stopifnot(!anyNA(res[, c("estimate", "q5", "q25", "q75", "q95", "P_gt0")]))
stopifnot(all(res$q5 <= res$q25 & res$q25 <= res$q75 & res$q75 <= res$q95))
stopifnot(all(res$P_gt0 >= 0 & res$P_gt0 <= 1))
cat("\nstructural checks passed\n")

# draw subsetting must give a valid result (same draws used for every prediction)
res_sub <- me_compute(list(data = d), "Test", "proportion", predict_fun = make_stub(),
                      draw_ids = sort(sample(S, 100)), verbose = FALSE)
stopifnot(nrow(res_sub) == nrow(res))
cat("draw_ids subsetting works\n")

# rate models: units and log2 ratio on the average rate
res_rate <- me_compute(list(data = d), "Rate", "rate", predict_fun = make_stub(scale = 3), verbose = FALSE)
r <- pick(res_rate, "treatment", "barracuda - control model", scale = "log2")
check("rate: log2 ratio barracuda / control (all rows)", r$estimate,
      log2(mean(3 * true_mean(setv(d, "treatment", "barracuda")))) - log2(mean(3 * true_mean(setv(d, "treatment", "positive-control")))))
stopifnot(any(grepl("bites", res_rate$unit)))

# plots are a smoke test only (skipped when ggplot2 is missing)
if (requireNamespace("ggplot2", quietly = TRUE)) {
  out <- file.path(tempdir(), "me_test_figs")
  me_forest_plots(rbind(res, res_rate), out)
  stopifnot(file.exists(file.path(out, "treatment_effects.png")), file.exists(file.path(out, "covariate_effects.png")))
  cat("figures written\n")
}

if (failures > 0) stop(failures, " check(s) failed", call. = FALSE)
cat("\nALL TESTS PASSED\n")