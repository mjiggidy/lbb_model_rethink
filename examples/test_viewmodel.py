import sys
from timecode import Timecode
from avbutils import LockInfo
from trt_model import viewmodels, viewitems
from PySide6 import QtWidgets, QtCore

def main():

	app = QtWidgets.QApplication()

	tree_timelines = QtWidgets.QTreeView()
	tree_timelines.setAlternatingRowColors(True)
	tree_timelines.setIndentation(0)
	tree_timelines.setSortingEnabled(True)
	tree_timelines.setUniformRowHeights(True)
	tree_timelines.show()

	viewmodel_timelines = viewmodels.TRTTimelineViewModel()
	
	tree_timelines.setModel(QtCore.QSortFilterProxyModel())
	tree_timelines.model().setSourceModel(viewmodel_timelines)

	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("timeline_name", "Name", viewitems.TRTStringViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("start_timecode", "Start TC", viewitems.TRTTimecodeViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("duration_ff", "Duration (F+F)", viewitems.TRTFeetFramesViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("duration_frames", "Duration (Frames)", viewitems.TRTNumericViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("duration_timecode", "Duration (TC)", viewitems.TRTDurationViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("bin_path", "Bin Path", viewitems.TRTPathViewItem))
	viewmodel_timelines.addHeader(viewitems.TRTAbstractViewHeaderItem("bin_lock", "Bin Lock", viewitems.TRTBinLockViewItem))

	viewmodel_timelines.addTimeline({
		"timeline_name": viewitems.TRTStringViewItem("Timeline 1"),
		"start_timecode": viewitems.TRTTimecodeViewItem(Timecode("01:00:00:00")),
		"duration_frames": viewitems.TRTNumericViewItem(2),
		"duration_ff": viewitems.TRTFeetFramesViewItem(800),
		"duration_timecode": viewitems.TRTDurationViewItem(Timecode(800)),
		"bin_path": viewitems.TRTPathViewItem("/Users/mjordan/Desktop/GLMP_250719_LensTest_01.mxf"),
		"bin_lock": viewitems.TRTBinLockViewItem(LockInfo("Tee hee hee!"))
	})

	viewmodel_timelines.addTimeline({
		"timeline_name": viewitems.TRTStringViewItem("Timeline 2"),
		"start_timecode": viewitems.TRTTimecodeViewItem(Timecode("02:00:00:00")),
		"duration_frames": viewitems.TRTNumericViewItem(4),
	})

	viewmodel_timelines.addTimeline({
		"timeline_name": viewitems.TRTStringViewItem("Timeline 3"),
		"start_timecode": viewitems.TRTTimecodeViewItem(Timecode("03:00:00:00")),
		"duration_frames": viewitems.TRTNumericViewItem(8),
		"bin_path": viewitems.TRTPathViewItem("/Users/mjordan/Desktop/GLMP_250719_LensTest_01.mxf")
	})

	return app.exec()

if __name__ == "__main__":
	sys.exit(main())