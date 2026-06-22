import typer

from cli.sync import sync as sync_cmd
from cli.connect import connect as connect_cmd


app = typer.Typer(help="Alpaca CLI")


@app.callback()
def main():
  """Alpaca CLI"""


app.command(name="sync")(sync_cmd)
app.command(name="connect")(connect_cmd)

if __name__ == "__main__":
  app()
