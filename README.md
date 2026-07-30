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
`📁 main` contains the desktop-side library. It is published under the import
name `alpaca` (see the `sources` mapping in `pyproject.toml`), so installed
users write `from alpaca import list_boards`.
`📁 cli` contains the ALPACA CLI for managing the boards 

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

## Setup

```bash
uv sync
```

This installs the project and exposes the `alpaca` command.

## Usage

### Sync your code onto the boards

```bash
uv run alpaca sync
```

This discovers connected Picos, copies the `common` + `student`/`helper` code
onto each, and soft-resets them. To drop into a REPL on one board right after
syncing:

```bash
uv run alpaca sync --connect student
```

### Open a serial REPL

```bash
uv run alpaca connect student   # or: helper
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