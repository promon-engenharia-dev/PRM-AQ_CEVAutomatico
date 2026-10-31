"""Ponto de entrada do executável (PyInstaller). Equivale a `python -m verificador`."""
import sys

from verificador.cli import main

sys.exit(main())
