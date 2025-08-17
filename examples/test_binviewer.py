import sys, os, pathlib
import avb
from PySide6 import QtCore, QtGui, QtWidgets
from trt_model import viewmodels, viewitems

def main(bin_paths:list[os.PathLike]):

	property_data = []

	for bin_path in bin_paths:
		with avb.open(bin_path) as bin_handle:
			for mob in bin_handle.content.mobs:
				p = {}
				for key, val in mob.property_data.items():
					p.update({key: str(val)})
				property_data.append(p)

	
	headers = set()
	for p in property_data:
		headers.update(k for k in p)


	app = QtWidgets.QApplication()
	
	view_model = viewmodels.TRTTimelineViewModel()

	for header in headers:
		view_model.addHeader(
			viewitems.TRTAbstractViewHeaderItem(
				field_name   = header,
				display_name = header.replace("_"," ").title(),
				item_factory = viewitems.TRTStringViewItem,
			)
		)
	
	for mob in property_data:
		view_model.addTimeline({
			key: viewitems.TRTStringViewItem(val) for key, val in mob.items()
		})

	
	tree_binview = QtWidgets.QTreeView()
	tree_binview.setModel(QtCore.QSortFilterProxyModel())
	tree_binview.model().setSourceModel(view_model)
	tree_binview.setSortingEnabled(True)

	tree_binview.show()

	app.exec()


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} avid_bin_path.avb")
	
	main(sys.argv[1:])
