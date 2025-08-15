import dataclasses
import avbutils
from datetime import datetime, timezone
from timecode import TimecodeRange, Timecode

@dataclasses.dataclass
class TRTMarkerPresetInfo:
	"""Represents a marker matching preset thing"""

	preset_name:str
	"""The name of the marker matching preset"""

	color:avbutils.MarkerColors|None = None
	"""The marker criteria to match"""

	author:str|None = None

	comment:str|None = None

	def match(self, marker:avbutils.MarkerInfo) -> bool:
		"""Match this preset against a marker in a timeline"""

		return all([
			self.color   is not None and self.color     ==   marker.color,
			self.author  is not None and self.author  not in marker.author,
			self.comment is not None and self.comment not in marker.comment

		])


# I think  COMBINE  these into one thing
@dataclasses.dataclass(frozen=True)
class TRTTimelineInfo:
	"""Representation of a Timeline (well, Sequence) from an Avid bin"""

	timeline_name:str
	"""The name of the sequence"""

	timeline_tc_range:TimecodeRange
	"""Start TC of sequence"""

	timeline_color:avbutils.ClipColor|None
	"""16-bit RGB triad chosen for the sequence color label"""

	date_created:datetime
	"""The date the sequence was last modified in the bin"""

	date_modified:datetime
	"""The date the sequence was last modified in the bin"""

	markers:list[avbutils.MarkerInfo]
	"""markers found in this reel"""

	bin_path:str
	"""Bin path"""

	bin_lock:avbutils.LockInfo|None
	"""Bin lock info if available"""


class TRTTrimmedTimelineInfo:
	"""Cached and calculated timeline info based on current trims, etc"""

	def __init__(self, timeline_info:TRTTimelineInfo):
		
		self._timeline_info = timeline_info

		# Basic info interpreted to Qt objects
		# self._clip_color = QtGui.QColor.fromRgba64(*self._timeline_info.timeline_color.as_rgb16(), self._timeline_info.timeline_color.max_16b()) if self._timeline_info.timeline_color else QtGui.QColor()
		# self._date_modified = QtCore.QDateTime(self._timeline_info.date_modified.astimezone(timezone.utc))
		# self._date_created = QtCore.QDateTime(self._timeline_info.date_created.astimezone(timezone.utc))
		# self._bin_file_path = QtCore.QFileInfo(self._timeline_info.bin_path)

		# Base trims to apply
		self._default_ffoa = Timecode(0, rate=self._timeline_info.timeline_tc_range.rate)
		self._default_lfoa = Timecode(0, rate=self._timeline_info.timeline_tc_range.rate)

		# Marker match criteria applied, if matched
		self._marker_ffoa:TRTMarkerPresetInfo|None = None
		self._marker_lfoa:TRTMarkerPresetInfo|None = None

		self._timecode_trimmed = self._timeline_info.timeline_tc_range

	def timelineName(self) -> str:
		"""Timeline name"""
		return self._timeline_info.timeline_name
	
	def binFilePath(self) -> str:
		"""Bin file path"""
		return self._timeline_info.bin_path
	
	def binLockInfo(self) -> avbutils.LockInfo|None:
		"""Bin lock info if available"""
		return self._timeline_info.bin_lock
	
	def timelineColor(self) -> avbutils.ClipColor|None:
		"""Timeline clip color"""
		return self._timeline_info.timeline_color
	
	def timelineTimecodeExtents(self) -> TimecodeRange:
		"""Full timecode extents of the timeline (without trims)"""
		return self._timeline_info.timeline_tc_range
	
	def timelineTimecodeTrimmed(self) -> TimecodeRange:
		"""Trimmed timecode range (FFOA -> LFOA)"""
		return self._timecode_trimmed
	
	def timelineDateModified(self) -> datetime:
		"""Timeline date modified"""
		return self._timeline_info.date_modified
	
	def timelineDateCreated(self) -> datetime:
		"""Timeline date created"""
		return self._timeline_info.date_created

	def markerFFOA(self) -> TRTMarkerPresetInfo|None:
		"""Matched marker currently in use for FFOA (or `None`)"""
		return self._marker_ffoa
	
	def markerLFOA(self) -> TRTMarkerPresetInfo|None:
		"""Matched marker currently in use for LFOA (or `None`)"""
		return self._marker_lfoa
	
	def ffoaOffset(self) -> Timecode:
		"""Duration from head to FFOA"""
		return self._timecode_trimmed.start - self._timeline_info.timeline_tc_range.start
	
	def lfoaOffset(self) -> Timecode:
		"""Duration from LFOA to tail"""
		return self._timeline_info.timeline_tc_range.end - self._timecode_trimmed.end
	
	# Setters & Dynamic stuff
	def setGlobalFFOA(self, ffoa_offset:Timecode):
		"""Set the relative FFOA offset used "globally" for each timeline unless a marker match overrides this"""
		
		if ffoa_offset.rate != self._timecode_trimmed.rate:
			raise ValueError("FFOA duration rate must match the timeline's timecode rate")
		
		self._default_ffoa = ffoa_offset
		self._updateTimelineTimecodeTrimmed()

	def setGlobalLFOA(self, lfoa_offset:Timecode):
		"""Set the relative LFOA offset used "globally" for each timeline unless a marker match overrides this"""
		
		if lfoa_offset.rate != self._timecode_trimmed.rate:
			raise ValueError("LFOA duration rate must match the timeline's timecode rate")
		
		self._default_lfoa = lfoa_offset
		self._updateTimelineTimecodeTrimmed()

	def setMarkerFFOAFromPreset(self, marker_preset:TRTMarkerPresetInfo):
		"""See if we can match us some of them marker for FFOA"""

		self._marker_ffoa = self._findMarkerFromPreset(marker_preset, from_end=False) if marker_preset else None
		self._updateTimelineTimecodeTrimmed()

	def setMarkerLFOAFromPreset(self, marker_preset:TRTMarkerPresetInfo):
		"""See if we can match us some of them marker for LFOA"""

		self._marker_lfoa = self._findMarkerFromPreset(marker_preset, from_end=True) if marker_preset else None
		self._updateTimelineTimecodeTrimmed()

	def _updateTimelineTimecodeTrimmed(self):
		"""Update trimmed timecode extents using active ffoa/lfoa offsets"""

		# FFOA offset must be less than the total duration of the sequence
		resolved_ffoa_offset = min(self._marker_ffoa.frm_offset if self._marker_ffoa else self._default_ffoa.frame_number, self._timeline_info.timeline_tc_range.duration)
		adjusted_start_timecode:Timecode = self._timeline_info.timeline_tc_range.start + resolved_ffoa_offset
		

		# Offset must be less than total duration minus FFOA
		resolved_lfoa_offset = min(self._marker_lfoa.frm_offset if self._marker_lfoa else self._default_lfoa.frame_number, self._timeline_info.timeline_tc_range.duration - resolved_ffoa_offset)
		adjusted_end_timecode:Timecode   = self._timeline_info.timeline_tc_range.end   - resolved_lfoa_offset

		self._timecode_trimmed = TimecodeRange(
			start = adjusted_start_timecode,
			end   = adjusted_end_timecode
		)

	def _findMarkerFromPreset(self, marker_preset:TRTMarkerPresetInfo, from_end:bool=False):
		"""Match a marker to the given preset criteria"""

		for marker_info in sorted(self._timeline_info.markers, key=lambda m: m.frm_offset, reverse=from_end):
			if marker_preset.match(marker_info):
				return marker_info
		
		return None



class TRTDataModel:

	def __init__(self):

		self._marker_presets:list[TRTMarkerPresetInfo] = []
		self._timelines:list[TRTTrimmedTimelineInfo] = []


