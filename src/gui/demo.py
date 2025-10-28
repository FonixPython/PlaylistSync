import sys
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QStandardItemModel,QStandardItem
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QTextEdit,
    QListWidget,
    QTreeView,
    QSplitter,
    QTabWidget,
    QDockWidget,
    QToolBar,
    QStatusBar,
    QMenuBar,
    QMenu,
    QAction,
    QFileDialog,
    QMessageBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QSlider,
    QHBoxLayout,
    QVBoxLayout,
    QStyle,
)

# --------------------------------------------------------------------------- #
#                                 Settings Dialog                               #
# --------------------------------------------------------------------------- #
class SettingsDialog(QDialog):
    """A simple modal dialog that lets the user change a couple of settings."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(300, 120)

        # UI elements
        self.font_label = QLabel("Editor Font Size:")
        self.font_edit = QLineEdit("12")
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Cancel")

        # Layout
        form = QHBoxLayout()
        form.addWidget(self.font_label)
        form.addWidget(self.font_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(form)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)

        # Connections
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def get_font_size(self):
        """Return the integer value entered by the user."""
        try:
            return int(self.font_edit.text())
        except ValueError:
            return 12  # default


# --------------------------------------------------------------------------- #
#                                 Main Window                                 #
# --------------------------------------------------------------------------- #
class DemoMainWindow(QMainWindow):
    """The central application window."""

    # Custom signal to demonstrate a slot that updates the status bar
    text_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt5 Demo App")
        self.resize(900, 600)

        # --- Central widget with splitter ------------------------------------
        central = QWidget()
        self.setCentralWidget(central)

        # Text editor on the left
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type here…")
        self.text_edit.textChanged.connect(self.on_text_changed)

        # Tree view on the right
        self.tree_view = QTreeView()
        self.tree_model = QStandardItemModel()
        self.tree_model.setHorizontalHeaderLabels(['Files'])
        self.populate_tree()
        self.tree_view.setModel(self.tree_model)

        # Put the two widgets in a horizontal splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.text_edit)
        splitter.addWidget(self.tree_view)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        # Add a progress bar at the bottom of the splitter
        progress_bar = QProgressBar()
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)

        # A vertical layout to stack the splitter and the progress bar
        vlayout = QVBoxLayout()
        vlayout.addWidget(splitter)
        vlayout.addWidget(progress_bar)

        central.setLayout(vlayout)

        # --- Dock widgets ----------------------------------------------------
        # Dock widget containing a list of "open files"
        self.dock_list = QListWidget()
        self.dock_list.addItems(["main.py", "utils.py", "config.yaml"])
        dock = QDockWidget("Open Files", self)
        dock.setWidget(self.dock_list)
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)

        # Another dock on the right that contains a slider
        self.dock_slider = QWidget()
        slider = QSlider(Qt.Vertical)
        slider.setRange(10, 30)
        slider.setValue(12)
        slider.valueChanged.connect(self.change_font_size)
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Font Size"))
        layout.addWidget(slider)
        layout.addStretch()
        self.dock_slider.setLayout(layout)

        dock2 = QDockWidget("View Controls", self)
        dock2.setWidget(self.dock_slider)
        self.addDockWidget(Qt.RightDockWidgetArea, dock2)

        # --- Tab widget ------------------------------------------------------
        tabs = QTabWidget()
        tabs.addTab(QTextEdit(), "Editor")
        tabs.addTab(QListWidget(), "File List")
        tabs.addTab(QTreeView(), "Project Tree")

        # Add the tabs to a dock widget
        dock_tabs = QDockWidget("Tabs", self)
        dock_tabs.setWidget(tabs)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock_tabs)

        # --- Menus and toolbars ---------------------------------------------
        self.create_actions()
        self.create_menus()
        self.create_toolbars()

        # --- Status bar ------------------------------------------------------
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Ready")

        # Connect custom signal
        self.text_changed.connect(self.status.showMessage)

        # Demo timer: auto increment progress bar
        self.progress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(lambda: self.update_progress(progress_bar))
        self.timer.start(200)

    # ----------------------------------------------------------------------- #
    #                     Utility / helper functions                           #
    # ----------------------------------------------------------------------- #
    def populate_tree(self):
        """Populate the QTreeView with a dummy file structure."""
        root = self.tree_model.invisibleRootItem()
        for folder in ["src", "tests", "docs"]:
            folder_item = QStandardItem(folder)
            for file in ["main.py", "utils.py", "README.md"]:
                file_item = QStandardItem(file)
                folder_item.appendRow(file_item)
            root.appendRow(folder_item)

    def update_progress(self, bar: QProgressBar):
        """Auto‑increment the progress bar until it reaches 100."""
        self.progress = (self.progress + 5) % 101
        bar.setValue(self.progress)

    def on_text_changed(self):
        """Emit the current cursor position."""
        cursor = self.text_edit.textCursor()
        row = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.text_changed.emit(f"Line {row}, Col {col}")

    def change_font_size(self, value: int):
        """Slot for the slider – changes the editor font size."""
        self.text_edit.setFontPointSize(value)

    def create_actions(self):
        """Create reusable actions for menus and toolbars."""
        icon = self.style().standardIcon

        # File actions
        self.new_act = QAction(icon(QStyle.SP_FileIcon), "&New", self)
        self.new_act.setShortcut("Ctrl+N")
        self.new_act.setStatusTip("Create a new file")
        self.new_act.triggered.connect(self.new_file)

        self.open_act = QAction(icon(QStyle.SP_DialogOpenButton), "&Open...", self)
        self.open_act.setShortcut("Ctrl+O")
        self.open_act.setStatusTip("Open an existing file")
        self.open_act.triggered.connect(self.open_file)

        self.save_act = QAction(icon(QStyle.SP_DialogSaveButton), "&Save", self)
        self.save_act.setShortcut("Ctrl+S")
        self.save_act.setStatusTip("Save the current file")
        self.save_act.triggered.connect(self.save_file)

        self.exit_act = QAction(icon(QStyle.SP_DialogCloseButton), "E&xit", self)
        self.exit_act.setShortcut("Ctrl+Q")
        self.exit_act.setStatusTip("Exit the application")
        self.exit_act.triggered.connect(self.close)

        # Edit actions
        self.undo_act = QAction(icon(QStyle.SP_ArrowBack), "&Undo", self)
        self.undo_act.setShortcut("Ctrl+Z")
        self.undo_act.setStatusTip("Undo the last action")
        self.undo_act.triggered.connect(self.text_edit.undo)

        self.redo_act = QAction(icon(QStyle.SP_ArrowForward), "&Redo", self)
        self.redo_act.setShortcut("Ctrl+Y")
        self.redo_act.setStatusTip("Redo the last undone action")
        self.redo_act.triggered.connect(self.text_edit.redo)

        # View actions
        self.toggle_dock_act = QAction("Show/Hide Open Files", self)
        self.toggle_dock_act.setCheckable(True)
        self.toggle_dock_act.setChecked(True)
        self.toggle_dock_act.toggled.connect(self.toggle_dock_list)

        # Settings
        self.settings_act = QAction(icon(QStyle.SP_FileDialogDetailedView), "Settings", self)
        self.settings_act.setShortcut("Ctrl+G")
        self.settings_act.setStatusTip("Open the settings dialog")
        self.settings_act.triggered.connect(self.open_settings)

        # Help
        self.about_act = QAction("&About", self)
        self.about_act.setStatusTip("Show about dialog")
        self.about_act.triggered.connect(self.show_about)

    def create_menus(self):
        """Build the menu bar."""
        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        # File menu
        file_menu = QMenu("&File", self)
        file_menu.addAction(self.new_act)
        file_menu.addAction(self.open_act)
        file_menu.addAction(self.save_act)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_act)
        menu_bar.addMenu(file_menu)

        # Edit menu
        edit_menu = QMenu("&Edit", self)
        edit_menu.addAction(self.undo_act)
        edit_menu.addAction(self.redo_act)
        menu_bar.addMenu(edit_menu)

        # View menu
        view_menu = QMenu("&View", self)
        view_menu.addAction(self.toggle_dock_act)
        menu_bar.addMenu(view_menu)

        # Help menu
        help_menu = QMenu("&Help", self)
        help_menu.addAction(self.about_act)
        menu_bar.addMenu(help_menu)

    def create_toolbars(self):
        """Add the toolbars to the main window."""
        file_tb = QToolBar("File", self)
        file_tb.setIconSize(Qt.QSize(24, 24))
        file_tb.addAction(self.new_act)
        file_tb.addAction(self.open_act)
        file_tb.addAction(self.save_act)
        self.addToolBar(Qt.TopToolBarArea, file_tb)

        edit_tb = QToolBar("Edit", self)
        edit_tb.addAction(self.undo_act)
        edit_tb.addAction(self.redo_act)
        self.addToolBar(Qt.TopToolBarArea, edit_tb)

    # ----------------------------------------------------------------------- #
    #                     Slots for actions / UI events                         #
    # ----------------------------------------------------------------------- #
    def new_file(self):
        """Clear the editor and show a message."""
        self.text_edit.clear()
        QMessageBox.information(self, "New File", "New file created.")
        self.status.showMessage("New file created.")

    def open_file(self):
        """Open a file dialog and load the selected file into the editor."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "Python Files (*.py);;All Files (*.*)"
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
            self.status.showMessage(f"Opened {path}")

    def save_file(self):
        """Save the contents of the editor to a file."""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save File", "", "Python Files (*.py);;All Files (*.*)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            self.status.showMessage(f"Saved to {path}")

    def on_text_changed(self):
        """Emit a signal with the cursor position whenever the text changes."""
        cursor = self.text_edit.textCursor()
        self.text_changed.emit(f"Line {cursor.blockNumber()+1}, Col {cursor.columnNumber()+1}")

    def change_font_size(self, value: int):
        """Called when the slider in the right dock changes value."""
        self.text_edit.setFontPointSize(value)

    def open_settings(self):
        """Show the modal SettingsDialog."""
        dlg = SettingsDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            size = dlg.get_font_size()
            self.text_edit.setFontPointSize(size)
            self.status.showMessage(f"Font size set to {size}")

    def show_about(self):
        """Show a simple About box."""
        QMessageBox.about(
            self,
            "About PyQt5 Demo",
            "This is a quick demonstration of many PyQt5 widgets.\n\n"
            "Created by ChatGPT.\n"
            "© 2023 OpenAI",
        )

    def change_font_size(self, value: int):
        """Helper that is called from the vertical slider."""
        self.text_edit.setFontPointSize(value)

    # ----------------------------------------------------------------------- #
    #                            UI Setup helpers                               #
    # ----------------------------------------------------------------------- #
    def create_actions(self):
        """Create QActions that can be reused in menus and toolbars."""
        # The actions have already been created in __init__
        pass

    def create_menus(self):
        """Create the menu bar – actually already called in __init__."""
        pass

    def create_toolbars(self):
        """Create the toolbars – already called in __init__."""
        pass


# --------------------------------------------------------------------------- #
#                                 Application entry                            #
# --------------------------------------------------------------------------- #
def main():
    app = QApplication(sys.argv)

    # Use the default application style (helps icons look native)
    app.setStyle('Fusion')

    win = DemoMainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()