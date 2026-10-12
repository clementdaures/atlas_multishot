# -*- coding: utf-8 -*-
"""Atlas Qt stylesheet

Shared dark purple stylesheet applied to every Atlas Multishot dialog.

Author: Clement Daures
Website: clementdaures.com
Created: 2025
"""

# region Atlas Stylesheet

ATLAS_STYLE = """
QWidget {
    background-color: #303030;
    color: #ddd;
    font-family: Segoe UI;
    font-size: 8pt;
}
QPushButton {
    background-color: #404040;
    border: 1px solid #262626;
    border-radius: 4px;
    padding: 4px 8px;
}
QPushButton:hover {
    background-color: #404040;
    border: 1px solid #7a53cf;
}
QLineEdit, QComboBox, QDoubleSpinBox {
    background-color: #262626;
    border: 1px solid #555;
    border-radius: 3px;
    padding: 2px;
}
QComboBox QAbstractItemView {
    selection-background-color: #7a53cf;
    selection-color: #ffffff;
    background-color: #262626;
}
QComboBox:hover {
    border: 1px solid #7a53cf;
}
QGroupBox {
    border: 1px solid #7a53cf;
    border-radius: 5px;
    margin-top: 6px;
    padding: 4px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QListWidget {
    background-color: #262626;
    color: #ddd;
    border: 1px solid #555;
    border-radius: 3px;
    font-family: Segoe UI;
    font-size: 8pt;
}
QListWidget::item {
    background-color: #404040;
    padding: 4px;
    border-radius: 3px;
    margin: 2px;
    height: 22px;
}
QListWidget::item:hover {
    background-color: #5e3fbf;
    color: #fff;
}
QListWidget::item:selected {
    background-color: #7a53cf;
    color: #fff;
}
"""

# endregion
