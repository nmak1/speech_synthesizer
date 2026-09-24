# test_minimal.py
import sys
print("1. Python OK", flush=True)

import torch
print(f"2. Torch OK: {torch.__version__}", flush=True)

from PyQt5.QtWidgets import QApplication, QLabel
print("3. PyQt5 OK", flush=True)

app = QApplication(sys.argv)
print("4. QApplication created", flush=True)

label = QLabel("Hello")
label.show()
print("5. Label shown", flush=True)

from PyQt5.QtCore import QTimer
QTimer.singleShot(2000, app.quit)
sys.exit(app.exec_())