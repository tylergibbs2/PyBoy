#!/usr/bin/env python3
#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import argparse
import os

from pyboy import PyBoy, core
from pyboy.logger import log_level, logger
from pyboy.plugins.manager import parser_arguments
from pyboy.pyboy import defaults

INTERNAL_LOADSTATE = "INTERNAL_LOADSTATE_TOKEN"


def color_tuple(string):
    color_palette = [int(c.strip(), 16) for c in string.split(",")]
    assert len(color_palette) == 4, f"Not the correct amount of colors! Expected four, got {len(color_palette)}"
    return color_palette


def valid_file_path(path):
    if not path == INTERNAL_LOADSTATE and not os.path.isfile(path):
        logger.error(f"Filepath '{path}' couldn't be found, or isn't a file!")
        exit(1)
    return path


parser = argparse.ArgumentParser(
    description="PyBoy -- Game Boy emulator written in Python",
    epilog="Warning: Features marked with (internal use) might be subject to change.",
)
parser.add_argument("ROM", type=valid_file_path, help="Path to a Game Boy compatible ROM file")
parser.add_argument("-b", "--bootrom", type=valid_file_path, help="Path to a boot-ROM file")
parser.add_argument("--profiling", action="store_true", help="Enable opcode profiling (internal use)")
parser.add_argument("--randomize-ram", action="store_true", help="Randomize Game Boy RAM on startup")
parser.add_argument(
    "--log-level",
    default="INFO",
    type=str,
    choices=["ERROR", "WARNING", "INFO", "DEBUG", "DISABLE"],
    help="Set logging level"
)
parser.add_argument(
    "--color-palette",
    type=color_tuple,
    default=defaults["color_palette"],
    help=('Four comma seperated, hexadecimal, RGB values for colors (i.e. "FFFFFF,999999,555555,000000")')
)
parser.add_argument(
    "-l",
    "--loadstate",
    nargs="?",
    default=None,
    const=INTERNAL_LOADSTATE,
    type=valid_file_path,
    help=(
        "Load state from file. If filepath is specified, it will load the given path. Otherwise, it will automatically "
        "locate a saved state next to the ROM file."
    )
)
parser.add_argument(
    "-w",
    "--window-type",
    "--window",
    default=defaults["window_type"],
    type=str,
    choices=["OpenGL", "headless", "dummy"],
    help="Specify window-type to use"
)
parser.add_argument("-s", "--scale", default=defaults["scale"], type=int, help="The scaling multiplier for the window")
parser.add_argument("--disable-renderer", action="store_true", help="Disables screen rendering for higher performance")
parser.add_argument("--sound", action="store_true", help="Enable sound (beta)")

for arguments in parser_arguments():
    for a in arguments:
        *args, kwargs = a
        if args[0] not in parser._option_string_actions:
            parser.add_argument(*args, **kwargs)


def main():
    argv = parser.parse_args()
    log_level(argv.log_level)

    logger.info(
        """
The Game Boy controls are as follows:

| Keyboard key | GameBoy equivalant |
| ---          | ---                |
| Up           | Up                 |
| Down         | Down               |
| Left         | Left               |
| Right        | Right              |
| A            | A                  |
| S            | B                  |
| Return       | Start              |
| Backspace    | Select             |

The other controls for the emulator:

| Keyboard key | Emulator function       |
| ---          | ---                     |
| Escape       | Quit                    |
| D            | Debug                   |
| Space        | Unlimited FPS           |
| Z            | Save state              |
| X            | Load state              |
| I            | Toggle screen recording |
| O            | Save screenshot         |
| ,            | Rewind backwards        |
| .            | Rewind forward          |
| J            | Memory Window + 0x100   |
| K            | Memory Window - 0x100   |
| Shift + J    | Memory Window + 0x1000  |
| Shift + K    | Memory Window - 0x1000  |

See "pyboy --help" for how to enable rewind and other awesome features!
"""
    )

    # Start PyBoy and run loop
    pyboy = PyBoy(argv.ROM, **vars(argv))

    if argv.loadstate is not None:
        if argv.loadstate == INTERNAL_LOADSTATE:
            # Guess filepath from ROM path
            state_path = argv.ROM + ".state"
        else:
            # Use filepath given
            state_path = argv.loadstate

        valid_file_path(state_path)
        with open(state_path, "rb") as f:
            pyboy.load_state(f)

    while not pyboy.tick():
        pass

    pyboy.stop()

    if argv.profiling:
        print("\n".join(profiling_printer(pyboy._cpu_hitrate())))


def profiling_printer(hitrate):
    print("Profiling report:")
    from operator import itemgetter
    names = [core.opcodes.CPU_COMMANDS[n] for n in range(0x200)]
    for hits, opcode, name in sorted(filter(itemgetter(0), zip(hitrate, range(0x200), names)), reverse=True):
        yield ("%3x %16s %s" % (opcode, name, hits))


if __name__ == "__main__":
    main()
