import typer

from cli.generate_stubs import generate_stubs_cmd
from cli.sync import sync as sync_cmd
from cli.connect import connect as connect_cmd
from cli.list import list_devices as list_cmd


app = typer.Typer(help="Alpaca CLI")


@app.callback()
def main():
  """Alpaca CLI"""


app.command(name="sync")(sync_cmd)
app.command(name="connect")(connect_cmd)
app.command(name="list")(list_cmd)
app.command(name="generate-stubs")(generate_stubs_cmd)

if __name__ == "__main__":
  app()
