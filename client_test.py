import tkinter as tk
from tkinter import messagebox
import re
import sys

from client import Client


def main():
    c = Client(None, 8080, "None", "password")
    c.run()


if __name__ == "__main__":
    main()
