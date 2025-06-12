# make sure pacman is installed and loaded
if (!requireNamespace("pacman", quietly = TRUE)) {
    install.packages("pacman")
}

# Load necessary packages

pacman::p_load("here", "dplyr", "tidyr", "flextable", "stringr")

i_am("functions/summary_tables.R")

# Create pretty table of model parameter summaries

parameters <- read.csv(here("outputs/parameter_summary.csv"))

parameters <- parameters %>%
    mutate(
        Behaviour = case_when(
            Parameter %in% c("sigma", "zeta", "gamma") ~ Variable,
            TRUE ~ Behaviour
        ),
        Variable = case_when(
            Parameter %in% c("sigma", "zeta", "gamma") ~ "",
            TRUE ~ Variable
        ),
        Parameter = case_when(
            Parameter == "beta" ~ "Protection",
            Parameter == "gamma" ~ "Rugosity",
            Parameter == "zeta" ~ "Biomass",
            Parameter == "eta" ~ "Predator Presence",
            Parameter == "omega" ~ "Size Class",
            Parameter == "epsilon" ~ "Foraging Guild",
            Parameter == "delta" ~ "Grouping",
            Parameter == "theta" ~ "Treatment",
            Parameter == "sigma" ~ "Scale",
            TRUE ~ Parameter
        ),
    ) %>%
    mutate_at(vars(Variable), ~ str_to_sentence(.)) %>%
    select(Parameter, Variable, Behaviour, Model, everything()) %>%
    group_by(Parameter, Variable, Behaviour, Model) %>%
    arrange(Parameter, Variable, Behaviour, Model) %>%
    rename(Level = Variable)


parameters_table <- flextable(parameters) %>%
    set_header_labels(
        Standard.Deviation = "SD",
        Lower.89..HDI = "Lower 89% HDI",
        Upper.89..HDI = "Upper 89% HDI",
        MCSE.Mean = "MCSE Mean",
        MCSE.SD = "MCSE SD",
        ESS.Bulk = "ESS Bulk",
        ESS.Tail = "ESS Tail",
        R.Hat = "R-Hat"
    ) %>%
    merge_v(~ Parameter + Level + Behaviour + Model) %>%
    set_table_properties(layout = "fixed", width = 0.9) %>%
    theme_box()

save_as_docx(parameters_table, path = here("outputs/parameter_summary.docx"))
