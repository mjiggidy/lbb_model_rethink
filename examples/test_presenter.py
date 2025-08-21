import sys, os
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets
from trt_model import presenters, viewitems


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

		super().addRow(column_definition)

		

class BinViewLoader(QtCore.QRunnable):
	"""Load a given bin"""

	class Signals(QtCore.QObject):

		sig_begin_loading = QtCore.Signal()
		sig_got_view_settings = QtCore.Signal(object)
		sig_done_loading = QtCore.Signal()

	def __init__(self, bin_path:os.PathLike, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._bin_path = bin_path
		self._signals  = self.Signals()
	
	def run(self):
		self._signals.sig_begin_loading.emit()

		with avb.open(self._bin_path) as bin_handle:
			view_settings = bin_handle.content.view_setting
			#view_settings.property_data = avb.core.AVBPropertyData(view_settings.property_data) # Dereference before closing file
			self._signals.sig_got_view_settings.emit(view_settings)
		
		self._signals.sig_done_loading.emit()
	
	def signals(self) -> Signals:
		return self._signals

class MainApplication(QtWidgets.QApplication):

	sig_load_bin_data = QtCore.Signal(object)

	def __init__(self):

		super().__init__()

		self._threadpool = QtCore.QThreadPool()

		self._col_defs_presenter = BinViewColumDefinitionsPresenter()
		self.sig_load_bin_data.connect(self._col_defs_presenter.addRow)
		
		self._tree_viewer = QtWidgets.QTreeView()
		self._tree_viewer.setModel(QtCore.QSortFilterProxyModel())
		self._tree_viewer.setSortingEnabled(True)
		self._tree_viewer.model().setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)
		self._tree_viewer.model().setSourceModel(self._col_defs_presenter.viewModel())

		self._tree_viewer.show()

	def loadBin(self, bin_path:str):
		"""Load the bin in another thread"""

		self._worker = BinViewLoader(bin_path)
		self._worker.signals().sig_got_view_settings.connect(self._col_defs_presenter.setBinView)
		self._threadpool.start(self._worker)

if __name__ == "__main__":

	if len(sys.argv) < 2:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} path/to/avidbin.avb")
	
	app = MainApplication()
	app.loadBin(sys.argv[1])
	sys.exit(app.exec())