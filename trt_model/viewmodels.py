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

		self._filter_bin_display_items = avbutils.BinDisplayItemTypes(0)
		self._filter_search_text       = ""

		self.setSortRole(QtCore.Qt.ItemDataRole.InitialSortOrderRole)

	def filterAcceptsRow(self, source_row:int, source_parent:QtCore.QModelIndex) -> bool:
		"""Filter rows based on all the applicable sift/bin display/search stuff"""

		return all((
			self.binDisplayFilter(source_row, source_parent),
			self.searchTextFilter(source_row, source_parent),
		))

		
		#return super().filterAcceptsRow(source_row, source_parent)
	
	def binDisplayFilter(self, source_row:int, source_parent:QtCore.QModelIndex) -> bool:
		"""Filter rows based on item type (via Bin Display settings)"""

		# Determine BinItemType column index from the source model (since it could be hidden)
		# NOTE: Once this is exclusively an AVB proxy model, won't need the `try`
		try:
			item_type_header_index = next(c
				for c in range(self.sourceModel().columnCount(source_parent))
				if self.sourceModel().headerData(c, QtCore.Qt.Orientation.Horizontal, role=QtCore.Qt.ItemDataRole.UserRole+1) == 200
			)
		except StopIteration:
#			print("Item types not available")
			# TODO: Pass through exception -- in AVB the type should definitely be available
			return super().filterAcceptsRow(source_row, source_parent)
		
		# Get the item type from the source moddel
		src_index = self.sourceModel().index(source_row, item_type_header_index, source_parent)
		item_types = src_index.data(QtCore.Qt.ItemDataRole.UserRole).raw_data()

		if isinstance(item_types, avbutils.BinDisplayItemTypes):
			return bool(item_types in self._filter_bin_display_items)
		else:
			raise ValueError(f"Invalid data type `{type(item_types).__name__}` for filter (expected `BinDisplayItemTypes`)")
	
	def searchTextFilter(self, source_row:int, source_parent:QtCore.QModelIndex) -> bool:
		"""Filter rows based on display text"""

		if not self._filter_search_text:
			return True

		search_text = self._filter_search_text.casefold()
		
		for source_col in range(self.sourceModel().columnCount()):

			# TODO: For later: ignore hidden columns
			if not self.filterAcceptsColumn(source_col, source_parent):
				continue

			source_text = self.sourceModel().data(self.sourceModel().index(source_row, source_col, source_parent), QtCore.Qt.ItemDataRole.DisplayRole) or ""
			if search_text in source_text.casefold():
				return True
		
		return False
	


	

	@QtCore.Slot(object)
	def setSearchText(self, search_text:str):
		"""Set the text filter"""

		self._filter_search_text = search_text
		self.invalidateRowsFilter()

	
	def lessThan(self, source_left:QtCore.QModelIndex, source_right:QtCore.QModelIndex) -> bool:
		return self._sort_collator.compare(
			source_left.data(self.sortRole()),
			source_right.data(self.sortRole())
		) <= 0	# gt OR EQUAL TO reverses sort even if all thingies are equal, I like it
	
	@QtCore.Slot(object)
	def setBinDisplayItemTypes(self, types:avbutils.BinDisplayItemTypes):

		self._filter_bin_display_items = types
		print(self.binDisplayItemTypes().__repr__())
		self.invalidateRowsFilter()
	
	def binDisplayItemTypes(self) -> avbutils.BinDisplayItemTypes:
		return self._filter_bin_display_items
	
	@QtCore.Slot(object)
	def setSearchFilterText(self, search_text:str):
		self._filter_search_text = search_text

	def searchFilterText(self) -> str:
		return self._filter_search_text
		

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
	
	def rowCount(self, /, parent:QtCore.QModelIndex=QtCore.QModelIndex()) -> int:
		if parent.isValid():
			return 0
		return len(self._timelines)
	
	def columnCount(self, /, parent:QtCore.QModelIndex=QtCore.QModelIndex()) -> int:
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