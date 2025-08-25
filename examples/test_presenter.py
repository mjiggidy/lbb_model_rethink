import sys, os
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets
from trt_model import presenters, viewitems

class BinDisplayOptionsView(QtWidgets.QWidget):

	sig_option_toggled  = QtCore.Signal(object, bool)
	sig_options_changed = QtCore.Signal(object)

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setSpacing(0)
		self.layout().setContentsMargins(0,0,0,0)

		self._option_mappings:dict[avbutils.BinDisplayOptions, QtWidgets.QCheckBox] = dict()

		for option in avbutils.BinDisplayOptions:

			chk_option = QtWidgets.QCheckBox(text=option.name.replace("_"," ").title())
			chk_option.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
			self._option_mappings[option] = chk_option
			self.layout().addWidget(chk_option)
		self.layout().addStretch()
		
	@QtCore.Slot(QtCore.Qt.CheckState)
	def what(self, state:QtCore.Qt.CheckState):
		print(state)
	
	@QtCore.Slot(object)
	def _optionToggled(self, option:avbutils.BinDisplayOptions):
		print(option)
	
	def setOptions(self, options:avbutils.BinDisplayOptions):
		"""Set all options from a given `avbutils.BinDisplayOptions` enum"""

		for option in self._option_mappings:
			self.setOption(option, option in options)
	
	def setOption(self, option:avbutils.BinDisplayOptions, is_enabled:bool):
		"""Toggle a single option"""

		if not len(option) == 1:
			raise ValueError("Only one option is allowed.  Use setOptions() for multiple flags.")

		self._option_mappings[option].setChecked(is_enabled)


class BinTreeView(QtWidgets.QTreeView):
	"""QTreeView but nicer"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.setSortingEnabled(True)
		self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setUniformRowHeights(True)
		
		self.setModel(QtCore.QSortFilterProxyModel())
		self.model().setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)
	
	@QtCore.Slot()
	def resizeAllColumnsToContents(self):
		for idx in range(self.header().count()):
			self.resizeColumnToContents(idx)


class BinViewColumDefinitionsPresenter(presenters.LBItemDefinitionView):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):
		self.viewModel().clear()

		headers = [
			viewitems.TRTAbstractViewHeaderItem("order", "Order"),
			viewitems.TRTAbstractViewHeaderItem("title", "Title"),
			viewitems.TRTAbstractViewHeaderItem("format", "Format"),
			viewitems.TRTAbstractViewHeaderItem("type", "Type"),
			viewitems.TRTAbstractViewHeaderItem("hidden", "Is Hidden"),
		]
		
		for header in headers[::-1]:
			super().addHeader(header)

		for idx, column in enumerate(bin_view.columns):
			column.update({"order": idx})
			self.addColumnDefinition(column)

	@QtCore.Slot(object)
	def addColumnDefinition(self, column_definition:dict[str,object]):

		column_definition["format"] = avbutils.BinColumnFormat(column_definition["format"])

		self.addRow(column_definition)

class BinViewPropertyDataPresenter(presenters.LBItemDefinitionView):

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):

		self.viewModel().clear()

		headers = [
			viewitems.TRTAbstractViewHeaderItem("name", "Name"),
			viewitems.TRTAbstractViewHeaderItem("value", "Value"),
		]
		
		for header in headers[::-1]:
			self.addHeader(header)
		
		for key,val in bin_view.property_data.items():
			self.addRow({"name": key, "value": val})

class BinContentsPresenter(presenters.LBItemDefinitionView):

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):

		self.viewModel().clear()

		for column in bin_view.columns[::-1]:

			if column["hidden"]:
				continue

			self.addHeader(
				viewitems.TRTAbstractViewHeaderItem(
					field_name="40_"+column["title"] if column["type"] == 40 else str(column["type"]),
					display_name=column["title"]
				)
			)
	
	@QtCore.Slot(object)
	def addMob(self, mob_info:dict):
		
		#timecode_range = avbutils.get_timecode_range_for_composition(mob)
		

		#if "attributes" in mob.property_data and "_USER" in mob.attributes:
		#	item.update(mob.attributes.get("_USER"))
		self.addRow(mob_info)



class BinViewLoader(QtCore.QRunnable):
	"""Load a given bin"""

	class Signals(QtCore.QObject):

		sig_begin_loading = QtCore.Signal()
		sig_got_display_options = QtCore.Signal(object)
		sig_got_view_settings = QtCore.Signal(object)
		sig_got_mob = QtCore.Signal(object)
		sig_done_loading = QtCore.Signal()

	def __init__(self, bin_path:os.PathLike, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._bin_path = bin_path
		self._signals  = self.Signals()
	
	def run(self):
		self._signals.sig_begin_loading.emit()

		with avb.open(self._bin_path) as bin_handle:
			self._loadBinDisplayOptions(bin_handle)
			self._loadBinView(bin_handle.content.view_setting)
			self._loadCompositionMobs([i.mob for i in bin_handle.content.items if i.user_placed])
		
		self._signals.sig_done_loading.emit()

	def _loadBinDisplayOptions(self, bin_handle:avb.bin):
		self._signals.sig_got_display_options.emit(avbutils.BinDisplayOptions.get_options_from_bin(bin_handle.content))
	
	def _loadBinView(self, bin_view:avb.bin.BinViewSetting):
		bin_view.property_data = avb.core.AVBPropertyData(bin_view.property_data) # Dereference before closing file
		self._signals.sig_got_view_settings.emit(bin_view)

	def _loadCompositionMobs(self, compositions:avb.trackgroups.Composition):
			
			for comp in compositions:
				if avbutils.composition_is_toplevel(comp):
					timecode_range = avbutils.get_timecode_range_for_composition(comp)
					tape_name = None
				else:
					try:
						import timecode
						source_mob = avbutils.matchback_to_sourcemob(comp)
						tape_name = source_mob.name
						source_mob_timecode_range = avbutils.get_timecode_range_for_composition(source_mob)
						timecode_range = timecode.TimecodeRange(start=source_mob_timecode_range.start, duration=comp.length)
					except Exception as e:
						print(type(e))
						tape_name=None
						timecode_range = None

				markers = avbutils.get_markers_from_timeline(comp)

				item = {
					avbutils.BIN_COLUMN_ROLES["Name"]: comp.name,
					avbutils.BIN_COLUMN_ROLES["Color"]: viewitems.TRTClipColorViewItem(avbutils.composition_clip_color(comp)) if avbutils.composition_clip_color(comp) else "",
					avbutils.BIN_COLUMN_ROLES["Start"]: timecode_range.start if timecode_range else None,
					avbutils.BIN_COLUMN_ROLES["End"]: timecode_range.end if timecode_range else None,
					avbutils.BIN_COLUMN_ROLES["Duration"]: viewitems.TRTDurationViewItem(timecode_range.duration) if timecode_range else None,
					avbutils.BIN_COLUMN_ROLES["Modified Date"]: comp.last_modified,
					avbutils.BIN_COLUMN_ROLES["Creation Date"]: comp.creation_time,
					avbutils.BIN_COLUMN_ROLES[""]: avbutils.MobUsage(comp.usage_code),
					avbutils.BIN_COLUMN_ROLES["Marker"]: viewitems.TRTMarkerViewItem(markers[0]) if markers else None,
					avbutils.BIN_COLUMN_ROLES["Tracks"]: avbutils.format_track_labels(list(avbutils.get_tracks_from_composition(comp))),
					avbutils.BIN_COLUMN_ROLES["Tape"]: tape_name,
				}

				for key, val in comp.attributes.get("_USER","{}").items():
					item.update({"40_"+key: val})
				
				self._signals.sig_got_mob.emit(item)

	
	def signals(self) -> Signals:
		return self._signals

class MainApplication(QtWidgets.QApplication):

	#sig_load_bin_data = QtCore.Signal(object)

	def __init__(self):

		super().__init__()

		self._threadpool = QtCore.QThreadPool()

		self._prog_loading = QtWidgets.QProgressBar()
		self._prog_loading.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
		self._prog_loading.setRange(0,0)
		self._prog_loading.setWindowTitle("Loading bin...")

		self._col_defs_presenter = BinViewColumDefinitionsPresenter()
		self._prop_data_presenter = BinViewPropertyDataPresenter()
		self._contents_presenter = BinContentsPresenter()

		self._btn_open = QtWidgets.QPushButton("Choose Bin...")
		self._btn_open.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FolderOpen))
		self._btn_open.clicked.connect(self.browseForBin)

		self._view_bindisplayoptions = BinDisplayOptionsView()
				
		self._tree_column_defs = BinTreeView()
		self._tree_column_defs.model().setSourceModel(self._col_defs_presenter.viewModel())

		self._tree_property_data = BinTreeView()
		self._tree_property_data.model().setSourceModel(self._prop_data_presenter.viewModel())

		self._tree_bin_contents = BinTreeView()
		self._tree_bin_contents.model().setSourceModel(self._contents_presenter.viewModel())


		self._wnd_main = QtWidgets.QMainWindow()
		self._wnd_main.resize(1024, 600)
		self._wnd_main.setCentralWidget(self._tree_bin_contents)


		dock_font = QtWidgets.QDockWidget().font()
		dock_font.setPointSizeF(dock_font.pointSizeF() * 0.8)

		dock_displayoptions = QtWidgets.QDockWidget("Bin Display Options")
		dock_displayoptions.setFont(dock_font)
		dock_displayoptions.setWidget(self._view_bindisplayoptions)

		dock_propdefs = QtWidgets.QDockWidget("Property Data")
		dock_propdefs.setFont(dock_font)
		dock_propdefs.setWidget(self._tree_property_data)


		dock_coldefs = QtWidgets.QDockWidget("Column Definitions")
		dock_coldefs.setFont(dock_font)
		dock_coldefs.setWidget(self._tree_column_defs)


		dock_btn_open = QtWidgets.QDockWidget("Options")
		dock_btn_open.setWidget(self._btn_open)


		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_propdefs)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_coldefs)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_displayoptions)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_btn_open)

		self._wnd_main.show()

	def loadBin(self, bin_path:str):
		"""Load the bin in another thread"""


		print(bin_path)
		self._worker = BinViewLoader(bin_path)
		self._worker.signals().sig_begin_loading.connect(lambda: self._wnd_main.setWindowFilePath(bin_path))
		self._worker.signals().sig_begin_loading.connect(lambda: self._wnd_main.setWindowFilePath(bin_path))
		self._worker.signals().sig_begin_loading.connect(self._prog_loading.show)

		self._worker.signals().sig_got_display_options.connect(self._view_bindisplayoptions.setOptions)
		
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_column_defs.setWindowTitle(f"{binview.name} | Column Definitions"))
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_property_data.setWindowTitle(f"{binview.name} | Property Data"))
		
		self._worker.signals().sig_got_view_settings.connect(self._col_defs_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._prop_data_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._contents_presenter.setBinView)

		self._worker.signals().sig_got_mob.connect(self._contents_presenter.addMob)

		self._worker.signals().sig_done_loading.connect(self._tree_bin_contents.resizeAllColumnsToContents)
		self._worker.signals().sig_done_loading.connect(self._tree_column_defs.resizeAllColumnsToContents)
		self._worker.signals().sig_done_loading.connect(self._tree_property_data.resizeAllColumnsToContents)

		self._worker.signals().sig_done_loading.connect(lambda: self._tree_bin_contents.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder))
		self._worker.signals().sig_done_loading.connect(lambda: self._tree_column_defs.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder))
		self._worker.signals().sig_done_loading.connect(lambda: self._tree_property_data.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder))

		self._worker.signals().sig_done_loading.connect(self._prog_loading.hide)
		self._threadpool.start(self._worker)
	
	@QtCore.Slot()
	def browseForBin(self):

		file_path, _  = QtWidgets.QFileDialog.getOpenFileName(self._btn_open, "Choose an Avid bin...", filter="Avid Bin (*.avb);;All Files (*)", dir=self._wnd_main.windowFilePath())
		if not file_path:
			return
		self.loadBin(file_path)

if __name__ == "__main__":

	if len(sys.argv) < 2:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} path/to/avidbin.avb")
	
	app = MainApplication()
	app.setStyle("Fusion")
	app.loadBin(sys.argv[1])
	sys.exit(app.exec())