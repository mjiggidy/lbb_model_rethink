import sys
from timecode import Timecode
import avbutils
import avb

from trt_model import viewmodels, viewitems
from PySide6 import QtWidgets, QtCore

def get_timelines_from_bin(bin_path:str):

	timeline_info_list = []

	with avb.open(bin_path) as bin_handle:

		for timeline in avbutils.get_timelines_from_bin(bin_handle.content):

			timeline_info_list.append({
				"clip_color": viewitems.TRTClipColorViewItem(avbutils.composition_clip_color(timeline)),
				"timeline_name": viewitems.TRTStringViewItem(timeline.name),
				"start_timecode": viewitems.TRTTimecodeViewItem(avbutils.get_timecode_range_for_composition(timeline).start),
				"duration_frames": viewitems.TRTNumericViewItem(avbutils.get_timecode_range_for_composition(timeline).duration),
				"duration_ff": viewitems.TRTFeetFramesViewItem(int(avbutils.get_timecode_range_for_composition(timeline).duration)),
				"duration_timecode": viewitems.TRTDurationViewItem(avbutils.get_timecode_range_for_composition(timeline).duration),
				"bin_path": viewitems.TRTPathViewItem(bin_path),
				"bin_lock": viewitems.TRTBinLockViewItem(avbutils.LockInfo("Tee hee hee!"))
			})
	
	return timeline_info_list



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

	headers = [
		viewitems.TRTAbstractViewHeaderItem("clip_color", "Clip Color", viewitems.TRTStringViewItem),
		viewitems.TRTAbstractViewHeaderItem("timeline_name", "Name", viewitems.TRTStringViewItem),
		viewitems.TRTAbstractViewHeaderItem("start_timecode", "Start TC", viewitems.TRTTimecodeViewItem),
		viewitems.TRTAbstractViewHeaderItem("duration_ff", "Duration (F+F)", viewitems.TRTFeetFramesViewItem),
		viewitems.TRTAbstractViewHeaderItem("duration_frames", "Duration (Frames)", viewitems.TRTNumericViewItem),
		viewitems.TRTAbstractViewHeaderItem("duration_timecode", "Duration (TC)", viewitems.TRTDurationViewItem),
		viewitems.TRTAbstractViewHeaderItem("bin_path", "Bin Path", viewitems.TRTPathViewItem),
		viewitems.TRTAbstractViewHeaderItem("bin_lock", "Bin Lock", viewitems.TRTBinLockViewItem),
	]

	for head in headers[::-1]:
		viewmodel_timelines.addHeader(head)


	timelines = get_timelines_from_bin(sys.argv[1])

	for timeline_info in timelines:
		viewmodel_timelines.addTimeline(timeline_info)

	return app.exec()

if __name__ == "__main__":
	sys.exit(main())