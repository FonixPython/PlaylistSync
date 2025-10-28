import gui.ui as ui
import backend.functions as backend
import backend.library as library
import backend.config as config
import sys
from PyQt5.QtWidgets import QApplication

def main():
    backendInstance = backend.Backend()
    configInstance = config.Config()
    libraryInstance = library.Library(filepath=configInstance.get("download_settings",{}).get("download_path","./Music"))
    app = QApplication(sys.argv)
    window = ui.MainWindow(backend=backendInstance,library=libraryInstance,config=configInstance)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()