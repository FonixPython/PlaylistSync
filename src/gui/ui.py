import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon, QPixmap, QPalette,QColor
from PyQt5.QtWidgets import QMainWindow, QListWidget, QDockWidget, QTreeView, QListWidgetItem, QPushButton, QWidget, QVBoxLayout, QDialog, QLabel, QLineEdit, QMessageBox, QHBoxLayout, QToolBar,QAction

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


class       MainWindow(QMainWindow):
    def __init__(self,backend = None,library = None,config = None):
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
        self.setWindowIcon(QIcon(QPixmap("gui/static/program_icon.png")))
        self.resize(900, 600)

        self.toolbar = QToolBar("Fuck you")
        self.addToolBar(self.toolbar)

        self.add_playlist_button = QAction("Add playlist",self)
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
        playlist_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.LeftDockWidgetArea, playlist_dock)
        playlist_dock.setMinimumWidth(100)


        # Dock 2 — Track Tree
        self.trackSelectorContainer = QWidget(self)
        self.trackSelectorLayout = QVBoxLayout()

        self.trackSelectorActionContainer = QWidget(self.trackSelectorContainer)
        self.trackSelectorActionLayout = QHBoxLayout()

        self.syncPlaylistButton = QPushButton("Sync")
        self.syncPlaylistButton.setIcon(QIcon("gui/static/sync_icon.png"))
        self.syncPlaylistButton.clicked.connect(self._sync_playlist)
        self.trackSelectorActionLayout = QHBoxLayout()
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
        self.trackSelectorTreeView.sortByColumn(0,Qt.AscendingOrder)
        self.trackSelectorLayout.addWidget(self.trackSelectorTreeView)
        
        self.trackSelectorContainer.setLayout(self.trackSelectorLayout)
        track_list_dock = QDockWidget("Track List", self)
        track_list_dock.setWidget(self.trackSelectorContainer)
        track_list_dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.addDockWidget(Qt.LeftDockWidgetArea, track_list_dock)

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

        self.addDockWidget(Qt.LeftDockWidgetArea, songViewDock)

        # Arrange horizontally next to each other
        self.splitDockWidget(playlist_dock, track_list_dock, Qt.Horizontal)
        self.resizeDocks([playlist_dock, track_list_dock], [250, 680], Qt.Horizontal)

        # Load functions
        self._load_playlists()

    def _add_playlist(self):
        dialog = AddPlaylistDialog(prompt="Enter a url")
        if dialog.exec_() == QDialog.Accepted:
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
            item = QListWidgetItem(QIcon(icon_path),playlist_data["title"])
            item.setData(Qt.UserRole, playlist)
            self.playlistSelectorListWidget.addItem(item)

    def set_selected_playlist(self,item):
        self.currentSelectedPlaylist = str(item.data(Qt.UserRole))
        self._load_tracks()

    def _load_tracks(self):
        self.trackSelectorTreeModel.removeRows(0, self.trackSelectorTreeModel.rowCount())
        for track in self.libraryInstance.get_playlist_items_data(self.currentSelectedPlaylist):
            title_item = QStandardItem(str(track.get("title", "")))
            title_item.setFlags(title_item.flags() & ~Qt.ItemIsEditable)
            artist_item = QStandardItem(",".join(track.get("artist", ["Unknown Artist"])))
            artist_item.setFlags(artist_item.flags() & ~Qt.ItemIsEditable)
            album_item = QStandardItem(str(track.get("album", "Unknown Album")))
            album_item.setFlags(album_item.flags() & ~Qt.ItemIsEditable)
            release_item = QStandardItem(str(track.get("release", "")))
            release_item.setFlags(release_item.flags() & ~Qt.ItemIsEditable)
            length_item = QStandardItem(str(track.get("file_info", {}).get("length", "")))
            length_item.setFlags(length_item.flags() & ~Qt.ItemIsEditable)
            platform_item = QStandardItem(str(track.get("track_id", "").split(":")[0]))
            platform_item.setFlags(platform_item.flags() & ~Qt.ItemIsEditable)
            uri_item = QStandardItem(str(track.get("track_id", "")))
            uri_item.setFlags(uri_item.flags() & ~Qt.ItemIsEditable)
            
            self.trackSelectorTreeModel.appendRow([
                title_item,
                artist_item,
                album_item,
                release_item,
                length_item,
                platform_item,
                uri_item
            ])
