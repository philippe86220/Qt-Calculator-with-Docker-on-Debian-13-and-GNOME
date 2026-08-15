#!/usr/bin/env python3
"""Calculatrice graphique simple avec PySide6 (Qt for Python)."""

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGridLayout,
    QLineEdit, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt


class Calculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calculatrice Qt")
        self.setFixedSize(320, 420)

        self.expression = ""
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()

        # Écran d'affichage
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setStyleSheet("font-size: 28px; padding: 12px;")
        self.display.setFixedHeight(60)
        main_layout.addWidget(self.display)

        # Grille de boutons
        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = [
            ("C", 0, 0), ("(", 0, 1), (")", 0, 2), ("/", 0, 3),
            ("7", 1, 0), ("8", 1, 1), ("9", 1, 2), ("*", 1, 3),
            ("4", 2, 0), ("5", 2, 1), ("6", 2, 2), ("-", 2, 3),
            ("1", 3, 0), ("2", 3, 1), ("3", 3, 2), ("+", 3, 3),
            ("0", 4, 0), (".", 4, 1), ("⌫", 4, 2), ("=", 4, 3),
        ]

        for label, row, col in buttons:
            btn = QPushButton(label)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setStyleSheet("font-size: 20px; padding: 14px;")
            btn.clicked.connect(lambda checked=False, l=label: self._on_click(l))
            grid.addWidget(btn, row, col)

        main_layout.addLayout(grid)
        self.setLayout(main_layout)

    def _on_click(self, label):
        if label == "C":
            self.expression = ""
        elif label == "⌫":
            self.expression = self.expression[:-1]
        elif label == "=":
            try:
                # eval restreint : uniquement chiffres et opérateurs autorisés
                allowed = set("0123456789+-*/(). ")
                if not set(self.expression) <= allowed:
                    raise ValueError("Caractère non autorisé")
                result = eval(self.expression, {"__builtins__": {}}, {})
                self.expression = str(result)
            except Exception:
                self.expression = "Erreur"
        else:
            if self.expression == "Erreur":
                self.expression = ""
            self.expression += label

        self.display.setText(self.expression)


def main():
    app = QApplication(sys.argv)
    window = Calculator()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

