# ALPACA 2.0

> © Copyright Delft University of Technology, CC BY 4.0.

**ALPACA (Advanced Learning Platform for Analog Circuits and Automation)** is a device built on RP2 and MicroPython and equipped with several digital tools to be a guide in introduction to digital systems and electronics for NB2420 Electronic Instrumentation course of TU Delft.

ALPACA splits work across two Picos:

- **Student Pico**: the board a student writes code on via Belay. It exposes a tiny RPC
  client so student programs can ask the Helper to do things. Student Pico is equiiped with 
  a double channel DAC.

- **Helper**: a self-contained instrument. It drives an LCD and runs
  a set of measurement screens (voltmeter, component/resistance tester) that
  the user can cycles through. It also answers commands sent by the Student
  over a UART link.

A host-side CLI (`alpaca`) handles flashing your code onto the boards and
opening a serial REPL, so you never have to manage USB ports by hand.


The Student and Helper talk over UART0 with a crossover wiring and a shared
ground:

```
  Student GP00 (TX) ──► Helper GP13 (RX)
  Student GP01 (RX) ◄── Helper GP12 (TX)
  GND ◄──────────────► GND
```

## Repository layout

`📁 alpaca` folder contains the libraries for Picos.
`📁 src/alpaca` contains the desktop-side library and the ALPACA CLI for
managing the boards (`src/alpaca/cli`). It is published on PyPI as `alpaca2`,
but the import name and the command stay `alpaca`, so installed users write
`from alpaca import list_boards`.

`alpaca/common` is copied alongside `alpaca/student` or `alpaca/helper` onto
each board at sync time, which is why on-device imports are flat
(`from command import ...`, `from link import ...`).

Therefore if the folders are like this

```
📁 alpaca/
  📁 common/
    📄 A.py
  📁 student/
    📄 B.py
  📁 helper/
    📄 C.py
```

using `alpaca sync` will copy the files to the root as:

```
🍓 HelperPico
  📄 A.py
  📄 C.py

🍓 StudentPico
  📄 A.py
  📄 B.py
```

## Installation

Choose the instructions for your environment manager. ALPACA requires Python
3.14 or newer. The package is called `alpaca2`; the Python import and CLI
command are both called `alpaca`.

### uv users

To work from this repository, open a terminal in the repository root and run:

```bash
uv sync
```

This creates the project's `.venv`, installs the project and its dependencies,
and makes the CLI available through `uv run alpaca`.

To use the published package without cloning this repository, run the following
in your working folder:

```bash
uv venv --python 3.14
uv pip install alpaca2
```

Run `uv run alpaca` commands from the same folder. In VS Code, select this
folder's `.venv` using **Python: Select Interpreter** (and select it as the
kernel when working in a notebook).

### Conda users (course students)

Follow the course manual's Software Installation instructions. You will need
Conda and VS Code, and a separate environment named `ei-env`.

Download
[`ei-env.yaml`](https://github.com/NB-TUDelft/Electronic_Instrumentation/blob/HEAD/book/static/ei-env.yaml)
from the course manuals and open a terminal with Conda available. Change to
the folder where you saved the file; for example, on macOS:

```bash
cd ~/Downloads
```

Create and activate the course environment:

```bash
conda env create -f ei-env.yaml
conda activate ei-env
```

The YAML file installs Python 3.14 or newer, the course's scientific Python
packages, notebook tools, `alpaca2`, Belay, and the MicroPython RP2 stubs.
You do not need to install `alpaca2` separately. If you already created
`ei-env` following the manual, just activate it.

In VS Code, press **Ctrl/Cmd+Shift+P**, choose **Python: Select Interpreter**,
and select `ei-env`. For notebooks, also select `ei-env` as the kernel.
Activate `ei-env` in each new terminal before running `alpaca` commands.

## Usage

Use `uv run alpaca` with uv, or `alpaca` in an activated Conda environment.
Both run the same CLI.

### Sync your code onto the boards

```bash
# uv
uv run alpaca sync

# Conda (after conda activate ei-env)
alpaca sync
```

This discovers connected Picos, copies the `common` + `student`/`helper` code
onto each, and soft-resets them. To drop into a REPL on one board right after
syncing:

```bash
# uv
uv run alpaca sync --connect student

# Conda
alpaca sync --connect student
```

### Open a serial REPL

```bash
# uv
uv run alpaca connect student   # or: helper

# Conda
alpaca connect student          # or: helper
```

### Picking a board

The first time the CLI needs a board it lists the connected Picos in a terminal
menu. Hovering an entry lights that board's onboard LED so you can tell
which is which, and you can choose to remember the selection — it's cached per
role under `.alpaca/` so later runs skip the prompt.

## Building

The repository workflow should build and publish stubs, and assemble firmware images on creation of a version tag.

```sh
git tag v1.0.0
git push origin v1.0.0
```

The MicroPython version for firmware is set inside the `build-firmware.yml` (currently 1.28.0).
