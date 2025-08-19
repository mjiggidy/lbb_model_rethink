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

		self._threadpool = QtCore.QThreadPool()
		
		self._binview_viewmodel = viewmodels.TRTTimelineViewModel()

		self._wnd_main = BinViewMainWindow()
		self._wnd_main.setCentralWidget(QtWidgets.QWidget())
		self._wnd_main.centralWidget().setLayout(QtWidgets.QVBoxLayout())
		self._wnd_main.resize(525, 800)

		self._lbl_binview = QtWidgets.QLabel()
		self._wnd_main.centralWidget().layout().addWidget(self._lbl_binview)

		self._tree_binview = QtWidgets.QTreeView()
		self._tree_binview.setIndentation(0)
		self._tree_binview.setAlternatingRowColors(True)
		self._tree_binview.setUniformRowHeights(True)
		self._tree_binview.setSortingEnabled(True)
		self._tree_binview.setModel(QtCore.QSortFilterProxyModel())
		
		font = QtGui.QFont()
		font.setPointSizeF(font.pointSizeF() * .8)
		self._tree_binview.setFont(font)
		
		self._tree_binview.model().setSourceModel(self._binview_viewmodel)

		self._wnd_main.centralWidget().layout().addWidget(self._tree_binview)

		self._wnd_main.show()
	
	@QtCore.Slot(object)
	def loadBin(self, bin_path:os.PathLike):
		self._wnd_main.setWindowFilePath(bin_path)
		self._loader = BinViewLoader(bin_path)
		self._loader.signals().sig_complete.connect(self.binLoaded)
		self._threadpool.start(self._loader)
	
	@QtCore.Slot(object)
	def binLoaded(self, binview_datamodel:avb.bin.BinViewSetting):

		viewitems.TRTNumericViewItem.STRING_PADDING=5

		self._binview_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("hidden", "Hidden", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.EditFind)))
		self._binview_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("type", "Type", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties)))
		self._binview_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("format", "Format", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatTextItalic)))
		self._binview_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("title", "Title", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatIndentMore)))
		self._binview_viewmodel.addHeader(viewitems.TRTAbstractViewHeaderItem("order", "Order", icon=QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd)))
		
		for idx, column in enumerate(binview_datamodel.columns):
			self._binview_viewmodel.addTimeline({
				"order": viewitems.TRTNumericViewItem(idx),
				"title": viewitems.TRTStringViewItem(column.get("title")),
				"format": viewitems.TRTEnumViewItem(avbutils.BinColumnFormat(column["format"])),
				"type": viewitems.TRTNumericViewItem(column["type"]),
				"hidden": viewitems.TRTStringViewItem(column["hidden"]),
			})

		for col in range(self._tree_binview.header().count()):
			self._tree_binview.resizeColumnToContents(col)
		
		self._tree_binview.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder)
		
		self._lbl_binview.setText(binview_datamodel.name)

def get_binview(bin_path:str) -> avb.bin.BinViewSetting:
	"""Get the binview data model"""

	with avb.open(bin_path) as bin_handle:
		return bin_handle.content.view_setting	

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