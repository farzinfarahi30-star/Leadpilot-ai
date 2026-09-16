import marimo

app = marimo.App()

@app.cell
def _():
    return "NOVA_MOLAB_PUBLIC_PREVIEW_TEST"

if __name__ == "__main__":
    app.run()
