import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium")


@app.cell
def _():
    # import libraries

    import pandas as pd

    return (pd,)


if __name__ == "__main__":
    app.run()
