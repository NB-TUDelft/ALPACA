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

A host-side CLI (`alpaca`) copies board libraries over USB and opens a serial
REPL, so you never have to manage USB ports by hand. Firmware installation
uses the Pico's BOOTSEL mode and the ALPACA UF2 files.


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

### Flash firmware with BOOTSEL (normal student setup and updates)

Download the course-specified firmware from the
[ALPACA releases](https://github.com/NB-TUDelft/ALPACA/releases). Choose the
`alpaca-student-...uf2` file for the Student Pico and
`alpaca-helper-...uf2` for the Helper Pico, matching your board model.
The current build targets `RPI_PICO2`.

For each board that needs updating:

1. Disconnect its USB cable, hold **BOOTSEL**, and reconnect it to your computer.
2. Release BOOTSEL when the USB drive appears (`RP2350` for Pico 2).
3. Copy the matching `.uf2` file onto that drive. The Pico reboots automatically.

These images include MicroPython and the ALPACA libraries. **Students normally
do not need to run `alpaca sync` after flashing.** If the board was previously
synced, read the [FAQ](#faq) about removing filesystem overrides first.
The BOOTSEL procedure is also described in the
[Raspberry Pi documentation](https://www.raspberrypi.com/documentation/microcontrollers/micropython.html#drag-and-drop-micropython).

### Sync board libraries (development or an instructor-directed patch)

Use this to test changed board libraries without rebuilding the firmware.
Close any notebook or serial connection using the boards first.
**Back up files saved on the Picos: sync can delete files outside the library
set.** See the [FAQ](#faq) before using this on a student board.

```bash
# uv
uv run alpaca sync

# Conda (after conda activate ei-env)
alpaca sync
```

This selects connected Picos, copies the `common` + `student`/`helper` code
onto each selected board's filesystem, and soft-resets them. It uses the
libraries in your checkout, or those bundled in the installed `alpaca2`
package. To drop into a REPL on one board right after syncing:

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

## FAQ

### What is the difference between BOOTSEL flashing and `alpaca sync`?

| | BOOTSEL + ALPACA UF2 | `alpaca sync` |
| --- | --- | --- |
| Writes | Firmware containing MicroPython and frozen ALPACA libraries | Library files on the writable MicroPython filesystem |
| Requires | BOOTSEL USB drive mode | Running MicroPython and a USB serial connection |
| Library format | Precompiled MicroPython bytecode frozen into firmware | `.py` source files (minified by Belay) |
| Typical use | Student setup, released updates, firmware recovery | Development and instructor-directed temporary patches |

Sync does not rewrite the frozen modules or update MicroPython itself. With
the default MicroPython 1.28.0 RP2 import path, the current directory is searched
before frozen modules, so synced modules in the filesystem root **override
imports of their frozen counterparts**. They remain there after a reboot.
This follows MicroPython's
[runtime initialization](https://github.com/micropython/micropython/blob/v1.28.0/py/runtime.c)
and [RP2 initialization](https://github.com/micropython/micropython/blob/v1.28.0/ports/rp2/main.c).

Startup files are a special case: MicroPython 1.28.0 checks for frozen
`boot.py` and `main.py` before filesystem copies. Our Helper has a frozen
`main.py`, so syncing a changed `main.py` does not replace that startup script.
Use a new UF2 for startup changes. See MicroPython's
[`pyexec_file_if_exists`](https://github.com/micropython/micropython/blob/v1.28.0/shared/runtime/pyexec.c).

### What should students do when we publish a patch?

For a **board-code patch**, use the course-specified ALPACA UF2 release
containing the fix and flash the affected board(s) using BOOTSEL. Follow the
release instructions about which boards need updating. For a **desktop-only
patch** to the CLI or host library, update `alpaca2` in your Python environment;
the Picos do not need reflashing.

A Git commit alone does not update installed packages or boards. Maintainers
must publish a package or build a UF2 containing the patch before students can
get it through that route. If an instructor asks students to apply a library
patch through sync, first install the package containing it:

```bash
# Conda: the course YAML installs alpaca2 through pip
conda activate ei-env
python -m pip install --upgrade alpaca2
alpaca sync
```

```bash
# uv: published package in a working folder, outside this repository
uv pip install --upgrade alpaca2
uv run alpaca sync
```

When developing from a checkout, pull the intended patch and run `uv sync`,
then `uv run alpaca sync`. Sync uses that checkout's board libraries.
It does not download a patch itself. Back up board files before either sync
workflow; use UF2 flashing for changes to MicroPython or frozen startup files.

### Does syncing an up-to-date UF2 make it slower?

It can increase startup/import time and RAM use without adding a fix. The
frozen libraries are **MicroPython bytecode**, not Cython modules. The current
sync command uploads `.py` files without asking Belay to precompile them.
When those files shadow frozen imports, MicroPython must parse and compile
them on the Pico and keep the resulting bytecode in RAM. Frozen bytecode
avoids that compilation and runs directly from flash. See MicroPython's
[frozen-bytecode explanation](https://docs.micropython.org/en/v1.28.0/develop/optimizations.html#frozen-bytecode).

This does not imply a fixed slowdown in every measurement loop: both forms
execute MicroPython bytecode, and steady-state timing depends on the workload.
Extra RAM use can also increase garbage-collection pressure. The size of the
effect needs a hardware benchmark. **Keep the frozen libraries for
normal student use; do not sync an already up-to-date board just in case.**
Repeated syncs skip unchanged file contents, but leave the overrides in place.

### Can sync delete my saved programs?

Yes. The current CLI uses Belay's directory sync with its default cleanup:
filesystem files absent from the staged library set are deleted, except for
`boot.py`, `webrepl_cfg.py`, and `lib`. This can remove saved student scripts
and data. Files with matching library names can be overwritten. Frozen
firmware modules are unaffected. Keep a laptop copy of anything you need
before running sync.

### How do I return to the frozen libraries after syncing?

Back up your board files, remove the ALPACA filesystem copies created by sync,
and reset the Pico. Imports can then use the frozen versions again. Reflashing
a UF2 alone is not a guaranteed filesystem cleanup: surviving overrides can
still hide the new firmware's libraries.

For a completely clean course setup, follow the instructor's filesystem-cleanup
procedure or a [factory reset](https://docs.micropython.org/en/v1.28.0/rp2/tutorial/reset.html),
then flash the correct ALPACA UF2. A factory reset erases saved programs and
data as well as the overrides. Do not run sync again unless you need another
development patch.

## Building

The repository workflow should build and publish stubs, and assemble firmware images on creation of a version tag.

```sh
git tag v1.0.0
git push origin v1.0.0
```

The MicroPython version for firmware is set inside the `build-firmware.yml` (currently 1.28.0).
