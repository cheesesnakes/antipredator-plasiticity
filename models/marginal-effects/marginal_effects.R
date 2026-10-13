# =============================================================================
# models/marginal-effects/marginal_effects.R
#
# Builds ONE table of average marginal effects (contrasts and slopes) for every
# behaviour model, from the models already saved by
#   models/behaviour-time/model.R   -> outputs/behaviour-time/model_<behaviour>.rds
#   models/behaviour-bites/model.R  -> outputs/behaviour-bites/model.rds
#
# Run from the project root (here() finds it via .Rprofile / renv):
#   Rscript models/marginal-effects/marginal_effects.R
#
# Outputs
#   outputs/marginal-effects/marginal_effects_table.csv   <- the single table
#   outputs/marginal-effects/marginal_effects_table.rds
#   outputs/marginal-effects/marginal_effects_table.docx  (optional)
#   outputs/marginal-effects/cache/<behaviour>.rds        (per-model cache)
#   figures/marginal-effects/*.png
#
# Notes
#   * rugosity_mean and biomass were standardised in model.R, so slopes are per
#     1 SD. SDs in original units are added as a column when predictors.csv exists.
#   * The *_log2 rows use log2 (as in counterfactuals.R), NOT natural log.
# =============================================================================

pacman::p_load(brms, ordbetareg, here, ggplot2, flextable)
# ordbetareg must be loaded so that posterior_epred() knows the custom family.

# ---- settings ---------------------------------------------------------------

FORCE         <- FALSE   # TRUE = ignore cached results and recompute
STRICT        <- FALSE   # TRUE = stop if any model file is missing (FALSE = skip it with a warning)
NDRAWS        <- NULL    # NULL = all posterior draws; e.g. 1000 for a quick run
SEED          <- 2025    # only used when NDRAWS is set
RE_FORMULA    <- NULL    # NULL = include observed group-level effects (as in counterfactuals.R); NA = population level
GUILDS        <- c("Herbivore", "Invertivore")  # NULL = all guilds in the model data
STEP          <- 0.01    # finite-difference step (SD units) for marginal slopes
MAKE_FIGURES  <- TRUE
MAKE_DOCX     <- TRUE

# ---- paths ------------------------------------------------------------------

source_file <- here("functions", "marginal_effects.R")
if (!file.exists(source_file)) stop("Cannot find ", source_file, ". Run from the project root.")
source(source_file)

out_dir   <- here("outputs", "marginal-effects")
cache_dir <- file.path(out_dir, "cache")
fig_dir   <- here("figures", "marginal-effects")
for (d in c(out_dir, cache_dir, fig_dir)) dir.create(d, recursive = TRUE, showWarnings = FALSE)

# one entry per model: behaviour label, response type, saved model file
models <- list(
  list(behaviour = "Foraging",  kind = "proportion", file = here("outputs", "behaviour-time",  "model_foraging.rds"),  script = "models/behaviour-time/model.R"),
  list(behaviour = "Vigilance", kind = "proportion", file = here("outputs", "behaviour-time",  "model_vigilance.rds"), script = "models/behaviour-time/model.R"),
  list(behaviour = "Movement",  kind = "proportion", file = here("outputs", "behaviour-time",  "model_movement.rds"),  script = "models/behaviour-time/model.R"),
  list(behaviour = "Bite rate", kind = "rate",       file = here("outputs", "behaviour-bites", "model.rds"),           script = "models/behaviour-bites/model.R")
)

# ---- guard: model files -----------------------------------------------------

missing <- Filter(function(m) !file.exists(m$file), models)
if (length(missing)) {
  msg <- paste0("Saved model not found for: ", paste(vapply(missing, `[[`, "", "behaviour"), collapse = ", "),
                ".\n  Missing: ", paste(vapply(missing, `[[`, "", "file"), collapse = "\n           "),
                "\n  Fit them first with: ", paste(unique(vapply(missing, `[[`, "", "script")), collapse = ", "))
  if (STRICT) stop(msg, call. = FALSE)
  warning(msg, call. = FALSE)
  models <- Filter(function(m) file.exists(m$file), models)
}
if (!length(models)) stop("No saved models found - nothing to do.", call. = FALSE)

# ---- optional: SDs in original units (guard: predictors.csv) ----------------

pred_file <- here("outputs", "data", "predictors.csv")
sd_orig <- c(rugosity_mean = NA_real_, biomass = NA_real_)
if (file.exists(pred_file)) {
  predictors <- read.csv(pred_file)
  sd_orig["rugosity_mean"] <- sd(predictors$rugosity_mean, na.rm = TRUE)
  sd_orig["biomass"]       <- sd(predictors$biomass, na.rm = TRUE)
} else {
  message("predictors.csv not found (run `uv run cleaning.py`); SDs in original units will be NA.")
}

# ---- compute (with per-model cache) -----------------------------------------

settings <- list(version = ME_VERSION, ndraws = NDRAWS, seed = SEED, re = RE_FORMULA,
                 guilds = GUILDS, step = STEP)

results <- lapply(models, function(m) {
  info <- file.info(m$file)
  cache_key  <- list(settings = settings, model_size = info$size, model_mtime = as.numeric(info$mtime))
  cache_file <- file.path(cache_dir, paste0(gsub("[^A-Za-z0-9]+", "_", tolower(m$behaviour)), ".rds"))

  if (!FORCE && file.exists(cache_file)) {
    cached <- tryCatch(readRDS(cache_file), error = function(e) NULL)
    if (!is.null(cached) && identical(cached$key, cache_key)) {
      message(m$behaviour, ": using cached result (set FORCE <- TRUE to recompute)")
      return(cached$result)
    }
  }

  message(m$behaviour, ": loading ", m$file)
  fit <- tryCatch(readRDS(m$file), error = function(e) {
    warning(m$behaviour, ": could not read model (", conditionMessage(e), ")", call. = FALSE); NULL
  })
  if (is.null(fit)) return(NULL)
  if (!inherits(fit, "brmsfit") || is.null(fit$data)) {
    warning(m$behaviour, ": file is not a brmsfit with stored data; skipped", call. = FALSE)
    return(NULL)
  }

  draw_ids <- NULL
  if (!is.null(NDRAWS)) {
    total <- brms::ndraws(fit)
    set.seed(SEED)
    draw_ids <- sort(sample.int(total, min(NDRAWS, total)))
  }

  result <- tryCatch(
    me_compute(fit, behaviour = m$behaviour, kind = m$kind, guilds = GUILDS,
               draw_ids = draw_ids, re_formula = RE_FORMULA, h = STEP),
    error = function(e) { warning(m$behaviour, ": failed - ", conditionMessage(e), call. = FALSE); NULL }
  )
  if (is.null(result)) return(NULL)

  saveRDS(list(key = cache_key, result = result), cache_file)
  rm(fit); gc(verbose = FALSE)
  result
})

results <- Filter(Negate(is.null), results)
if (!length(results)) stop("No marginal effects could be computed.", call. = FALSE)

# ---- single table -----------------------------------------------------------

tab <- do.call(rbind, results)
tab$sd_original_units <- ifelse(tab$term %in% names(sd_orig), unname(sd_orig[tab$term]), NA_real_)

cols <- c("behaviour", "variable", "term", "type", "comparison", "protection", "guild", "treatment",
          "scale", "unit", "n_obs", "ref_mean", "estimate", "mean", "q5", "q25", "q75", "q95",
          "P_gt0", "sd_original_units", "note")
tab <- tab[, cols]
tab$behaviour <- factor(tab$behaviour, levels = vapply(models, `[[`, "", "behaviour"))
tab <- tab[order(tab$behaviour, match(tab$term, c("treatment", "protection", "guild", "group", "size_class", "rugosity_mean", "biomass")),
                tab$comparison, match(tab$scale, c("response", "slope", "log2")),
                tab$treatment, tab$protection, tab$guild, na.last = FALSE), ]
tab$behaviour <- as.character(tab$behaviour)
rownames(tab) <- NULL

num <- vapply(tab, is.numeric, logical(1))
tab_out <- tab
tab_out[num] <- lapply(tab_out[num], function(x) signif(x, 4))

csv_file <- file.path(out_dir, "marginal_effects_table.csv")
write.csv(tab_out, csv_file, row.names = FALSE, na = "")
saveRDS(tab, file.path(out_dir, "marginal_effects_table.rds"))
message("Wrote ", nrow(tab), " rows -> ", csv_file)

# ---- optional docx ----------------------------------------------------------

if (MAKE_DOCX) {
  tryCatch({
    ft <- flextable::flextable(tab_out[, setdiff(cols, c("type", "n_obs", "sd_original_units"))])
    ft <- flextable::set_header_labels(ft, estimate = "Median", mean = "Mean", q5 = "90% lower",
                                       q25 = "50% lower", q75 = "50% upper", q95 = "90% upper",
                                       P_gt0 = "P(>0)", ref_mean = "Reference mean")
    ft <- flextable::theme_box(ft)
    ft <- flextable::fontsize(ft, size = 7, part = "all")
    flextable::save_as_docx(ft, path = file.path(out_dir, "marginal_effects_table.docx"),
                            pr_section = officer::prop_section(
                              page_size = officer::page_size(orient = "landscape")))
  }, error = function(e) warning("Could not write docx: ", conditionMessage(e), call. = FALSE))
}

# ---- optional figures -------------------------------------------------------

if (MAKE_FIGURES) {
  tryCatch(me_forest_plots(tab, fig_dir),
           error = function(e) warning("Could not make figures: ", conditionMessage(e), call. = FALSE))
}

message("Done.")