"""
View Models
"""
import typing
from .viewitems import TRTAbstractViewItem, TRTAbstractViewHeaderItem
from PySide6 import QtCore
import avbutils

class TRTSortFilterProxyModel(QtCore.QSortFilterProxyModel):
	"""QSortFilterProxyModel that implements natural sorting and such"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# Sort mimicking Avid natural sorting (9 before 10, etc)
		self._sort_collator = QtCore.QCollator()
		self._sort_collator.setNumericMode(True)
		self._sort_collator.setCaseSensitivity(QtCore.Qt.CaseSensitivity.CaseInsensitive)

		self._bin_display_items = avbutils.BinDisplayItemTypes(0)

		self.setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)

	def filterAcceptsRow(self, source_row:int, source_parent:QtCore.QModelIndex) -> bool:
		
		BIN_TYPES_COLUMN = 1
		
		src = self.mapToSource(self.index(source_row, BIN_TYPES_COLUMN, source_parent))
		item_types = src.data(QtCore.Qt.ItemDataRole.UserRole)

		
		
		if isinstance(item_types, avbutils.BinDisplayItemTypes):
			#print(source_row, item_types, avbutils.BinDisplayItemTypes.SHOW_CLIPS_CREATED_BY_USER in item_types)
			#print(self._bin_display_items & item_types)
			#print(f"{self._bin_display_items & item_types=}")
			return bool(item_types in self._bin_display_items)
		#else:
			#print(self.headerData(section=BIN_TYPES_COLUMN, orientation=QtCore.Qt.Orientation.Horizontal, role=QtCore.Qt.ItemDataRole.DisplayRole))
			#print(f"item_types is {item_types=}")
		
		return super().filterAcceptsRow(source_row, source_parent)
		
		
		
		#print(item_types & self.binDisplayItemTypes())
		#return bool(item_types & self.binDisplayItemTypes())

	
	def lessThan(self, source_left:QtCore.QModelIndex, source_right:QtCore.QModelIndex) -> bool:
		return self._sort_collator.compare(
			source_left.data(self.sortRole()),
			source_right.data(self.sortRole())
		) <= 0	# gt OR EQUAL TO reverses sort even if all thingies are equal, I like it
	
	@QtCore.Slot(object)
	def setBinDisplayItemTypes(self, types:avbutils.BinDisplayItemTypes):

		self._bin_display_items = types
		#print(self.binDisplayItemTypes())
		self.invalidateRowsFilter()
	
	def binDisplayItemTypes(self) -> avbutils.BinDisplayItemTypes:
		return self._bin_display_items
		

class TRTTimelineViewModel(QtCore.QAbstractItemModel):
	"""A view model for timelines"""

	def __init__(self):

		super().__init__()

		self._timelines:list[dict[str, TRTAbstractViewItem]] = []
		"""List of view items by key"""

		self._headers:list[TRTAbstractViewHeaderItem] = []
		"""List of view headers"""

	def parent(self, /, child:QtCore.QModelIndex) -> QtCore.QModelIndex:
		return QtCore.QModelIndex()
	
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
	
	def clear(self):
		self.beginResetModel()
		self._timelines = []
		self._headers = []
		self.endResetModel()
	
	def headerData(self, section:int, orientation:QtCore.Qt.Orientation, /, role:QtCore.Qt.ItemDataRole) -> typing.Any:
		if orientation == QtCore.Qt.Orientation.Horizontal:
			return self._headers[section].data(role)
	
	def fields(self) -> list[str]:
		"""Field names for mapping headers and columns, in order"""
		return [x.field_name() for x in self._headers]
	
	def addHeader(self, header:TRTAbstractViewHeaderItem) -> bool:
		self.beginInsertColumns(QtCore.QModelIndex(), 0, 0)
		self._headers.insert(0, header)
		self.endInsertColumns()
		return True

	def addTimeline(self, timeline:dict[str,TRTAbstractViewItem]) -> bool:

		self.beginInsertRows(QtCore.QModelIndex(), 0, 0)
		self._timelines.insert(0, timeline)
		self.endInsertRows()
		return True