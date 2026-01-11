import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QPalette, QColor, QAction
from PyQt6.QtWidgets import (
    QMainWindow, QListWidget, QDockWidget, QTreeView, QListWidgetItem,
    QPushButton, QWidget, QVBoxLayout, QDialog, QLabel, QLineEdit,
    QMessageBox, QHBoxLayout, QToolBar, QApplication
)


class AddPlaylistDialog(QDialog):
    def __init__(self, prompt="Enter text:"):
        super().__init__()
        self.setWindowTitle("Add Playlist From Url")
        self.resize(300, 100)

        self.value = None  # Will store the input

        layout = QVBoxLayout()

        # Prompt label
        self.label = QLabel(prompt)
        layout.addWidget(self.label)

        # Entry field
        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit)

        # OK button
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept_input)
        layout.addWidget(self.ok_button)

        self.setLayout(layout)

    def accept_input(self):
        self.value = self.line_edit.text()  # Save input
        self.accept()  # Close dialog with QDialog.Accepted


class MainWindow(QMainWindow):
    def __init__(self, backend=None, library=None, config=None):
        super().__init__()
        if backend is None:
            raise ValueError("No backend given!")
        if library is None:
            raise ValueError("No library given!")
        if config is None:
            raise ValueError("No configuration given!")

        self.backendInstance = backend
        self.libraryInstance = library
        self.configInstance = config

        self.currentSelectedPlaylist = None

        self.setWindowTitle("Playlist Sync")
        # Ensure the path exists or handle the error if the icon is missing
        self.setWindowIcon(QIcon(QPixmap("gui/static/program_icon.png")))
        self.resize(900, 600)

        self.toolbar = QToolBar("Main Toolbar")  # Renamed for standard practice
        self.addToolBar(self.toolbar)

        # QAction is now imported from QtGui in PyQt6
        self.add_playlist_button = QAction("Add playlist", self)
        self.add_playlist_button.setStatusTip("This opens the wizard for a new playlist")
        self.add_playlist_button.triggered.connect(self._add_playlist)
        self.toolbar.addAction(self.add_playlist_button)

        self.add_queue_button = QAction("New queue", self)
        self.add_queue_button.setStatusTip("This opens a wizard for adding a new user queue")
        ##self.add_queue_button.triggered.connect(self._add_playlist)
        self.toolbar.addAction(self.add_queue_button)

        self.show_status = QAction("Show status", self)
        self.show_status.setStatusTip("This opens the current status of the library")
        ##self.add_queue_button.triggered.connect(self._add_playlist)
        self.toolbar.addAction(self.show_status)

        # Dock 1 — Playlist
        self.playlistSelectorContainer = QWidget(self)
        self.playlistSelectorLayout = QVBoxLayout()

        self.playlistSelectorListWidget = QListWidget()
        self.playlistSelectorListWidget.itemClicked.connect(self.set_selected_playlist)

        self.playlistSelectorLayout.addWidget(self.playlistSelectorListWidget)

        self.playlistSelectorContainer.setLayout(self.playlistSelectorLayout)

        playlist_dock = QDockWidget("Playlists", self)
        playlist_dock.setWidget(self.playlistSelectorContainer)

        # PyQt6 Enum: Qt.DockWidgetArea.AllDockWidgetAreas
        playlist_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)

        # PyQt6 Enum: Qt.DockWidgetArea.LeftDockWidgetArea
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, playlist_dock)
        playlist_dock.setMinimumWidth(100)

        # Dock 2 — Track Tree
        self.trackSelectorContainer = QWidget(self)
        self.trackSelectorLayout = QVBoxLayout()

        self.trackSelectorActionContainer = QWidget(self.trackSelectorContainer)
        # Note: In your original code you overwrote trackSelectorActionLayout immediately after defining it.
        # I preserved the logic, but the first QHBoxLayout definition was redundant.
        self.trackSelectorActionLayout = QHBoxLayout()

        self.syncPlaylistButton = QPushButton("Sync")
        self.syncPlaylistButton.setIcon(QIcon("gui/static/sync_icon.png"))
        self.syncPlaylistButton.clicked.connect(self._sync_playlist)

        self.trackSelectorActionLayout.addWidget(self.syncPlaylistButton)

        self.trackSelectorActionContainer.setLayout(self.trackSelectorActionLayout)
        self.trackSelectorLayout.addWidget(self.trackSelectorActionContainer)

        self.trackSelectorTreeView = QTreeView()
        self.trackSelectorTreeModel = QStandardItemModel()
        self.trackSelectorTreeModel.setColumnCount(7)
        self.trackSelectorTreeModel.setHorizontalHeaderLabels(
            ["Title", "Artist", "Album", "Release", "Length", "Platform", "Library URI"]
        )
        self.trackSelectorTreeView.setModel(self.trackSelectorTreeModel)
        self.trackSelectorTreeView.setSortingEnabled(True)

        # PyQt6 Enum: Qt.SortOrder.AscendingOrder
        self.trackSelectorTreeView.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.trackSelectorLayout.addWidget(self.trackSelectorTreeView)

        self.trackSelectorContainer.setLayout(self.trackSelectorLayout)
        track_list_dock = QDockWidget("Track List", self)
        track_list_dock.setWidget(self.trackSelectorContainer)
        track_list_dock.setAllowedAreas(Qt.DockWidgetArea.AllDockWidgetAreas)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, track_list_dock)

        # 3. Song view

        self.songViewContainer = QWidget()
        self.songViewContainerLayout = QVBoxLayout()
        self.songViewContainer.setLayout(self.songViewContainerLayout)

        self.coverLabel = QLabel("Cover")
        self.songViewContainerLayout.addWidget(self.coverLabel)

        self.titleLabel = QLabel("Title")
        self.songViewContainerLayout.addWidget(self.titleLabel)

        self.artistAlbumLabel = QLabel("Album - Artist")
        self.songViewContainerLayout.addWidget(self.artistAlbumLabel)

        self.yearLabel = QLabel("Year")
        self.songViewContainerLayout.addWidget(self.yearLabel)

        self.showInFolderButton = QPushButton("Show Folder", self)
        self.songViewContainerLayout.addWidget(self.showInFolderButton)

        self.moreInfoButton = QPushButton("More Info", self)
        self.songViewContainerLayout.addWidget(self.moreInfoButton)

        songViewDock = QDockWidget("Song View", self)
        songViewDock.setWidget(self.songViewContainer)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, songViewDock)

        # Arrange horizontally next to each other
        # PyQt6 Enum: Qt.Orientation.Horizontal
        self.splitDockWidget(playlist_dock, track_list_dock, Qt.Orientation.Horizontal)
        self.resizeDocks([playlist_dock, track_list_dock], [250, 680], Qt.Orientation.Horizontal)

        # Load functions
        self._load_playlists()

    def _add_playlist(self):
        dialog = AddPlaylistDialog(prompt="Enter a url")
        # PyQt6 Change: .exec_() is removed, use .exec()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                if dialog.value is not None and dialog.value != "":
                    playlist_uri = self.backendInstance.add_playlist_to_library(str(dialog.value))
                    self.backendInstance.sync_playlist(playlist_uri)
                    self.libraryInstance._load()
                    self._load_playlists()
                    self._load_tracks()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _sync_playlist(self):
        self.backendInstance.sync_playlist(str(self.currentSelectedPlaylist))
        self.libraryInstance._load()
        self._load_tracks()

    def _load_playlists(self):
        self.playlistSelectorListWidget.clear()
        playlists = self.libraryInstance._get("playlists")
        for playlist in playlists:
            playlist_data = self.libraryInstance.get_playlist_full(playlist)
            icon_path = ""
            if playlist.split(":")[0] == "youtube":
                icon_path = "gui/static/ytmusic_icon.png"
            item = QListWidgetItem(QIcon(icon_path), playlist_data["title"])
            # PyQt6 Enum: Qt.ItemDataRole.UserRole
            item.setData(Qt.ItemDataRole.UserRole, playlist)
            self.playlistSelectorListWidget.addItem(item)

    def set_selected_playlist(self, item):
        # PyQt6 Enum: Qt.ItemDataRole.UserRole
        self.currentSelectedPlaylist = str(item.data(Qt.ItemDataRole.UserRole))
        self._load_tracks()

    def _load_tracks(self):
        self.trackSelectorTreeModel.removeRows(0, self.trackSelectorTreeModel.rowCount())
        for track in self.libraryInstance.get_playlist_items_data(self.currentSelectedPlaylist):
            # Helper to reduce repetition of Flag Setting
            def make_item(text):
                item = QStandardItem(str(text))
                # PyQt6 Enum: Qt.ItemFlag.ItemIsEditable
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                return item

            title_item = make_item(track.get("title", ""))
            artist_item = make_item(",".join(track.get("artist", ["Unknown Artist"])))
            album_item = make_item(track.get("album", "Unknown Album"))
            release_item = make_item(track.get("release", ""))
            length_item = make_item(track.get("file_info", {}).get("length", ""))
            platform_item = make_item(track.get("track_id", "").split(":")[0])
            uri_item = make_item(track.get("track_id", ""))

            self.trackSelectorTreeModel.appendRow([
                title_item,
                artist_item,
                album_item,
                release_item,
                length_item,
                platform_item,
                uri_item
            ])