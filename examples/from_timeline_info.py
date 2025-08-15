from timecode import TimecodeRange, Timecode
from datetime import datetime
from trt_model.datamodels import TRTTimelineInfo, TRTTrimmedTimelineInfo, TRTMarkerPresetInfo

class Controller:

	def __init__(self):

		self._timelines:list[TRTTrimmedTimelineInfo] = []
	
	def addTimeline(self, timeline:TRTTimelineInfo):
		
		self._timelines.append(TRTTrimmedTimelineInfo(timeline))
		
		self._marker_ffoa:TRTMarkerPresetInfo|None = None
		self._marker_lfoa:TRTMarkerPresetInfo|None = None
	
	def setRelativeFFOA(self, ffoa:Timecode):
		
		for t in self._timelines:
			t.setGlobalFFOA(ffoa)
	
	def setRelativeLFOA(self, lfoa:Timecode):

		for t in self._timelines:
			t.setGlobalLFOA(lfoa)
	
	def setMarkerFFOA(self, marker_preset:TRTMarkerPresetInfo):

		self._marker_ffoa = marker_preset
		for t in self._timelines:
			t.setMarkerFFOAFromPreset(self._marker_ffoa)
	
	def setMarkerLFOA(self, marker_preset:TRTMarkerPresetInfo):

		self._marker_lfoa = marker_preset
		for t in self._timelines:
			t.setMarkerLFOAFromPreset(self._marker_lfoa)
	
	def trt(self) -> Timecode:
		return Timecode(sum(t.timelineTimecodeTrimmed().duration for t in self._timelines), rate=24)
	


def main():

	controller = Controller()

	for n in range(8):
		controller.addTimeline(TRTTimelineInfo(
			timeline_color=None,
			timeline_name= f"Reel {n}",
			timeline_tc_range=TimecodeRange(
				start = Timecode(f"0{n}:00:00:00", rate=24) + n,
				duration = Timecode("00:00:10", rate=24) - n
			),
			date_created=datetime.now(),
			date_modified=datetime.now(),
			markers=[],
			bin_path=f"/Users/mjordan/Desktop/Reel {n}.avb",
			bin_lock=None
		))
	before_trims = controller.trt()
	print(f"TRT before trims is {before_trims}")

	controller.setRelativeLFOA(Timecode(20, rate=24))
	
	after_trims = controller.trt()
	print(f"TRT after trims is {after_trims}")
	
	#for timeline in timelines:
	#	print(f"{timeline.timelineName()}: {timeline.timelineTimecodeTrimmed()}")

if __name__ == "__main__":
	main()