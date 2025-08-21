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
					field_name=column["title"],
					display_name=column["title"]
				)
			)
	
	@QtCore.Slot(object)
	def setMobs(self, mobs:list[avb.trackgroups.Composition]):
		
		#self.viewModel().clear()

		for mob in mobs:

			item = {"Name": mob.name}
			if "attributes" in mob.property_data and "_USER" in mob.attributes:
				item.update(mob.attributes.get("_USER"))
			self.addRow(item)



class BinViewLoader(QtCore.QRunnable):
	"""Load a given bin"""

	class Signals(QtCore.QObject):

		sig_begin_loading = QtCore.Signal()
		sig_got_view_settings = QtCore.Signal(object)
		sig_got_mobs = QtCore.Signal(object)
		sig_done_loading = QtCore.Signal()

	def __init__(self, bin_path:os.PathLike, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._bin_path = bin_path
		self._signals  = self.Signals()
	
	def run(self):
		self._signals.sig_begin_loading.emit()

		with avb.open(self._bin_path) as bin_handle:
			view_settings = bin_handle.content.view_setting
			view_settings.property_data = avb.core.AVBPropertyData(view_settings.property_data) # Dereference before closing file
			self._signals.sig_got_view_settings.emit(view_settings)

			toplevel_mobs = [i.mob for i in bin_handle.content.items if i.user_placed]
			for mob in toplevel_mobs:
				mob.attributes = dict(mob.attributes)
			self._signals.sig_got_mobs.emit(toplevel_mobs)
		
		self._signals.sig_done_loading.emit()
	
	def signals(self) -> Signals:
		return self._signals

class MainApplication(QtWidgets.QApplication):

	#sig_load_bin_data = QtCore.Signal(object)

	def __init__(self):

		super().__init__()

		self._threadpool = QtCore.QThreadPool()

		self._col_defs_presenter = BinViewColumDefinitionsPresenter()
		self._prop_data_presenter = BinViewPropertyDataPresenter()
		self._contents_presenter = BinContentsPresenter()
		#self.sig_load_bin_data.connect(self._col_defs_presenter.addRow)
		#self.sig_load_bin_data.connect(self._col_defs_presenter.addRow)

		self._btn_open = QtWidgets.QPushButton("Choose Bin...")
		self._btn_open.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FolderOpen))
		self._btn_open.clicked.connect(self.browseForBin)
		
		self._tree_column_defs = QtWidgets.QTreeView()
		self._tree_column_defs.setModel(QtCore.QSortFilterProxyModel())
		self._tree_column_defs.setSortingEnabled(True)
		self._tree_column_defs.setIndentation(0)
		self._tree_column_defs.model().setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)
		self._tree_column_defs.model().setSourceModel(self._col_defs_presenter.viewModel())

		self._tree_property_data = QtWidgets.QTreeView()
		self._tree_property_data.setModel(QtCore.QSortFilterProxyModel())
		self._tree_property_data.setIndentation(0)
		self._tree_property_data.setSortingEnabled(True)
		self._tree_property_data.model().setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)
		self._tree_property_data.model().setSourceModel(self._prop_data_presenter.viewModel())

		self._tree_bin_contents = QtWidgets.QTreeView()
		self._tree_bin_contents.setModel(QtCore.QSortFilterProxyModel())
		self._tree_bin_contents.setIndentation(0)
		self._tree_bin_contents.setSortingEnabled(True)
		self._tree_bin_contents.model().setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)
		self._tree_bin_contents.model().setSourceModel(self._contents_presenter.viewModel())


		self._tree_column_defs.show()
		self._tree_property_data.show()
		self._tree_bin_contents.show()
		self._btn_open.show()

	def loadBin(self, bin_path:str):
		"""Load the bin in another thread"""

		self._worker = BinViewLoader(bin_path)
		self._worker.signals().sig_begin_loading.connect(lambda: self._tree_bin_contents.setWindowFilePath(bin_path))
		
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_column_defs.setWindowTitle(f"{binview.name} | Column Definitions"))
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_property_data.setWindowTitle(f"{binview.name} | Property Data"))
		
		self._worker.signals().sig_got_view_settings.connect(self._col_defs_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._prop_data_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._contents_presenter.setBinView)

		self._worker.signals().sig_got_mobs.connect(self._contents_presenter.setMobs)
		self._threadpool.start(self._worker)
	
	@QtCore.Slot()
	def browseForBin(self):

		file_path, _  = QtWidgets.QFileDialog.getOpenFileName(self._btn_open, "Choose an Avid bin...", filter="Avid Bin (*.avb);;All Files (*)")
		self.loadBin(file_path)

if __name__ == "__main__":

	if len(sys.argv) < 2:
		import pathlib
		sys.exit(f"Usage: {pathlib.Path(__file__).name} path/to/avidbin.avb")
	
	app = MainApplication()
	app.loadBin(sys.argv[1])
	sys.exit(app.exec())