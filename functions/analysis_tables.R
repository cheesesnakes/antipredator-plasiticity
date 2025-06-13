# make sure pacman is installed and loaded
if (!requireNamespace("pacman", quietly = TRUE)) {
    install.packages("pacman")
}

# Load necessary packages

pacman::p_load("here", "dplyr", "tidyr", "flextable", "stringr")

i_am("functions/summary_tables.R")

folder <- "outputs/analysis"

# 1. Comparing effects across treatments

df <- read.csv(here(folder, "compare_effects_treatment.csv"))

table <- df %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_header_labels(
        Grouper...Barracuda = "Grouper > Barracuda",
        Barracuda...Positive.Control = "Barracuda > Positive Control",
        Grouper...Positive.Control = "Grouper > Positive Control"
    ) %>%
    set_table_properties(width = 0.9, layout = "autofit") %>%
    set_caption("Posterior probability") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box()

# Save the table
save_as_docx(table, path = here("outputs", "compare_effects_treatment.docx"))

# 2. Comparing response across guild

df <- read.csv(here(folder, "compare_response_guild.csv"))

table <- df %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Posterior probability") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~Behaviour) %>%
    set_header_labels(
        guild = "Guild",
        Outside.PA...Inside.PA..Grouper. = "Outside PA > Inside PA (Grouper)",
        Outside.PA...Inside.PA..Barracuda. = "Outside PA > Inside PA (Barracuda)",
        Outside.PA...Inside.PA..Positive.Control. = "Outside PA > Inside PA (Positive Control)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "compare_response_guild.docx"))

# 3. Comparing response protection

df <- read.csv(here(folder, "compare_response_protection.csv"))

table <- df %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Posterior probability") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~Behaviour) %>%
    set_header_labels(
        Outside.PA...Inside.PA..Grouper. = "Outside PA > Inside PA (Grouper)",
        Outside.PA...Inside.PA..Barracuda. = "Outside PA > Inside PA (Barracuda)",
        Outside.PA...Inside.PA..Positive.Control. = "Outside PA > Inside PA (Positive Control)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "compare_response_protection.docx"))

# 4. Comparing response protection by size

df <- read.csv(here(folder, "compare_response_size.csv"))

table <- df %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Posterior probability") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~Behaviour) %>%
    set_header_labels(
        size_class = "Size Class",
        Outside.PA...Inside.PA..Grouper. = "Outside PA > Inside PA (Grouper)",
        Outside.PA...Inside.PA..Barracuda. = "Outside PA > Inside PA (Barracuda)",
        Outside.PA...Inside.PA..Positive.Control. = "Outside PA > Inside PA (Positive Control)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "compare_response_size.docx"))

# 5. summary of effects by treatment
df <- read.csv(here(folder, "summary_effects_treatment.csv"))

table <- df %>%
    arrange(Treatment, Behaviour) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Treatment + Behaviour) %>%
    set_header_labels(
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_effects_treatment.docx"))

# 6. summary of effects by guild
df <- read.csv(here(folder, "summary_response_guild.csv"))

table <- df %>%
    select(Treatment, guild, Behaviour, Protection, everything()) %>%
    arrange(Treatment, guild, Behaviour, Protection) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Treatment + guild + Behaviour) %>%
    set_header_labels(
        Treatment = "Treatment",
        Protection = "Protection Level",
        guild = "Guild",
        Behaviour = "Behaviour",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_response_guild.docx"))

# 7. summary of effects by protection
df <- read.csv(here(folder, "summary_response_protection.csv"))

table <- df %>%
    select(Treatment, Behaviour, Protection, everything()) %>%
    arrange(Treatment, Behaviour, Protection) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Treatment + Behaviour + Protection) %>%
    set_header_labels(
        Treatment = "Treatment",
        Protection = "Protection Level",
        Behaviour = "Behaviour",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_response_protection.docx"))

# 8. summary of effects by size
df <- read.csv(here(folder, "summary_response_size.csv"))

table <- df %>%
    select(Treatment, Behaviour, size_class, everything()) %>%
    arrange(Treatment, Behaviour, size_class) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Treatment + Behaviour + size_class) %>%
    set_header_labels(
        Treatment = "Treatment",
        size_class = "Size Class",
        Behaviour = "Behaviour",
        Protection = "Protection Level",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_response_size.docx"))
