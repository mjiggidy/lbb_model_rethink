"""
View Models
"""
import typing
from viewitems import TRTAbstractViewItem, TRTAbstractViewHeaderItem
from PySide6 import QtCore

class TRTTimelineViewModel(QtCore.QAbstractItemModel):
	"""A view model for timelines"""

	def __init__(self):

		super().__init__()

		self._timelines:list[dict[str, TRTAbstractViewItem]] = []
		"""List of view items by key"""

		self._headers:list[TRTAbstractViewHeaderItem] = []
		"""List of view headers"""
	
	def rowCount(self, /, parent:QtCore.QModelIndex) -> int:
		if parent.isValid():
			return 0
		return len(self._timelines)
	
	def columnCount(self, /, parent:QtCore.QModelIndex) -> int:
		if parent.isValid():
			return 0
		return len(self._headers)
	
	def index(self, row:int, column:int, /, parent:QtCore.QModelIndex) -> QtCore.QModelIndex:
		if parent.isValid():
			return QtCore.QModelIndex()
		return self.createIndex(row, column)
	
	def data(self, index:QtCore.QModelIndex, /, role:QtCore.Qt.ItemDataRole) -> typing.Any:
		if not index.isValid():
			return None
		
		timeline   = self._timelines[index.row()]
		field_name = self._headers[index.column()].field_name()

		if field_name not in timeline:
			return None

		return timeline.get(field_name).data(role)
	
	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, /, role:QtCore.Qt.ItemDataRole) -> typing.Any:
		if orientation == QtCore.Qt.Orientation.Horizontal:
			return self._headers[section].data(role)
	
	def insertHeader(self, header:TRTAbstractViewHeaderItem) -> bool:
		
		self.beginInsertColumns(QtCore.QModelIndex(), 0, 0)
		self._headers.insert(0, header)
		self.endInsertColumns()

	def insertTimeline(self, timeline:dict[str,TRTAbstractViewItem]) -> bool:

		self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
		self._timelines.insert(0, timeline)
		self.endInsertRows()