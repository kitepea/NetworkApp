import tkinter as tk
from tkinter import messagebox
import re
from threading import Thread, Lock
import time
import sys

from server import Server

SERVERPORT = 8080


def main():
    s = Server(SERVERPORT)
    s.start()
    s.checkStatus()  # still in loading stage
    s.checkStatus()  # still in loading stage
    s.checkStatus()  # OK
    s.close()
    s.checkStatus()
    # Test more here


if __name__ == "__main__":
    main()
