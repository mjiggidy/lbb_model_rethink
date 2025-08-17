import sys, os, pathlib
import avb, avbutils
from PySide6 import QtCore, QtWidgets
from trt_model import viewmodels, viewitems



def main(bin_path:os.PathLike):

	app = QtWidgets.QApplication()
	app.setApplicationName("Bin Look-er-at-er")

	data_model = []
	view_model = viewmodels.TRTTimelineViewModel()

	with avb.open(bin_path) as bin_handle:
		for item in bin_handle.content.items:
			mob = item.mob
			p = {}
			for key, val in mob.property_data.items():
				if isinstance(val, avb.core.AVBPropertyData):
					val = list(avb.core.walk_references(val))
				p.update({key: val})
			data_model.append(p)

	
	header_keys = set()

	for mob in data_model:

		mob_view_item:dict[str, viewitems.TRTAbstractViewItem] = {}

		for key,val in mob.items():

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
			
			header_keys.add(key)
			mob_view_item.update({key: val})

		view_model.addTimeline(mob_view_item)
	
	for header in header_keys:
		view_model.addHeader(
			viewitems.TRTAbstractViewHeaderItem(
				field_name   = header,
				display_name = header.replace("_"," ").title(),
				item_factory = viewitems.TRTStringViewItem,
			)
		)
	
	print("Showing", len(data_model))

	
	tree_binview = QtWidgets.QTreeView()
	tree_binview.setModel(QtCore.QSortFilterProxyModel())
	tree_binview.model().setSourceModel(view_model)
	tree_binview.setSortingEnabled(True)
	tree_binview.setAlternatingRowColors(True)
	tree_binview.setUniformRowHeights(True)
	tree_binview.setIndentation(0)

	tree_binview.show()
	#tree_binview.setWindowTitle(app.applicationName())
	tree_binview.setWindowFilePath(bin_path)

	app.exec()


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {pathlib.Path(__file__).name} avid_bin_path.avb")
	
	main(sys.argv[1])
