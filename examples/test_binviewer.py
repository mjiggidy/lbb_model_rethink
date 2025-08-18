import sys, os, pathlib
sys.path.insert(0,"/home/mjordan/dev/lbb_model_rethink/")
from PySide6 import QtCore, QtWidgets
from trt_model import viewmodels, viewitems



class BinLoaderSignals(QtCore.QObject):

	sig_load_start = QtCore.Signal()
	sig_load_complete = QtCore.Signal()

	sig_total_rows_determiend = QtCore.Signal(int)
	sig_row_loaded = QtCore.Signal(dict)
	sig_header_added = QtCore.Signal(viewitems.TRTAbstractViewHeaderItem)

class BinLoader(QtCore.QRunnable):



	def __init__(self, bin_path:os.PathLike):

		super().__init__()
		self._bin_path = bin_path
		self._signals = BinLoaderSignals()
	
	def signals(self) -> BinLoaderSignals:
		return self._signals
	
	def run(self):
		
		import avb, avbutils

		self.signals().sig_load_start.emit()

		header_keys = set()
		with avb.open(self._bin_path) as bin_handle:
			#self.signals().sig_total_rows_determiend.emit(len(bin_handle.content.items))
			for item in bin_handle.content.items:

				mob = item.mob
				item_row = dict()

				for key, val in mob.property_data.items():

					# Dereference property data
					if isinstance(val, avb.core.AVBPropertyData):
						val = list(avb.core.walk_references(val))

					if key == "usage_code":
						val = viewitems.TRTEnumViewItem(avbutils.MobUsage(val))
					elif key == "mob_type_id":
						val = viewitems.TRTEnumViewItem(avbutils.MobTypes(val))
					elif key == "media_kind_id":
						val = viewitems.TRTEnumViewItem(avbutils.MediaKind(val))
					elif key in ["creation_time","last_modified"]:
						val = viewitems.TRTDateTimeViewItem(val)
					else:
						val = viewitems.TRTStringViewItem(val)
					
					if key not in header_keys:
						header_keys.add(key)
						self._signals.sig_header_added.emit(viewitems.TRTAbstractViewHeaderItem(
							field_name   = key,
							display_name = key.replace("_"," ").title(),
							item_factory = viewitems.TRTStringViewItem,
						))

					item_row.update({key:val})
					
				self._signals.sig_row_loaded.emit(item_row)
			
			self._signals.sig_load_complete.emit()


class BinViewerMainWindow(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.setCentralWidget(QtWidgets.QWidget())
		self.centralWidget().setLayout(QtWidgets.QVBoxLayout())

		self._tree_viewer = QtWidgets.QTreeView()
		self._tree_viewer.setModel(QtCore.QSortFilterProxyModel())
		self._tree_viewer.setSortingEnabled(True)
		self._tree_viewer.setAlternatingRowColors(True)
		self._tree_viewer.setUniformRowHeights(True)
		self._tree_viewer.setIndentation(0)

		self.centralWidget().layout().addWidget(self._tree_viewer)

		self._lay_status = QtWidgets.QHBoxLayout()
		
		self._prog_status = QtWidgets.QProgressBar()
		self._prog_status.setRange(0,0)
		self._prog_status.setHidden(True)

		self._lbl_status = QtWidgets.QLabel()

		self._lay_status.addWidget(self._lbl_status)
		self._lay_status.addStretch()
		self._lay_status.addWidget(self._prog_status)

		self.centralWidget().layout().addLayout(self._lay_status)
	
	def treeViewer(self) -> QtWidgets.QTreeView:
		return self._tree_viewer

class BinViewerApp(QtWidgets.QApplication):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self._thread_pool = QtCore.QThreadPool()
		
		self._wnd_main = BinViewerMainWindow()
		self._wnd_main.resize(1024,600)

		self._view_model = viewmodels.TRTTimelineViewModel()
		self._wnd_main.treeViewer().model().setSourceModel(self._view_model)

		self._wnd_main.show()

	@QtCore.Slot(str)
	def load_bin(self, bin_path:os.PathLike):

		self._loader = BinLoader(bin_path)
		self._loader.signals().sig_load_start.connect(lambda: self._wnd_main.setWindowFilePath(bin_path))
		self._loader.signals().sig_load_start.connect(lambda: self._wnd_main._prog_status.setVisible(True))
		self._loader.signals().sig_load_start.connect(lambda: self._wnd_main._lbl_status.setText(f"Loading..."))

		#self._loader.signals().sig_total_rows_determiend.connect(self._wnd_main._prog_status.setMaximum)
		self._loader.signals().sig_header_added.connect(self._view_model.addHeader)
		self._loader.signals().sig_row_loaded.connect(self._view_model.addTimeline)
		#self._loader.signals().sig_row_loaded.connect(lambda: self._wnd_main._prog_status.setValue(self._wnd_main._prog_status.value()+1))
		
		self._loader.signals().sig_load_complete.connect(lambda: self._wnd_main._prog_status.setHidden(True))
		self._loader.signals().sig_load_complete.connect(lambda: self._wnd_main._lbl_status.setText(f"{self._wnd_main._tree_viewer.model().rowCount()} mobs loaded"))
		
		self._thread_pool.start(self._loader)





def main(bin_path:os.PathLike):

	app = BinViewerApp()
	app.setApplicationName("Bin Look-er-at-er")

	app.load_bin(bin_path)

	app.exec()


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} avid_bin_path.avb")
	
	main(sys.argv[1])
