import gui.ui as ui
import backend.functions as backend
import backend.library as library
import backend.config as config
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette,QColor, QFont


def set_dark_mode(app):
    dark_palette = QPalette()
    dark_color = QColor(18, 18, 18)
    disabled_color = QColor(127, 127, 127)

    dark_palette.setColor(QPalette.Window, dark_color)
    dark_palette.setColor(QPalette.WindowText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, dark_color)
    dark_palette.setColor(QPalette.ToolTipBase, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.ToolTipText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Text, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
    dark_palette.setColor(QPalette.Button, QColor(30, 30, 30))
    dark_palette.setColor(QPalette.ButtonText, QColor(240, 240, 240))
    dark_palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, QColor(0, 0, 0))

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
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()