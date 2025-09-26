pacman::p_load(brms, here, ordbetareg, tidybayes, ggplot2, marginaleffects)

source(here("functions", "summaries.R"))

# Set default ggplot theme
theme_set(
    theme_bw() +
        theme(
            legend.position = "top",
            legend.text = element_text(size = 14),
            strip.text = element_text(size = 14),
            axis.title = element_text(size = 14),
            axis.text = element_text(size = 12)
        )
)

dir.create(here("outputs", "behaviour-bites"), showWarnings = FALSE)
dir.create(here("figures", "behaviour-bites"), showWarnings = FALSE)

responses <- read.csv(here("outputs", "data", "response.csv"))
predictors <- read.csv(here("outputs", "data", "predictors.csv"))

moments_rugosity <- c(mean(predictors$rugosity_mean), sd(predictors$rugosity_mean))
moments_biomass <- c(mean(predictors$biomass), sd(predictors$biomass))

data <- responses %>%
  filter(bites > 0, !is.infinite(bites)) %>%
  left_join(predictors, by = c("plot_id" = "plot_id")) %>%
  select(-c(sponge)) %>%
  filter(guild != "Piscivore", guild != "Unknown")%>%
  filter(observed_duration > 45) %>%
  mutate(
    deployment_id = str_split(plot_id, "_", simplify = TRUE)[, 1],
    rugosity_mean = (rugosity_mean - moments_rugosity[1]) / moments_rugosity[2],
    biomass = (biomass - moments_biomass[1]) / moments_biomass[2],
    treatment = factor(treatment, levels = c("positive-control", "negative-control", "grouper", "barracuda")),
    protection = factor(protection, levels = c("Unprotected", "Protected")),
  ) %>%
  filter(!is.na(treatment), guild != "Unknown", guild != "") %>%
  distinct()

# analysis

# load models

model <- readRDS(here("outputs", "behaviour-bites", "model.rds"))

# plot posterior proportions by protection

counterfactual_treatment <- data %>%
    ungroup() %>%
    select(ind_id, plot_id, deployment_id, family, species, guild, size_class, protection, group, rugosity_mean, biomass) %>%
    distinct() %>%
    expand_grid(treatment = c("positive-control", "negative-control", "grouper", "barracuda")) %>%
    add_epred_draws(model, value = "prop") %>%
    ungroup()

# Counterfactual effect of treatment on bite rates

effect <- counterfactual_treatment %>%
    pivot_wider(names_from = treatment, values_from = prop, id_cols = c(".draw", "ind_id", "plot_id", "deployment_id", "protection", "size_class", "guild", "rugosity_mean", "biomass")) %>%
    mutate(
        effect_grouper = log2(grouper) - log2(`positive-control`),
        effect_barracuda = log2(barracuda) - log2(`positive-control`),
        effect_control = log2(`positive-control`) - log2(`negative-control`)
    ) %>%
    select(.draw, plot_id, deployment_id, protection, size_class, guild, effect_grouper, effect_barracuda, effect_control) %>%
    pivot_longer(cols = starts_with("effect"), names_to = "treatment", values_to = "effect") %>%
    mutate(treatment = recode(treatment, effect_grouper = "grouper", effect_barracuda = "barracuda", effect_control = "control"))


head(effect)

# Counterfactual effect of control on number individuals in plot

effect %>%
    filter(treatment == "control") %>%
    group_by(treatment, guild, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    ggplot(aes(x = guild, y = effect, col = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5)) +
    labs(x = "Foraging Guild", y = "Log odds ratio", col = "") 

ggsave(here("figures", "behaviour-bites", "control_plot.png"), plot = last_plot(), width = 10, height = 6)

# Summary control

P <- effect %>%
    filter(treatment == "control") %>%
    group_by(guild, treatment) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment == "control") %>%
    group_by(guild, treatment) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(guild, treatment, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    arrange(treatment) %>%
    mutate(
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        behaviour = "Behaviour",
        treatment = "Treatment",
        protection = "Protection",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "behaviour-bites", "counterfactual_control.docx"))

# Counterfactual effect of treatment on number individuals in plot

effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    ggplot(aes(x = guild, y = effect, col = protection)) +
    geom_hline(yintercept = 0, linetype = "dashed", color = "black") +
    geom_pointinterval(aes(ymin = .lower, ymax = .upper), position = position_dodge(width = 0.5)) +
    labs(x = "Foraging guild", y = "Log response ratio", col = "") +
    scale_color_brewer(palette = "Set1") +
    facet_wrap(~treatment)

ggsave(here("figures", "behaviour-bites", "effect_plot.png"), plot = last_plot(), width = 10, height = 6)

# Summary table

## Full

P <- effect %>%
    filter(treatment != "control") %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    group_by(treatment, guild, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    group_by(treatment, guild, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(guild, treatment, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)

table <- effect_summary %>%
    arrange(guild, treatment, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        behaviour = "Behaviour",
        treatment = "Treatment",
        protection = "Protection",
        guild = "Foraging Guild",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "behaviour-bites", "counterfactual_treatment_guild_protection.docx"))

## Treatmen x protection

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, protection) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, protection) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, protection, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    filter(treatment != "control") %>%
    arrange(treatment, protection) %>%
    mutate(
        protection = case_when(
            protection == "Protected" ~ "Inside PA",
            protection == "Unprotected" ~ "Outside PA"
        ),
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        behaviour = "Behaviour",
        treatment = "Treatment",
        protection = "Protection",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "behaviour-bites", "counterfactual_treatment_protection.docx"))

## Treatment x Guild

P <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild) %>%
    summarise(P = mean(effect > 0), .groups = "drop")

effect_summary <- effect %>%
    filter(treatment != "control") %>%
    group_by(treatment, guild) %>%
    median_qi(effect, .width = c(0.5, 0.9)) %>%
    pivot_wider(names_from = .width, values_from = c(.lower, .upper)) %>%
    left_join(P) %>%
    select(treatment, guild, effect, .lower_0.9, .lower_0.5, .upper_0.5, .upper_0.9, P)


table <- effect_summary %>%
    arrange(treatment, guild) %>%
    filter(guild %in% c("Herbivore", "Invertivore")) %>%
    mutate(
        treatment = case_when(
            treatment == "grouper" ~ "Grouper",
            treatment == "barracuda" ~ "Barracuda"
        )
    ) %>%
    mutate(across(where(is.numeric), ~ round(., 3))) %>%
    flextable() %>%
    set_header_labels(
        behaviour = "Behaviour",
        treatment = "Treatment",
        guild = "Foraging Guild",
        effect = "Median",
        .lower_0.9 = "90% Lower CI",
        .lower_0.5 = "50% Lower CI",
        .upper_0.5 = "50% Upper CI",
        .upper_0.9 = "90% Upper CI",
        P = "P(>0)"
    ) %>%
    merge_v(j = ) %>%
    theme_box() %>%
    set_table_properties(width = 0.5, layout = "fixed")

print(table)

save_as_docx(table, path = here("outputs", "behaviour-bites", "counterfactual_treatment_guild.docx"))
