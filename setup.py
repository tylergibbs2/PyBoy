import distutils.cmd
import multiprocessing
import os
import platform
import shutil
import subprocess
import sys
from distutils.command.clean import clean as _clean
from distutils.command.clean import log
from distutils.dir_util import remove_tree
from multiprocessing import cpu_count
from pathlib import Path

from setuptools import Extension, find_packages, setup
from setuptools.command.test import test

from tests.utils import kirby_rom, supermarioland_rom, tetris_rom

# The requirements.txt file will not be included in the PyPi package
REQUIREMENTS = """\
# Change in setup.py
cython>=0.29.16; platform_python_implementation == 'CPython'
numpy; python_version >= '3.7' or platform_python_implementation == 'PyPy'
numpy<=1.19; python_version < '3.7' and platform_python_implementation == 'CPython'
pillow
"""


def load_requirements(filename):
    if os.path.isfile(filename):
        with open(filename, "w") as f:
            f.write(REQUIREMENTS)
    return [line.strip() for line in REQUIREMENTS.splitlines()]


requirements = load_requirements("requirements.txt")

MSYS = os.getenv("MSYS")
CYTHON = platform.python_implementation() != "PyPy"
py_version = platform.python_version()[:3]


try:
    for r in requirements:
        if r.startswith("cython"):
            break
    else:
        r = None
    requirements.remove(r)
except ValueError:
    pass

class build_ext(distutils.cmd.Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        pass


DEBUG = os.getenv("DEBUG")
with open("pyboy/core/debug.pxi", "w") as f:
    f.writelines([
        "#\n",
        "# License: See LICENSE.md file\n",
        "# GitHub: https://github.com/Baekalfen/PyBoy\n",
        "#\n",
        f"DEF DEBUG={int(bool(DEBUG))}\n",
    ])

ROOT_DIR = "pyboy"


# Add inplace functionality to the clean command
class clean(_clean):
    user_options = _clean.user_options + [("inplace", "i", "remove all output from an inplace build")]
    boolean_options = _clean.boolean_options + ["inplace"]

    def initialize_options(self):
        super().initialize_options()
        self.inplace = None

    def run(self):
        super().run()
        if self.inplace:
            for p in ("PyBoy.egg-info", "build", "dist"):
                if os.path.isdir(p):
                    shutil.rmtree(p)

            for root, dirs, files in os.walk(ROOT_DIR):
                if "__pycache__" in dirs:
                    log.info(f"removing: {os.path.join(root, '__pycache__')}")
                    remove_tree(os.path.join(root, "__pycache__"))
                for f in files:
                    if os.path.splitext(f)[1] in (
                        ".pyo", ".pyc", ".pyd", ".so", ".c", ".h", ".dll", ".lib", ".exp", ".html"
                    ):
                        print(f"removing: {os.path.join(root, f)}")
                        os.remove(os.path.join(root, f))


def prep_pxd_py_files():
    ignore_py_files = ["__main__.py", "manager_gen.py", "opcodes_gen.py"]
    # Cython doesn't trigger a recompile on .py files, where only the .pxd file has changed. So we fix this here.
    # We also yield the py_files that have a .pxd file, as we feed these into the cythonize call.
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if os.path.splitext(f)[1] == ".py" and f not in ignore_py_files:
                yield os.path.join(root, f)
            if os.path.splitext(f)[1] == ".pxd":
                py_file = os.path.join(root, os.path.splitext(f)[0]) + ".py"
                if os.path.isfile(py_file):
                    if os.path.getmtime(os.path.join(root, f)) > os.path.getmtime(py_file):
                        os.utime(py_file)

try:
    this_directory = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(this_directory, "README.md"), encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    print("README.md not found")
    long_description = ""

setup(
    name="pyboy",
    version="1.4.1",
    packages=find_packages(),
    author="Mads Ynddal",
    author_email="mads-pyboy@ynddal.dk",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Baekalfen/PyBoy",
    classifiers=[
        "License :: Free for non-commercial use",
        "Operating System :: OS Independent",
        "Programming Language :: Cython",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: System :: Emulators",
    ],
    entry_points={
        "console_scripts": ["pyboy = pyboy.__main__:main", ],
    },
    cmdclass={
        "build_ext": build_ext,
        "clean": clean
    },
    install_requires=requirements,
    tests_require=[
        *requirements,
        "pytest>=6.0.0",
        "pytest-xdist",
        "pyopengl",
        "scipy<=1.5.3; python_version < '3.7' and platform_python_implementation == 'CPython'",
        "gym" if CYTHON and not MSYS and py_version != "3.9" and not (sys.platform == "win32" and py_version == "3.8")
        else "",
    ],
    extras_require={
        "all": [
            "pyopengl",
            "markdown",
            "pdoc3",
            "scipy<=1.5.3; python_version < '3.7' and platform_python_implementation == 'CPython'",
            "gym" if CYTHON and not MSYS and py_version != "3.9" and
            not (sys.platform == "win32" and py_version == "3.8") else "",
        ],
    },
    zip_safe=(not CYTHON), # Cython doesn't support it
    ext_modules=None,
    python_requires=">=3.6",
    package_data={"": ["*.pxi", "*.pyx", "*.pxd", "*.c", "*.h", "bootrom.bin", "font.txt"]},
)
