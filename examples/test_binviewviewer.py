import sys, os
import avb, avbutils
from trt_model import viewmodels, viewitems
from PySide6 import QtCore, QtGui, QtWidgets

class BinViewLoader(QtCore.QRunnable):

	class Signals(QtCore.QObject):

		sig_begin_loading = QtCore.Signal()
		sig_complete = QtCore.Signal(object)

	def __init__(self, bin_path:os.PathLike, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._bin_path = bin_path
		self._signals  = self.Signals()
	
	def run(self):
		self._signals.sig_begin_loading.emit()
		self._signals.sig_complete.emit(get_binview(self._bin_path))
	
	def signals(self) -> Signals:
		return self._signals

class BinViewTreeView(QtWidgets.QTreeView):

	def __init__(self, *argv, **kwargv):

		super().__init__(*argv, **kwargv)

		self.setIndentation(0)
		self.setAlternatingRowColors(True)
		self.setUniformRowHeights(True)
		self.setSortingEnabled(True)
		self.setItemsExpandable(False)
		self.setSelectionBehavior(self.SelectionBehavior.SelectRows)
		self.setSelectionMode(self.SelectionMode.ExtendedSelection)
	
	@QtCore.Slot()
	def resizeAllColumnsToContents(self):
		"""Resize all columns to fit contents"""

		for col in range(self.header().count()):
			self.resizeColumnToContents(col)

		#self.setStyleSheet("QTreeView::item { padding: 4px 0px; }")

class BinViewMainWindow(QtWidgets.QMainWindow):
	pass

class UncaptionedGroupBox(QtWidgets.QFrame):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)
		
		self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
		self.setFrameShadow(QtWidgets.QFrame.Shadow.Plain)

class BinViewViewerApp(QtWidgets.QApplication):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		viewitems.TRTNumericViewItem.STRING_PADDING=5

		self._threadpool = QtCore.QThreadPool()
		
		self._binview_columns_viewmodel = viewmodels.TRTTimelineViewModel()
		self._binview_properties_viewmodel = viewmodels.TRTTimelineViewModel()
		self._binview_descriptors_viewmodel = viewmodels.TRTTimelineViewModel()

		self._wnd_main = BinViewMainWindow()
		self._wnd_main.setCentralWidget(QtWidgets.QWidget())
		self._wnd_main.centralWidget().setLayout(QtWidgets.QVBoxLayout())
		self._wnd_main.resize(250, 800)

		self._lbl_binview = QtWidgets.QLabel()
		self._wnd_main.centralWidget().layout().addWidget(self._lbl_binview)

		self._splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

		#wdg_properties.setFrameShape(QtWidgets.Frame)

		self._splitter.addWidget(UncaptionedGroupBox())
		self._splitter.addWidget(UncaptionedGroupBox())
		self._splitter.addWidget(UncaptionedGroupBox())

		self._splitter.setStretchFactor(0,0)
		self._splitter.setStretchFactor(1,1)
		self._splitter.setStretchFactor(2,0)


		self._tree_binview_properties = BinViewTreeView()
		self._tree_binview_properties.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_properties.model().setSourceModel(self._binview_properties_viewmodel)
		font = self._tree_binview_properties.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._tree_binview_properties.setFont(font)

		self._tree_binview_columns = BinViewTreeView()
		self._tree_binview_columns.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_columns.model().setSourceModel(self._binview_columns_viewmodel)
		font = self._tree_binview_columns.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._tree_binview_columns.setFont(font)

		self._tree_binview_descriptors = BinViewTreeView()
		self._tree_binview_descriptors.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_descriptors.model().setSourceModel(self._binview_descriptors_viewmodel)
		font = self._tree_binview_descriptors.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._tree_binview_descriptors.setFont(font)

		margin_size = QtCore.QMargins(5,3, 5,3)

		wdg_propdata = self._splitter.widget(0)
		wdg_propdata.setLayout(QtWidgets.QVBoxLayout())
		wdg_propdata.layout().setContentsMargins(margin_size)
		self._lbl_binview_properties = QtWidgets.QLabel("Property Data")
		font = self._lbl_binview_properties.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._lbl_binview_properties.setFont(font)
		wdg_propdata.layout().addWidget(self._lbl_binview_properties)
		wdg_propdata.layout().addWidget(self._tree_binview_properties)
		
		wdg_coldefs = self._splitter.widget(1)
		wdg_coldefs.setLayout(QtWidgets.QVBoxLayout())
		wdg_coldefs.layout().setContentsMargins(margin_size)
		
		self._lbl_binview_columns = QtWidgets.QLabel("Column Definitions")
		font = self._lbl_binview_columns.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._lbl_binview_columns.setFont(font)
		
		wdg_coldefs.layout().addWidget(self._lbl_binview_columns)
		wdg_coldefs.layout().addWidget(self._tree_binview_columns)

		wdg_coldescs = self._splitter.widget(2)
		wdg_coldescs.setLayout(QtWidgets.QVBoxLayout())
		wdg_coldescs.layout().setContentsMargins(margin_size)
		self._lbl_binview_descriptors = QtWidgets.QLabel("Column Format Descriptors")
		font = self._lbl_binview_descriptors.font()
		font.setPointSizeF(font.pointSizeF() * 0.8)
		self._lbl_binview_descriptors.setFont(font)
		wdg_coldescs.layout().addWidget(self._lbl_binview_descriptors)
		wdg_coldescs.layout().addWidget(self._tree_binview_descriptors)

		self._wnd_main.centralWidget().layout().addWidget(self._splitter)

		self._splitter.setSizes([
			150,
			100,
			100
		])

		self._wnd_main.show()
	
	@QtCore.Slot(object)
	def loadBin(self, bin_path:os.PathLike):
		self._wnd_main.setWindowFilePath(bin_path)
		self._loader = BinViewLoader(bin_path)

		self._loader.signals().sig_begin_loading.connect(self._binview_columns_viewmodel.clear)
		self._loader.signals().sig_begin_loading.connect(self._binview_properties_viewmodel.clear)
		
		self._loader.signals().sig_complete.connect(self.setBinViewProperties)
		self._loader.signals().sig_complete.connect(self.setBinViewColumns)
		self._loader.signals().sig_complete.connect(self.setBinViewFormatDescriptors)
		self._loader.signals().sig_complete.connect(self.setBinViewName)
		
		self._threadpool.start(self._loader)

	@QtCore.Slot(object)
	def setBinViewProperties(self, binview_datamodel:avb.bin.BinViewSetting):

		self._binview_properties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="value", display_name="Value", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DialogInformation)))
		self._binview_properties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="name", display_name="Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binview_properties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="order", display_name="Order", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))

		for idx, (k,v) in enumerate(binview_datamodel.property_data.items()):
			self._binview_properties_viewmodel.addTimeline({
				"name": viewitems.TRTStringViewItem(k),
				"value": viewitems.TRTStringViewItem(v),
				"order": viewitems.TRTNumericViewItem(idx),
			})
		
		self._tree_binview_properties.resizeAllColumnsToContents()
		self._tree_binview_properties.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

	@QtCore.Slot(object)
	def setBinViewFormatDescriptors(self, binview_datamodel:avb.bin.BinViewSetting):

		self._binview_descriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="type", display_name="Type", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties)))
		self._binview_descriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="value", display_name="Value", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DialogInformation)))
		self._binview_descriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="name", display_name="Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binview_descriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="column_id", display_name="Column ID", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))

		import json

		for format_descriptor in binview_datamodel.format_descriptors:
			column_id = format_descriptor["vcid_free_column_id"]
			properties = json.loads(format_descriptor["format_descriptor"])
	
			for property in properties["properties"]:
				self._binview_descriptors_viewmodel.addTimeline({
					"column_id": viewitems.TRTNumericViewItem(column_id),
					"name": viewitems.TRTStringViewItem(property["name"]),
					"value": viewitems.TRTStringViewItem(property["value"]),
					"type": viewitems.TRTStringViewItem(property["type"]),
				})
		
		self._tree_binview_descriptors.resizeAllColumnsToContents()
		self._tree_binview_descriptors.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)


	
	@QtCore.Slot(object)
	def setBinViewColumns(self, binview_datamodel:avb.bin.BinViewSetting):

		

		self._binview_columns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("hidden", "Hidden", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.EditFind)))
		self._binview_columns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("type", "Type", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties)))
		self._binview_columns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("format", "Format", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatTextItalic)))
		self._binview_columns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("title", "Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binview_columns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("order", "Order", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))
		
		for idx, column in enumerate(binview_datamodel.property_data["columns"]):
			self._binview_columns_viewmodel.addTimeline({
				"order": viewitems.TRTNumericViewItem(idx),
				"title": viewitems.TRTStringViewItem(column.get("title")),
				"format": viewitems.TRTEnumViewItem(avbutils.BinColumnFormat(column["format"])),
				"type": viewitems.TRTNumericViewItem(column["type"]),
				"hidden": viewitems.TRTStringViewItem(column["hidden"]),
			})

		self._tree_binview_columns.resizeAllColumnsToContents()
		self._tree_binview_columns.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
		
	@QtCore.Slot(object)
	def setBinViewName(self, binview_datamodel:avb.bin.BinViewSetting):
		self._lbl_binview.setText(binview_datamodel.name)

def get_binview(bin_path:str) -> avb.bin.BinViewSetting:
	"""Get the binview data model"""

	with avb.open(bin_path) as bin_handle:
		view_settings = bin_handle.content.view_setting
		view_settings.property_data = avb.core.AVBPropertyData(view_settings.property_data) # Dereference before closing file
		return view_settings

def main(bin_path:os.PathLike):

	app = BinViewViewerApp()
	app.setStyle("Fusion")
	app.loadBin(bin_path)

	app.exec()







if __name__ == "__main__":

	if len(sys.argv) < 2:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} path/to/avidbin.avb")
	
	main(sys.argv[1])