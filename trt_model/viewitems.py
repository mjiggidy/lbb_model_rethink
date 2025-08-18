"""
View Items for View Models
"""

import typing, enum, datetime
import avbutils
from timecode import Timecode
from PySide6 import QtCore, QtGui, QtWidgets

class TRTAbstractViewHeaderItem:
	"""An abstract header item for TRT views"""

	def __init__(self, field_name:str, display_name:str, item_factory:typing.Type["TRTAbstractViewItem"], delegate:QtWidgets.QStyledItemDelegate|None=None):

		self._field_name = field_name
		self._display_name = display_name

		self._item_factory = item_factory

		self._delgate = delegate

		self._data_roles = {}
		self._prepare_data()
	
	def _prepare_data(self):
		"""Precalculate Header Data"""

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole: str(self._display_name),
			QtCore.Qt.ItemDataRole.UserRole:    str(self._item_factory),
		 })
	
	def data(self, role:QtCore.Qt.ItemDataRole) -> typing.Any:
		return self._data_roles.get(role, None)
	
	def itemData(self) -> dict[QtCore.Qt.ItemDataRole, typing.Any]:
		return self._data_roles
	
	def item_factory(self) -> typing.Type:
		return self._item_factory
	
	def field_name(self) -> str:
		return self._field_name
	
	def delegate(self) -> QtWidgets.QStyledItemDelegate:
		return self._delgate

class TRTAbstractViewItem:
	"""An abstract item for TRT views"""

	def __init__(self, raw_data:typing.Any, icon:QtGui.QIcon|None=None, tooltip:QtWidgets.QToolTip|str|None=None):
		#super().__init__()

		self._data = raw_data
		self._icon = icon
		self._tooltip = tooltip 

		self._data_roles = {}
		self._prepare_data()
	
	def _prepare_data(self):
		"""Precalculate them datas for all them roles"""
		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:          self.to_string(self._data),
			QtCore.Qt.ItemDataRole.ToolTipRole:          self._tooltip if self._tooltip is not None else repr(self._data),
			QtCore.Qt.ItemDataRole.DecorationRole:       self._icon,
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: avbutils.human_sort(str(self._data)),
			QtCore.Qt.ItemDataRole.UserRole:             self._data,
		})

	def data(self, role:QtCore.Qt.ItemDataRole) -> typing.Any:
		"""Get item data for a given role.  By default, returns the raw data as a string."""
		return self._data_roles.get(role, None)
	
	def setData(self, role:QtCore.Qt.ItemDataRole, data:typing.Any):
		"""Override data for a particular role"""
		self._data_roles[role] = data
	
	def itemData(self) -> dict[QtCore.Qt.ItemDataRole, typing.Any]:
		"""Get all item data roles"""
		return self._data_roles
	
	def to_json(self) -> str:
		"""Format as JSON object"""
		return self.data(QtCore.Qt.ItemDataRole.DisplayRole)
	
	@classmethod
	def to_string(cls, data:typing.Any) -> str:
		return str(data)
	
class TRTStringViewItem(TRTAbstractViewItem):
	"""A standard string"""

	def _prepare_data(self):
		super()._prepare_data()

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:          str(self._data),
		})

class TRTEnumViewItem(TRTAbstractViewItem):
	"""Represents an Enum"""

	def __init__(self, raw_data:enum.Enum, *args, **kwargs):
		super().__init__(raw_data, *args, **kwargs)

	def _prepare_data(self):
		super()._prepare_data()

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:          self._data.name.replace("_", " ").title(),
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: self._data.value,
		})
	

class TRTNumericViewItem(TRTAbstractViewItem):
	"""A numeric value"""

	STRING_PADDING:int = 0
	"""Left-side padding for string formatting"""

	def __init__(self, raw_data:int, *args, **kwargs):
		super().__init__(raw_data, *args, **kwargs)

	def _prepare_data(self):
		super()._prepare_data()

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:          self.to_string(self._data),
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: self._data,
			QtCore.Qt.ItemDataRole.FontRole:             QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.SystemFont.FixedFont),
		})
	
	def to_json(self) -> int:
		return self.data(QtCore.Qt.ItemDataRole.UserRole)
	
	@classmethod
	def to_string(cls, data):
		return super().to_string(data).rjust(cls.STRING_PADDING)

class TRTPathViewItem(TRTAbstractViewItem):
	"""A file path"""

	def __init__(self, raw_data:str|QtCore.QFileInfo):
		super().__init__(QtCore.QFileInfo(raw_data))
	
	def _prepare_data(self):
		super()._prepare_data()

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:          self._data.fileName(),
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: avbutils.human_sort(self._data.fileName()),
			QtCore.Qt.ItemDataRole.DecorationRole:       QtWidgets.QFileIconProvider().icon(self._data),
			QtCore.Qt.ItemDataRole.ToolTipRole:          QtCore.QDir.toNativeSeparators(self._data.absoluteFilePath()),
		})
	
	def to_json(self) -> str:
		return QtCore.QDir.toNativeSeparators(self.data(QtCore.Qt.ItemDataRole.UserRole).absoluteFilePath())

class TRTDateTimeViewItem(TRTAbstractViewItem):
	"""A datetime entry"""

	def __init__(self, raw_data:datetime.datetime, format_string:QtCore.Qt.DateFormat|str=QtCore.Qt.DateFormat.TextDate):
		
		self._format_string = format_string
		
		super().__init__(QtCore.QDateTime.fromMSecsSinceEpoch(int(raw_data.timestamp() * 1000)).toLocalTime())
	
	def setFormatString(self, format_string:str):
		"""Set the datetime formatting string used by strftime"""
		self._format_string = format_string
		self._data_roles.update()
	
	def formatString(self) -> str:
		"""The datetime formatting string used by strftime"""
		return self._format_string

	def _prepare_data(self):
		super()._prepare_data()
	
		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole: self._data.toString(self._format_string),
		})
	
	def to_json(self) -> dict:
		return {
			"type": "datetime",
			"timestamp": self.data(QtCore.Qt.ItemDataRole.UserRole).timestamp(),
			"formatted": self.data(QtCore.Qt.ItemDataRole.DisplayRole)
		}

class TRTTimecodeViewItem(TRTNumericViewItem):
	"""A timecode"""

	def __init__(self, raw_data:Timecode, *args, **kwargs):
		if not isinstance(raw_data, Timecode):
			raise TypeError("Data must be an instance of `Timecode`")
		super().__init__(raw_data, *args, **kwargs)
	
	def _prepare_data(self):
		super()._prepare_data()
		self._data_roles.update({
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: self._data.frame_number,
		})
	
	def to_json(self) -> dict:
		tc = self.data(QtCore.Qt.ItemDataRole.UserRole)
		return {
			"type": "timecode",
			"frames": tc.frame_number,
			"rate": tc.rate,
			"formatted": self.data(QtCore.Qt.ItemDataRole.DisplayRole).strip()
		}

class TRTDurationViewItem(TRTTimecodeViewItem):
	"""A duration (hh:mm:ss:ff), a subset of timecode"""

	def _prepare_data(self):
		super()._prepare_data()
		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole: self.to_string(self._data),
		})
	
	@classmethod
	def to_string(cls, data):

		tc_str = str(data)
		is_neg =tc_str.startswith("-")
		
		# Get the index of the last separator
		leading_chars = 1
		sep = ":"
		idx_last_sep = tc_str.rfind(sep) - leading_chars
		pre, post = tc_str[:idx_last_sep], tc_str[idx_last_sep:]
		pre = pre.lstrip("-00" + sep)

		return f"{'-' if is_neg else ''}{pre}{post}".rjust(cls.STRING_PADDING)

class TRTFeetFramesViewItem(TRTNumericViewItem):
	"""A frame offset described in feet & frames (f+ff)"""

	def __init__(self, raw_data:int, *args, **kwargs):

		if not isinstance(raw_data, int):
			raise TypeError(f"Data must be an integer (not {type(raw_data)})")
		super().__init__(raw_data, *args, **kwargs)

	def _prepare_data(self):
		super()._prepare_data()
	
	def to_json(self) -> dict:
		return {
			"type":      "feet_frames",
			"format":    "35mm",
			"perfs":     4,
			"frames":    self.data(QtCore.Qt.ItemDataRole.UserRole),
			"formatted": self.data(QtCore.Qt.ItemDataRole.DisplayRole).strip()
		}
	
	@classmethod
	def to_string(cls, data):
		return str(str(data // 16) + "+" + str(data % 16).zfill(2)).rjust(cls.STRING_PADDING)

class TRTClipColorViewItem(TRTAbstractViewItem):
	"""A clip color"""

	def __init__(self, raw_data:avbutils.ClipColor|QtGui.QRgba64, *args, **kwargs):

		if isinstance(raw_data, avbutils.ClipColor):
			raw_data = QtGui.QColor.fromRgba64(*raw_data.as_rgb16())
		elif isinstance(raw_data, QtGui.QRgba64):
			raw_data = QtGui.QColor.fromRgba64(raw_data)
		elif not isinstance(raw_data, QtGui.QColor):
			raise TypeError(f"Data must be a QColor object (got {type(raw_data)})")
		
		super().__init__(raw_data, *args, **kwargs)
	
	def _prepare_data(self):
		# Not calling super, would be weird

		color = QtGui.QColor(self._data)

		self._data_roles.update({
			QtCore.Qt.ItemDataRole.UserRole: self._data,
			QtCore.Qt.ItemDataRole.ToolTipRole: f"R: {color.red()} G: {color.green()} B: {color.blue()}" if color.isValid() else None,
			QtCore.Qt.ItemDataRole.InitialSortOrderRole: self._data.getRgb()
		})
	
	def to_json(self) -> dict|None:

		color = self.data(QtCore.Qt.ItemDataRole.UserRole)
		
		if not color.isValid():
			return None
		
		color_64 = color.rgba64()

		return {
			"type": "color",
			"rgb16": [color_64.red(), color_64.green(), color_64.blue()],
			"rgb8": [color.red(), color.green(), color.blue()],
			"hex": self.data(QtCore.Qt.ItemDataRole.UserRole).name()
		}

class TRTBinLockViewItem(TRTAbstractViewItem):
	"""Bin lock info"""

	# Note: For now I think we'll do a string, but want to expand this later probably
	def __init__(self, raw_data:avbutils.LockInfo, *args, **kwargs):
		super().__init__(raw_data, *args, **kwargs)

	def _prepare_data(self):
		super()._prepare_data()
		self._data_roles.update({
			QtCore.Qt.ItemDataRole.DisplayRole:    self._data.name if self._data else "",
			QtCore.Qt.ItemDataRole.DecorationRole: QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.SystemLockScreen if self._data else None)
		})
	
	def to_json(self) -> str|None:
		return self.data(QtCore.Qt.ItemDataRole.DisplayRole) or None

