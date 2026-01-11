import gui.ui as ui
import backend.functions as backend
import backend.library as library
import backend.config as config
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette,QColor, QFont


def set_dark_mode(app):
    app.setStyle("Fusion")

    dark_palette = QPalette()
    dark_color = QColor(18, 18, 18)
    text_color = QColor(240, 240, 240)
    disabled_text_color = QColor(127, 127, 127)


    dark_palette.setColor(QPalette.ColorRole.Window, dark_color)
    dark_palette.setColor(QPalette.ColorRole.WindowText, text_color)
    dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, text_color)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
    dark_palette.setColor(QPalette.ColorRole.Text, text_color)

    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_text_color)

    dark_palette.setColor(QPalette.ColorRole.Button, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))

    app.setPalette(dark_palette)

def main():
    backendInstance = backend.Backend()
    configInstance = config.Config()
    libraryInstance = library.Library(filepath=configInstance.get("download_settings",{}).get("download_path","./Music"))
    app = QApplication(sys.argv)
    app.setFont(QFont("JetBrainsMonoNL NF", 10, QFont.Weight.Normal))
    set_dark_mode(app)
    window = ui.MainWindow(backend=backendInstance,library=libraryInstance,config=configInstance)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()