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

class BinViewMainWindow(QtWidgets.QMainWindow):
	pass

class BinViewViewerApp(QtWidgets.QApplication):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		viewitems.TRTNumericViewItem.STRING_PADDING=5

		self._threadpool = QtCore.QThreadPool()
		
		self._binviewviewcolumns_viewmodel = viewmodels.TRTTimelineViewModel()
		self._binviewproperties_viewmodel = viewmodels.TRTTimelineViewModel()
		self._binviewdescriptors_viewmodel = viewmodels.TRTTimelineViewModel()

		self._wnd_main = BinViewMainWindow()
		self._wnd_main.setCentralWidget(QtWidgets.QWidget())
		self._wnd_main.centralWidget().setLayout(QtWidgets.QVBoxLayout())
		self._wnd_main.resize(525, 800)

		self._lbl_binview = QtWidgets.QLabel()
		self._wnd_main.centralWidget().layout().addWidget(self._lbl_binview)

		self._splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

		self._splitter.addWidget(QtWidgets.QGroupBox())
		self._splitter.addWidget(QtWidgets.QGroupBox())
		self._splitter.addWidget(QtWidgets.QGroupBox())


		self._tree_binview_properties = QtWidgets.QTreeView()
		self._tree_binview_properties.setIndentation(0)
		self._tree_binview_properties.setAlternatingRowColors(True)
		self._tree_binview_properties.setUniformRowHeights(True)
		self._tree_binview_properties.setSortingEnabled(True)
		self._tree_binview_properties.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_properties.model().setSourceModel(self._binviewproperties_viewmodel)

		self._tree_binview_columns = QtWidgets.QTreeView()
		self._tree_binview_columns.setIndentation(0)
		self._tree_binview_columns.setAlternatingRowColors(True)
		self._tree_binview_columns.setUniformRowHeights(True)
		self._tree_binview_columns.setSortingEnabled(True)
		self._tree_binview_columns.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_columns.model().setSourceModel(self._binviewviewcolumns_viewmodel)

		self._tree_binview_descriptors = QtWidgets.QTreeView()
		self._tree_binview_descriptors.setIndentation(0)
		self._tree_binview_descriptors.setAlternatingRowColors(True)
		self._tree_binview_descriptors.setUniformRowHeights(True)
		self._tree_binview_descriptors.setSortingEnabled(True)
		self._tree_binview_descriptors.setModel(QtCore.QSortFilterProxyModel())
		self._tree_binview_descriptors.model().setSourceModel(self._binviewdescriptors_viewmodel)
		
		font = QtGui.QFont()
		font.setPointSizeF(font.pointSizeF() * .8)
		self._tree_binview_properties.setFont(font)
		self._tree_binview_columns.setFont(font)
		self._tree_binview_descriptors.setFont(font)


		wdg_propdata = self._splitter.widget(0)
		wdg_propdata.setLayout(QtWidgets.QVBoxLayout())
		#wdg_propdata.layout().setContentsMargins(0,5,0,5)
		wdg_propdata.layout().addWidget(QtWidgets.QLabel("Property Data"))
		wdg_propdata.layout().addWidget(self._tree_binview_properties)
		
		wdg_coldefs = self._splitter.widget(1)
		wdg_coldefs.setLayout(QtWidgets.QVBoxLayout())
		#wdg_coldefs.layout().setContentsMargins(0,5,0,5)
		wdg_coldefs.layout().addWidget(QtWidgets.QLabel("Column Definitions"))
		wdg_coldefs.layout().addWidget(self._tree_binview_columns)

		wdg_coldescs = self._splitter.widget(2)
		wdg_coldescs.setLayout(QtWidgets.QVBoxLayout())
		#wdg_coldescs.layout().setContentsMargins(0,5,0,5)
		wdg_coldescs.layout().addWidget(QtWidgets.QLabel("Column Format Descriptors"))
		wdg_coldescs.layout().addWidget(self._tree_binview_descriptors)

		self._wnd_main.centralWidget().layout().addWidget(self._splitter)

		self._wnd_main.show()
	
	@QtCore.Slot(object)
	def loadBin(self, bin_path:os.PathLike):
		self._wnd_main.setWindowFilePath(bin_path)
		self._loader = BinViewLoader(bin_path)

		self._loader.signals().sig_begin_loading.connect(self._binviewviewcolumns_viewmodel.clear)
		self._loader.signals().sig_begin_loading.connect(self._binviewproperties_viewmodel.clear)
		
		self._loader.signals().sig_complete.connect(self.setBinViewProperties)
		self._loader.signals().sig_complete.connect(self.setBinViewColumns)
		self._loader.signals().sig_complete.connect(self.setBinViewFormatDescriptors)
		self._loader.signals().sig_complete.connect(self.setBinViewName)
		
		self._threadpool.start(self._loader)

	@QtCore.Slot(object)
	def setBinViewProperties(self, binview_datamodel:avb.bin.BinViewSetting):

		self._binviewproperties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="value", display_name="Value", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DialogInformation)))
		self._binviewproperties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="name", display_name="Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binviewproperties_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="order", display_name="Order", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))

		for idx, (k,v) in enumerate(binview_datamodel.property_data.items()):
			self._binviewproperties_viewmodel.addTimeline({
				"name": viewitems.TRTStringViewItem(k),
				"value": viewitems.TRTStringViewItem(v),
				"order": viewitems.TRTNumericViewItem(idx),
			})
		
		for col in range(self._tree_binview_properties.header().count()):
			self._tree_binview_properties.resizeColumnToContents(col)

		self._tree_binview_properties.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)

	@QtCore.Slot(object)
	def setBinViewFormatDescriptors(self, binview_datamodel:avb.bin.BinViewSetting):

		self._binviewdescriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="type", display_name="Type", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties)))
		self._binviewdescriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="value", display_name="Value", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DialogInformation)))
		self._binviewdescriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="name", display_name="Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binviewdescriptors_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="column_id", display_name="Column ID", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))

		import json

		for format_descriptor in binview_datamodel.format_descriptors:
			column_id = format_descriptor["vcid_free_column_id"]
			properties = json.loads(format_descriptor["format_descriptor"])
	
			for property in properties["properties"]:
				self._binviewdescriptors_viewmodel.addTimeline({
					"column_id": viewitems.TRTNumericViewItem(column_id),
					"name": viewitems.TRTStringViewItem(property["name"]),
					"value": viewitems.TRTStringViewItem(property["value"]),
					"type": viewitems.TRTStringViewItem(property["type"]),
				})
		
		for col in range(self._tree_binview_descriptors.header().count()):
			self._tree_binview_descriptors.resizeColumnToContents(col)

		self._tree_binview_descriptors.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)


	
	@QtCore.Slot(object)
	def setBinViewColumns(self, binview_datamodel:avb.bin.BinViewSetting):

		

		self._binviewviewcolumns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("hidden", "Hidden", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.EditFind)))
		self._binviewviewcolumns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("type", "Type", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties)))
		self._binviewviewcolumns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("format", "Format", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatTextItalic)))
		self._binviewviewcolumns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("title", "Name", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binviewviewcolumns_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("order", "Order", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))
		
		for idx, column in enumerate(binview_datamodel.property_data["columns"]):
			self._binviewviewcolumns_viewmodel.addTimeline({
				"order": viewitems.TRTNumericViewItem(idx),
				"title": viewitems.TRTStringViewItem(column.get("title")),
				"format": viewitems.TRTEnumViewItem(avbutils.BinColumnFormat(column["format"])),
				"type": viewitems.TRTNumericViewItem(column["type"]),
				"hidden": viewitems.TRTStringViewItem(column["hidden"]),
			})

		for col in range(self._tree_binview_columns.header().count()):
			self._tree_binview_columns.resizeColumnToContents(col)
		
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