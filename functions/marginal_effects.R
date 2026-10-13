# =============================================================================
# functions/marginal_effects.R
#
# Average marginal effects (AMEs) from the saved brms / ordbetareg models.
# Same logic as models/*/counterfactuals.R (counterfactual posterior_epred),
# with two differences:
#   1. predictions are averaged over observations WITHIN each posterior draw,
#      so the interval is the posterior of the average effect (the
#      counterfactuals scripts summarise across individuals AND draws, which
#      also folds among-individual variation into the interval);
#   2. continuous covariates get marginal slopes (central finite difference),
#      categorical variables get average counterfactual contrasts.
#
# The numerical core uses base R only. brms is called only inside me_epred(),
# so the core can be tested with a stub predictor (see `predict_fun`).
# =============================================================================

ME_VERSION <- "1.0"

# ---- small helpers ----------------------------------------------------------

me_summarise <- function(x) {
  q <- stats::quantile(x, c(0.05, 0.25, 0.75, 0.95), names = FALSE)
  data.frame(
    estimate = stats::median(x), mean = mean(x),
    q5 = q[1], q25 = q[2], q75 = q[3], q95 = q[4],
    P_gt0 = mean(x > 0)
  )
}

# posterior_epred() on a fixed set of draws. Using the same draw_ids for every
# call keeps counterfactual predictions paired draw-by-draw.
me_epred <- function(model, newdata, draw_ids = NULL, re_formula = NULL) {
  brms::posterior_epred(
    model, newdata = newdata, draw_ids = draw_ids, re_formula = re_formula
  )
}

me_binary_levels <- function(x) {
  if (is.logical(x)) return(c(FALSE, TRUE))
  if (is.factor(x) || is.character(x)) {
    lv <- levels(factor(x))
    if (length(lv) != 2) warning("binary variable has ", length(lv), " levels; using first and last")
    return(c(lv[1], lv[length(lv)]))
  }
  u <- sort(unique(x))
  if (length(u) != 2) warning("binary variable has ", length(u), " values; using min and max")
  c(u[1], u[length(u)])
}

# ---- core -------------------------------------------------------------------

#' Marginal effects for one fitted model.
#'
#' @param model       brmsfit (brm / ordbetareg). model$data must hold the data
#'                    used for fitting (brms stores it).
#' @param behaviour   label for the output table.
#' @param kind        "proportion" (time budgets; ordered beta) or "rate" (bites; Gamma, log link).
#' @param guilds      guilds to average over / report (NULL = all levels).
#' @param draw_ids    integer vector of posterior draws (NULL = all).
#' @param re_formula  passed to posterior_epred. NULL = include the observed
#'                    group-level effects (same as add_epred_draws in your
#'                    counterfactuals scripts); NA = population level only.
#' @param h           step (in SD units) for the finite-difference slopes.
#' @param predict_fun function(model, newdata, draw_ids, re_formula) -> draws x rows matrix.
me_compute <- function(model, behaviour, kind = c("proportion", "rate"),
                       guilds = c("Herbivore", "Invertivore"),
                       draw_ids = NULL, re_formula = NULL, h = 0.01,
                       predict_fun = me_epred, verbose = TRUE) {
  kind <- match.arg(kind)
  d <- model$data
  if (is.null(d)) stop("model$data is NULL; cannot build counterfactual data")

  need <- c("protection", "treatment", "rugosity_mean", "biomass", "group", "guild", "size_class")
  miss <- setdiff(need, names(d))
  if (length(miss)) stop("model$data is missing columns: ", paste(miss, collapse = ", "))

  tr <- c(control = "positive-control", negative_control = "negative-control",
          grouper = "grouper", barracuda = "barracuda")
  pr <- c(unprotected = "Unprotected", protected = "Protected")
  if (!all(tr %in% as.character(d$treatment)))
    stop("treatment levels not found in model data: ", paste(setdiff(tr, as.character(d$treatment)), collapse = ", "))
  if (!all(pr %in% as.character(d$protection)))
    stop("protection levels not found in model data: ", paste(setdiff(pr, as.character(d$protection)), collapse = ", "))

  obs_trt  <- as.character(d$treatment)
  obs_prot <- as.character(d$protection)
  obs_gld  <- as.character(d$guild)
  gl   <- if (is.null(guilds)) levels(factor(d$guild)) else guilds
  keep <- obs_gld %in% gl
  if (!any(keep)) stop("no observations in guilds: ", paste(gl, collapse = ", "))

  say <- function(...) if (verbose) message("  ", ...)
  pred <- function(df) predict_fun(model, df, draw_ids = draw_ids, re_formula = re_formula)

  # set a variable to one value for every row, respecting factor levels
  setv <- function(df, var, value) {
    orig <- d[[var]]
    if (is.factor(orig)) {
      df[[var]] <- factor(rep(as.character(value), nrow(df)), levels = levels(orig))
    } else if (is.character(orig)) {
      df[[var]] <- factor(rep(as.character(value), nrow(df)), levels = sort(unique(orig)))
    } else {
      df[[var]] <- rep(value, nrow(df))
    }
    df
  }

  units <- if (kind == "proportion") {
    c(response = "change in proportion of time", log2 = "log2 odds ratio",
      slope = "change in proportion of time per 1 SD")
  } else {
    c(response = "change in bites per second", log2 = "log2 rate ratio",
      slope = "change in bites per second per 1 SD")
  }

  out <- list()
  add <- function(variable, term, type, comparison, scale, draws, n, ref_mean = NA_real_,
                  protection = NA_character_, guild = NA_character_,
                  treatment = NA_character_, note = NA_character_) {
    out[[length(out) + 1]] <<- data.frame(
      behaviour = behaviour, variable = variable, term = term, type = type,
      comparison = comparison, protection = protection, guild = guild,
      treatment = treatment, scale = scale, unit = unname(units[scale]),
      n_obs = n, ref_mean = ref_mean, me_summarise(draws), note = note,
      stringsAsFactors = FALSE
    )
  }
  # contrast A - B averaged over `mask`, on both scales
  add_contrast <- function(variable, term, comparison, A, B, mask, ...) {
    n <- sum(mask)
    if (n == 0) return(invisible())
    a <- rowMeans(A[, mask, drop = FALSE])
    b <- rowMeans(B[, mask, drop = FALSE])
    lg <- if (kind == "proportion") log2(a / (1 - a)) - log2(b / (1 - b)) else log2(a) - log2(b)
    add(variable, term, "contrast", comparison, "response", a - b, n, stats::median(b), ...)
    add(variable, term, "contrast", comparison, "log2", lg, n, stats::median(b), ...)
  }

  # subgroups (defined on OBSERVED protection / guild, as in counterfactuals.R)
  subs <- list(list(protection = NA_character_, guild = NA_character_, mask = keep))
  for (p in pr) subs[[length(subs) + 1]] <- list(protection = p, guild = NA_character_, mask = keep & obs_prot == p)
  for (g in gl) subs[[length(subs) + 1]] <- list(protection = NA_character_, guild = g, mask = keep & obs_gld == g)
  for (p in pr) for (g in gl)
    subs[[length(subs) + 1]] <- list(protection = p, guild = g, mask = keep & obs_prot == p & obs_gld == g)

  # ---- 1. treatment x protection grid (8 prediction sets) ---------------------
  say(behaviour, ": predicting treatment x protection grid")
  key <- function(t, p) paste(t, p, sep = "|")
  G <- list()
  for (t in tr) for (p in pr) G[[key(t, p)]] <- pred(setv(setv(d, "treatment", t), "protection", p))

  # treatment set counterfactually, protection as observed
  Tobs <- lapply(tr, function(t) {
    M <- G[[key(t, pr[1])]]
    i <- obs_prot == pr[2]
    M[, i] <- G[[key(t, pr[2])]][, i]
    M
  })
  # protection set counterfactually, treatment as observed
  Pobs <- lapply(pr, function(p) {
    M <- G[[key(tr[1], p)]]
    for (t in tr[-1]) { i <- obs_trt == t; M[, i] <- G[[key(t, p)]][, i] }
    M
  })

  # treatment contrasts (vs control model; control model vs negative control)
  cons <- list(c("grouper", "control"), c("barracuda", "control"), c("control", "negative_control"))
  lab  <- c(grouper = "grouper", barracuda = "barracuda", control = "control model",
            negative_control = "negative control")
  for (cc in cons) for (s in subs)
    add_contrast("Predator model treatment", "treatment",
                 paste(lab[cc[1]], "-", lab[cc[2]]), Tobs[[cc[1]]], Tobs[[cc[2]]], s$mask,
                 protection = s$protection, guild = s$guild)

  # protection contrast (Protected - Unprotected)
  add_contrast("Protection", "protection", "Protected - Unprotected",
               Pobs[["protected"]], Pobs[["unprotected"]], keep,
               note = "all observations; protection set counterfactually, treatment as observed")
  for (g in gl)
    add_contrast("Protection", "protection", "Protected - Unprotected",
                 Pobs[["protected"]], Pobs[["unprotected"]], keep & obs_gld == g, guild = g,
                 note = "protection set counterfactually, treatment as observed")
  for (nm in names(tr))
    add_contrast("Protection", "protection", "Protected - Unprotected",
                 G[[key(tr[nm], pr[2])]], G[[key(tr[nm], pr[1])]], keep, treatment = lab[[nm]],
                 note = "all observations; treatment set counterfactually")

  # ---- 2. guild ---------------------------------------------------------------
  if (length(gl) > 1) {
    say(behaviour, ": guild")
    Gd <- lapply(gl, function(g) pred(setv(d, "guild", g)))
    names(Gd) <- gl
    for (g in gl[-1]) for (s in subs[seq_len(1 + length(pr))])
      add_contrast("Foraging guild", "guild", paste(g, "-", gl[1]), Gd[[g]], Gd[[gl[1]]], s$mask,
                   protection = s$protection,
                   note = "guild set counterfactually (descriptive predictive comparison)")
  }

  # ---- 3. grouping ------------------------------------------------------------
  say(behaviour, ": group")
  gb <- me_binary_levels(d$group)
  Gp1 <- pred(setv(d, "group", gb[2]))
  Gp0 <- pred(setv(d, "group", gb[1]))
  for (s in subs[seq_len(1 + length(pr))])
    add_contrast("Grouping", "group", "in group - solitary", Gp1, Gp0, s$mask, protection = s$protection)

  # ---- 4. size class ----------------------------------------------------------
  sl <- levels(factor(d$size_class))
  if (length(sl) > 1) {
    say(behaviour, ": size class")
    Gs <- lapply(sl, function(s) pred(setv(d, "size_class", s)))
    names(Gs) <- sl
    for (s in sl[-1])
      add_contrast("Size class", "size_class", paste(s, "-", sl[1]), Gs[[s]], Gs[[sl[1]]], keep)
  }

  # ---- 5. marginal slopes of continuous covariates (per 1 SD) ----------------
  slope_labels <- c(rugosity_mean = "Rugosity index (higher = more complex)",
                    biomass = "Algal / microbial cover (resource availability)")
  for (v in names(slope_labels)) {
    say(behaviour, ": slope of ", v)
    dp <- d; dp[[v]] <- d[[v]] + h
    dm <- d; dm[[v]] <- d[[v]] - h
    S <- (pred(dp) - pred(dm)) / (2 * h)
    for (s in subs[seq_len(1 + length(pr))])
      add(slope_labels[[v]], v, "marginal slope", "per 1 SD", "slope",
          rowMeans(S[, s$mask, drop = FALSE]), sum(s$mask), protection = s$protection)
  }

  res <- do.call(rbind, out)
  rownames(res) <- NULL
  res
}

# ---- figures ----------------------------------------------------------------

me_forest_plots <- function(tab, dir, width = 11, height = 8, dpi = 300) {
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("ggplot2 not installed")
  dir.create(dir, recursive = TRUE, showWarnings = FALSE)
  lv <- unique(tab$behaviour)
  tab$behaviour <- factor(tab$behaviour, levels = lv)
  base <- function(p) p +
    ggplot2::geom_vline(xintercept = 0, linetype = "dashed") +
    ggplot2::geom_linerange(ggplot2::aes(xmin = q5, xmax = q95), linewidth = 0.5,
                            position = ggplot2::position_dodge(width = 0.6)) +
    ggplot2::geom_linerange(ggplot2::aes(xmin = q25, xmax = q75), linewidth = 1.6,
                            position = ggplot2::position_dodge(width = 0.6)) +
    ggplot2::geom_point(size = 2.2, position = ggplot2::position_dodge(width = 0.6)) +
    ggplot2::theme_bw(base_size = 12) +
    ggplot2::theme(legend.position = "top", strip.text = ggplot2::element_text(size = 11))

  # (a) predator-model contrasts by protection and guild
  a <- tab[tab$term == "treatment" & tab$scale == "response" & !is.na(tab$protection) & !is.na(tab$guild) &
             tab$comparison %in% c("grouper - control model", "barracuda - control model"), ]
  if (nrow(a)) {
    p <- base(ggplot2::ggplot(a, ggplot2::aes(x = estimate, y = guild, colour = protection, shape = protection))) +
      ggplot2::facet_grid(comparison ~ behaviour, scales = "free_x") +
      ggplot2::scale_colour_brewer(palette = "Set1") +
      ggplot2::labs(x = "Average marginal effect (response scale; thin = 90%, thick = 50% interval)",
                    y = NULL, colour = NULL, shape = NULL)
    ggplot2::ggsave(file.path(dir, "treatment_effects.png"), p, width = width, height = height, dpi = dpi)
  }

  # (b) everything else, overall
  b <- tab[tab$term != "treatment" & tab$scale %in% c("response", "slope") & is.na(tab$protection) &
             is.na(tab$guild) & is.na(tab$treatment), ]
  if (nrow(b)) {
    b$label <- paste0(b$variable, ": ", b$comparison)
    p <- base(ggplot2::ggplot(b, ggplot2::aes(x = estimate, y = stats::reorder(label, estimate)))) +
      ggplot2::facet_wrap(~behaviour, scales = "free_x", nrow = 1) +
      ggplot2::labs(x = "Average marginal effect / slope per 1 SD (response scale)", y = NULL)
    ggplot2::ggsave(file.path(dir, "covariate_effects.png"), p, width = width, height = height, dpi = dpi)
  }
  invisible(TRUE)
}