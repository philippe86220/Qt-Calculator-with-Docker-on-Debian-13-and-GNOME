[Back to the main README](README.md)

# README — `calculator.py` Explained Line by Line

This document provides a detailed explanation of the PySide6 graphical calculator script.

---

## Header and Imports

**Lines 1–2**

```python
#!/usr/bin/env python3
```

* Line 1 is the shebang. It allows the script to be executed directly with `./calculator.py` on Linux, provided that execution permission has been granted. This is useful for testing the calculator directly, without IDLE, before placing it inside a Docker container.

**Line 4**

```python
import sys
```

This imports the standard `sys` module, which is required for:

* `sys.argv`: passes command-line arguments to Qt.
* `sys.exit()`: returns the program’s exit code cleanly to the operating system.

**Lines 5–8**

```python
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QSizePolicy
)
```

This imports the Qt classes used by the application:

* `QApplication`: initializes the Qt application and manages its event loop. Every Qt graphical application must have exactly one `QApplication` instance.
* `QWidget`: the base class for graphical windows and interface components.
* `QVBoxLayout`: arranges widgets vertically, one below another.
* `QGridLayout`: arranges widgets in rows and columns. It is used here for the calculator buttons.
* `QLineEdit`: a single-line text field, used here as the calculator display.
* `QPushButton`: a clickable button.
* `QSizePolicy`: controls how a widget can expand or shrink inside its layout.

**Line 9**

```python
from PySide6.QtCore import Qt
```

This imports Qt’s core constants and enumerations. In this application, it is used for `Qt.AlignRight`, which aligns the display text to the right.

---

## The `Calculator` Class

**Line 12**

```python
class Calculator(QWidget):
```

The `Calculator` class inherits from `QWidget`. This means that the calculator itself is a Qt window and receives the standard Qt behavior for displaying, closing, and managing a graphical widget.

**Lines 13–16**

```python
def __init__(self):
    super().__init__()
    self.setWindowTitle("Calculatrice Qt")
    self.setFixedSize(320, 420)
```

* `super().__init__()` calls the `QWidget` constructor. This is required so that Qt can initialize the object correctly.
* `setWindowTitle(...)` defines the title displayed in the window’s title bar.
* `setFixedSize(320, 420)` fixes the window size at 320 × 420 pixels. The user cannot resize it.

**Lines 18–19**

```python
self.expression = ""
self._build_ui()
```

* `self.expression` is the state variable that stores the expression currently entered and displayed, for example `"12+5"`. It is the logical core of the calculator.
* `_build_ui()` is an internal method, indicated by the `_` prefix, that builds the graphical interface.

---

## The `_build_ui` Method — Building the Interface

**Line 22**

```python
main_layout = QVBoxLayout()
```

This creates the main vertical layout. The calculator display is placed at the top, with the button grid below it.

**Lines 25–30 — The Display**

```python
self.display = QLineEdit()
self.display.setReadOnly(True)
self.display.setAlignment(Qt.AlignRight)
self.display.setStyleSheet("font-size: 28px; padding: 12px;")
self.display.setFixedHeight(60)
main_layout.addWidget(self.display)
```

* `QLineEdit()` creates the text field used as the calculator display.
* `setReadOnly(True)` prevents the user from typing directly into the field. Input must be entered using the calculator buttons.
* `setAlignment(Qt.AlignRight)` aligns the text to the right, as on a physical calculator.
* `setStyleSheet(...)` applies Qt Style Sheet rules, also known as QSS, to define the font size and internal spacing.
* `setFixedHeight(60)` sets the display height to 60 pixels.
* `addWidget(self.display)` adds the display to the main layout.

**Lines 33–34 — The Grid**

```python
grid = QGridLayout()
grid.setSpacing(6)
```

This creates a grid layout with 6 pixels of spacing between the buttons.

**Lines 36–42 — Defining the Buttons**

```python
buttons = [
    ("C", 0, 0), ("(", 0, 1), (")", 0, 2), ("/", 0, 3),
    ...
]
```

This is a list of `(label, row, column)` tuples.

Each tuple defines a button and its position in the grid. This is a declarative approach: the entire calculator keypad layout is described in a single data structure that is easy to read and modify.

**Lines 44–49 — Creating the Buttons Dynamically**

```python
for label, row, col in buttons:
    btn = QPushButton(label)
    btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    btn.setStyleSheet("font-size: 20px; padding: 14px;")
    btn.clicked.connect(lambda checked=False, l=label: self._on_click(l))
    grid.addWidget(btn, row, col)
```

For each tuple in the list:

* `QPushButton(label)` creates a button displaying the corresponding label, such as `"7"` or `"+"`.
* `setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)` allows the button to expand horizontally and vertically to fill the available space.
* `setStyleSheet(...)` defines the visual style of the button.
* `clicked.connect(...)` connects the button’s `clicked` signal to the `_on_click(label)` method. This is Qt’s **signal-and-slot mechanism**.

  * `lambda checked=False, l=label: ...` captures the current value of `label` in the default argument `l=label`.
  * Without this capture, all the buttons would use the last value assigned to `label` by the loop. This is a common Python closure pitfall.
  * `checked=False` receives the Boolean argument automatically provided by Qt’s `clicked` signal. This value is not used by the calculator.
* `grid.addWidget(btn, row, col)` places the button at the specified row and column.

**Lines 51–52**

```python
main_layout.addLayout(grid)
self.setLayout(main_layout)
```

* `addLayout(grid)` inserts the button grid into the main vertical layout, below the display.
* `setLayout(main_layout)` applies the complete layout to the calculator window. Without this step, the interface would not be displayed correctly.

---

## The `_on_click` Method — Calculator Logic

**Line 54**

```python
def _on_click(self, label):
```

This method is called each time a button is clicked. It receives the text of the selected button through the `label` parameter.

**Lines 55–56 — The C Button**

```python
if label == "C":
    self.expression = ""
```

This clears the current expression.

**Lines 57–58 — The Backspace Button**

```python
elif label == "⌫":
    self.expression = self.expression[:-1]
```

The `[:-1]` slice returns the string without its final character. It therefore removes one digit or operator from the current expression.

If the expression is already empty, the result simply remains an empty string.

**Lines 59–68 — The Equals Button**

```python
elif label == "=":
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(self.expression) <= allowed:
            raise ValueError("Caractère non autorisé")
        result = eval(self.expression, {"__builtins__": {}}, {})
        self.expression = str(result)
    except Exception:
        self.expression = "Erreur"
```

* `allowed = set(...)` creates a set containing all the characters accepted in a mathematical expression.
* `set(self.expression) <= allowed` verifies that **every** character in the expression belongs to the allowed set.

  * For Python sets, `<=` means “is a subset of.”
  * This prevents the expression from containing letters, underscores, quotation marks, or other characters normally required to inject Python names, function calls, or strings.
* If an unauthorized character is found, `raise ValueError(...)` deliberately raises an exception.
* `eval(self.expression, {"__builtins__": {}}, {})` evaluates the expression as Python code.

  * The second argument, `{"__builtins__": {}}`, defines the global namespace used during evaluation. Replacing `__builtins__` with an empty dictionary removes direct access to built-in Python functions such as `open()` and `__import__()`.
  * The third argument, `{}`, defines an empty local namespace, so no predefined local variables are available.
* `str(result)` converts the numerical result to a string so that it can be displayed.
* `except Exception` catches errors such as division by zero, invalid syntax, an empty expression, or a rejected character. The calculator displays `"Erreur"` instead of terminating unexpectedly.

The character allowlist and empty evaluation namespaces considerably restrict the expressions accepted by this calculator. However, `eval()` remains a Python code-evaluation function and should not be treated as a general-purpose secure mathematical expression parser for an exposed public service.

In this application, input is additionally limited by the available calculator buttons because the display is read-only.

**Lines 69–72 — Digits and Operators**

```python
else:
    if self.expression == "Erreur":
        self.expression = ""
    self.expression += label
```

* If the display currently contains `"Erreur"`, the expression is cleared before accepting a new character.
* The selected button label is then appended to the end of the current expression.

**Line 74**

```python
self.display.setText(self.expression)
```

This updates the calculator display with the new value of `self.expression`, regardless of which branch was executed above.

It is the only line in `_on_click` that directly updates the graphical display. All the preceding logic only modifies the Python state variable.

---

## The `main` Function — Application Entry Point

**Lines 77–81**

```python
def main():
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    sys.exit(app.exec())
```

* `QApplication(sys.argv)` initializes the Qt application. A graphical Qt program must contain exactly one `QApplication` instance.
* Passing `sys.argv` allows Qt to process any supported command-line options.
* `Calculator()` creates an instance of the window defined by the `Calculator` class.
* `window.show()` makes the window visible. By default, a newly created Qt widget is hidden.
* `app.exec()` starts the Qt **event loop**. The application remains inside this loop, listening for button clicks, window events, and redraw requests until the window is closed.
* `sys.exit(...)` returns Qt’s exit code to the operating system. This can be useful for scripts or continuous integration systems that inspect the program’s return code.

**Lines 84–85**

```python
if __name__ == "__main__":
    main()
```

This is the standard Python entry-point guard.

It ensures that `main()` is called only when the file is executed directly with:

```bash
python calculator.py
```

It is not called automatically if `calculator.py` is imported as a module by another Python program.

---

## Execution Flow Summary

1. `main()` starts, creates the calculator window, and displays it.
2. Each button click calls `_on_click(label)`.
3. `_on_click` modifies the `self.expression` state variable.
4. The final line of `_on_click` synchronizes the graphical display with that variable.
5. Qt remains inside its event loop through `app.exec()` until the user closes the window.
