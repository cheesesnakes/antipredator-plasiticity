# make sure pacman is installed and loaded
if (!requireNamespace("pacman", quietly = TRUE)) {
    install.packages("pacman")
}

# Load necessary packages

pacman::p_load("here", "dplyr", "tidyr", "flextable", "stringr")

i_am("functions/summary_tables.R")

folder <- "outputs/analysis"

# 1. Comparing effects across treatments

compare_df <- read.csv(here(folder, "compare_effects_treatment.csv"))

df <- read.csv(here(folder, "summary_effects_treatment.csv"))

df <- df %>%
    left_join(compare_df, by = c("Behaviour"))

table <- df %>%
    select(Behaviour, , Grouper...Barracuda, Treatment, everything()) %>%
    arrange(Behaviour, Treatment, Grouper...Barracuda) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~Behaviour) %>%
    set_header_labels(
        Treatment = "Treatment",
        Behaviour = "Behaviour",
        Grouper...Barracuda = "P(Grouper > Barracuda)",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_effects_treatment.docx"))

# 2. Comparing response across guild

compare_df <- read.csv(here(folder, "compare_response_guild.csv"))

df <- read.csv(here(folder, "summary_response_guild.csv"))

df <- df %>%
    left_join(compare_df, by = c("Behaviour", "guild"))

table <- df %>%
    select(guild, Behaviour, Grouper...Barracuda, Treatment, everything()) %>%
    arrange(guild, Behaviour, Grouper...Barracuda, Treatment) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ guild + Behaviour + Grouper...Barracuda + Treatment) %>%
    set_header_labels(
        Treatment = "Treatment",
        Protection = "Protection Level",
        guild = "Guild",
        Behaviour = "Behaviour",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)",
        Grouper...Barracuda = "P(Grouper > Barracuda)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_response_guild.docx"))

# 3. Comparing response protection

compare_df <- read.csv(here(folder, "compare_response_protection.csv"))

df <- read.csv(here(folder, "summary_response_protection.csv"))

df <- df %>%
    left_join(compare_df, by = c("Behaviour", "Protection"))

compare_protection <- read.csv(here(folder, "effect_protection.csv"))

df <- df %>%
    left_join(compare_protection, by = c("Behaviour", "Treatment"))

table <- df %>%
    select(Behaviour, Treatment, Difference, Protection, everything()) %>%
    arrange(Behaviour, Treatment, Protection) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Behaviour + Treatment + Difference + Protection) %>%
    set_header_labels(
        Treatment = "Treatment",
        Protection = "Protection Level",
        Behaviour = "Behaviour",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)",
        Difference = "P(Inside > Outside)"
    )

# Save the table
save_as_docx(table, path = here("outputs", "summary_response_protection.docx"))

# 4. Comparing response protection by size

compare_df <- read.csv(here(folder, "compare_response_size.csv"))

df <- read.csv(here(folder, "summary_response_size.csv"))

df <- df %>%
    left_join(compare_df, by = c("Behaviour", "size_class"))

table <- df %>%
    select(Behaviour, size_class, Grouper...Barracuda, Treatment, everything()) %>%
    arrange(Behaviour, size_class, Treatment) %>%
    mutate_if(is.numeric, round, 3) %>%
    flextable() %>%
    set_table_properties(width = 0.9, layout = "fixed") %>%
    set_caption("Log-fold change") %>%
    # center the text
    align(align = "center", part = "all") %>%
    theme_box() %>%
    merge_v(~ Behaviour + size_class + Grouper...Barracuda + Treatment) %>%
    set_header_labels(
        Treatment = "Treatment",
        size_class = "Size Class",
        Behaviour = "Behaviour",
        Protection = "Protection Level",
        X5th = "5th Percentile",
        X25th = "25th Percentile",
        X75th = "75th Percentile",
        X95th = "95th Percentile",
        P...0. = "P(> 0)",
        Grouper...Barracuda = "P(Grouper > Barracuda)"
    )
# Save the table
save_as_docx(table, path = here("outputs", "summary_response_size.docx"))
