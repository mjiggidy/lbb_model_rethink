import dataclasses, enum
from PySide6 import QtCore
from .datamodels import TRTDataModel
from .viewmodels import TRTTimelineViewModel

class TRTTimelineDataTypes(enum.Enum):
	"""Types of data represented by the TRTDataModel"""

	STRING      = enum.auto()
	"""A standard string"""

	NUMERIC     = enum.auto()
	"""A numeric value"""

	FILEPATH    = enum.auto()
	"""A file path"""

	DATETIME    = enum.auto()
	"""A datetime entry"""

	TIMECODE    = enum.auto()
	"""A timecode"""

	DURATION    = enum.auto()
	"""A duration (hh:mm:ss:ff)"""

	FEET_FRAMES = enum.auto()
	"""A frame offset described in feet & frames (f+ff)"""

	CLIP_COLOR  = enum.auto()
	"""A clip color"""

	BIN_LOCK    = enum.auto()
	"""Bin lock info"""


@dataclasses.dataclass(frozen=True)
class TRTTimelinePresenterHeader:

	field_name:str
	"""A unique field name for the data"""

	display_name:str
	"""Display text for headers, etc"""

	data_type:TRTTimelineDataTypes
	"""Which type of data is represented"""


class TRTTimelinePresenter(QtCore.QObject):
	"""Interface between data and view models"""

	def __init__(self, data_model:TRTDataModel, view_model:TRTTimelineViewModel):
		
		self._data_model = data_model
		self._view_model = view_model
		
		self._headers = [
			TRTTimelinePresenterHeader(field_name="timeline_name", display_name="Name", data_type=TRTTimelineDataTypes.STRING),
			TRTTimelinePresenterHeader(field_name="timecode_start", display_name="Start TC", data_type=TRTTimelineDataTypes.TIMECODE),
			TRTTimelinePresenterHeader(field_name="timecode_end", display_name="End TC", data_type=TRTTimelineDataTypes.TIMECODE),
		]
	
	def dataModel(self) -> TRTDataModel:
		"""The data model in use"""
		return self._data_model
	
	def viewModel(self) -> TRTTimelineViewModel:
		"""The view model in use"""
		return self._view_model
	
	def setViewModelHeaders()