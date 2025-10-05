"""
This spiraled out of control into an Avid bin viewer
I'll eventually pull this out and into its own project
"""

import sys, os, enum
import avb, avbutils, timecode
from PySide6 import QtCore, QtGui, QtWidgets
from trt_model import presenters, viewitems, viewmodels, delegates

class PushButtonAction(QtWidgets.QPushButton):
	"""A QPushButton with Action support"""

	def __init__(self, action:QtGui.QAction|None=None, show_text:bool=True, show_icon:bool=True, show_tooltip:bool=True, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self._action = None
		
		self._show_text    = show_text
		self._show_icon    = show_icon
		self._show_tooltip = show_tooltip

		if action:
			self.setAction(action)
	
	def setAction(self, action:QtGui.QAction):

		if self._action:

			# Disconnect previous action
			self._action.enabledChanged.disconnect(self.setEnabled)
			self._action.visibleChanged.disconnect(self.setVisible)
			self._action.checkableChanged.disconnect(self.setCheckable)
			self._action.toggled.disconnect(self.setChecked)

			self.clicked.disconnect(self._action.trigger)
		
		self._action = action

		self.setEnabled(self._action.isEnabled())
		self.setVisible(self._action.isVisible())
		self.setCheckable(self._action.isCheckable())
		self.setChecked(self._action.isChecked())

		self.setIcon(self._action.icon() if self._show_icon else QtGui.QIcon())
		self.setToolTip(self._action.toolTip() if self._show_tooltip else None)
		self.setText(self._action.text() if self._show_text else None)

		self._action.enabledChanged.connect(self.setEnabled)
		self._action.visibleChanged.connect(self.setVisible)
		self._action.checkableChanged.connect(self.setCheckable)
		self._action.toggled.connect(self.setChecked)

		self.clicked.connect(self._action.trigger)





class BinContentsWidget(QtWidgets.QWidget):
	"""Display bin contents and controls"""

	sig_request_open_bin = QtCore.Signal()
	sig_request_bin_display  = QtCore.Signal()
	sig_request_display_mode = QtCore.Signal(object)

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.setAutoFillBackground(True)

		self.setLayout(QtWidgets.QVBoxLayout())
		
		#self.setContentsMargins(0,0,0,0)
		self.layout().setContentsMargins(0,0,0,0)
		self.layout().setSpacing(0)

		self._section_top       = QtWidgets.QToolBar()
		self._tree_bin_contents = BinTreeView()
		self._section_bottom    = QtWidgets.QWidget()

		self.layout().addWidget(self._section_top)
		self.layout().addWidget(self._tree_bin_contents)
		self.layout().addWidget(self._section_bottom)

		#self._section_top.setLayout(QtWidgets.QHBoxLayout())
		#self._section_top.layout().setContentsMargins(0,0,0,0)
		#self._section_top.layout().setSpacing(0)

		toolbar_font = self._section_top.font()
		toolbar_font.setPointSizeF(toolbar_font.pointSizeF() * 0.8)
		self._section_top.setFont(toolbar_font)
		self._section_bottom.setFont(toolbar_font)

		#self._cmb_bin_view_list = QtWidgets.QComboBox()
		#self._cmb_bin_view_list.setSizePolicy(self._cmb_bin_view_list.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Policy.MinimumExpanding)
#
		#self._btngrp_view_modes = QtWidgets.QButtonGroup()
		#self._btngrp_view_modes.idClicked.connect(lambda id: self.sig_request_display_mode.emit(avbutils.BinDisplayModes(id)))
		#self.sig_request_display_mode.connect(lambda d: print(d.name))
#
		#self._btn_view_list = QtWidgets.QPushButton()
		#self._btn_view_list.setCheckable(True)
		#self._btn_view_list.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatTextDirectionLtr))
#
		#self._btn_view_script = QtWidgets.QPushButton()
		#self._btn_view_script.setCheckable(True)
		#self._btn_view_script.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentProperties))
#
		#self._btn_view_frame = QtWidgets.QPushButton()
		#self._btn_view_frame.setCheckable(True)
		#self._btn_view_frame.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.CameraPhoto))
#
		#self._btngrp_view_modes.addButton(self._btn_view_list)
		#self._btngrp_view_modes.setId(self._btn_view_list, avbutils.BinDisplayModes.LIST.value)
		#self._btngrp_view_modes.addButton(self._btn_view_script)
		#self._btngrp_view_modes.setId(self._btn_view_script, avbutils.BinDisplayModes.SCRIPT.value)
		#self._btngrp_view_modes.addButton(self._btn_view_frame)
		#self._btngrp_view_modes.setId(self._btn_view_frame, avbutils.BinDisplayModes.FRAME.value)
#
		#self._btn_request_open = QtWidgets.QPushButton("&Open Bin...")
		#self._btn_request_open.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentOpen))
		#self._btn_request_open.clicked.connect(self.sig_request_open_bin)
		#
		#self._section_top.addWidget(self._btn_request_open)
		
		sep = QtWidgets.QWidget()
		sep.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
		#self._section_top.addWidget(sep)
		#self._section_top.addWidget(self._cmb_bin_view_list)
		#self._section_top.addWidget(self._btn_view_list)
		#self._section_top.addWidget(self._btn_view_script)
		#self._section_top.addWidget(self._btn_view_frame)

		self._section_bottom.setLayout(QtWidgets.QHBoxLayout())
		self._section_bottom.layout().setContentsMargins(2,2,2,2)

		self._section_bottom.layout().addStretch()
		self._lbl_bin_item_count = QtWidgets.QLabel()
		self._section_bottom.layout().addWidget(self._lbl_bin_item_count)

		self._btn_show_bin_display = QtWidgets.QPushButton()
		self._btn_show_bin_display.setCheckable(True)
		self._btn_show_bin_display.toggled.connect(self.sig_request_bin_display)
		self._btn_show_bin_display.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.GoNext))

		self._section_bottom.layout().addWidget(self._btn_show_bin_display)


	def treeView(self) -> "BinTreeView":
		"""Get the main view"""
		return self._tree_bin_contents
	
	def setTreeView(self, treeview:"BinTreeView"):
		self._tree_bin_contents = treeview
	
	def topSectionWidget(self) -> QtWidgets.QWidget:
		return self._section_top
	
	def setTopSectionWidget(self, widget:QtWidgets.QWidget):
		self._section_top = widget
	
	def bottomSectionWidget(self) -> QtWidgets.QWidget:
		return self._section_bottom
	
	def setBottomSectionWidget(self, widget:QtWidgets.QWidget):
		self._section_bottom = widget
	
	@QtCore.Slot(object)
	def setDisplayMode(self, mode:avbutils.BinDisplayModes):
		pass
		#self._btngrp_view_modes.button(mode.value).setChecked(True)

	@QtCore.Slot()
	def _connectSourceModelSlots(self):

		source_model = self._tree_bin_contents.model().sourceModel()

		if not source_model:
			return
		
		source_model.rowsInserted.connect(self.updateBinStats)
		source_model.rowsRemoved.connect(self.updateBinStats)
		source_model.modelReset.connect(self.updateBinStats)

	@QtCore.Slot()
	def updateBinStats(self):

		#print("HI")

		count_visible = self._tree_bin_contents.model().rowCount()
		count_all = self._tree_bin_contents.model().sourceModel().rowCount()
		self._lbl_bin_item_count.setText(f"Showing {QtCore.QLocale.system().toString(count_visible)} of {QtCore.QLocale.system().toString(count_all)} items")
	


class AbstractEnumFlagsView(QtWidgets.QWidget):

	sig_flag_toggled  = QtCore.Signal(object, bool)
	sig_flags_changed = QtCore.Signal(object)

	def __init__(self, initial_values:enum.Flag=None, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self._option_mappings:dict[enum.Flag, QtWidgets.QCheckBox] = dict()

		self._flags = initial_values

		# Set initial values
		for option in self._flags.__class__.__members__.values():

			chk_option = QtWidgets.QCheckBox(text=option.name.replace("_"," ").title())
			chk_option.setProperty("checkvalue", option)
			
			chk_option.clicked.connect(lambda is_checked, option=option:self._option_changed(option, is_checked))
			
			self._option_mappings[option] = chk_option

		self.updateCheckStates()
		
	@QtCore.Slot(object)
	def _option_changed(self, option:enum.Flag, is_enabled:bool):


		if is_enabled:
			self._flags |= option
		else:
			self._flags &= ~option

		self.sig_flag_toggled.emit(option, is_enabled)
		self.sig_flags_changed.emit(self._flags)
	
	def flags(self) -> enum.Flag:

		return self._flags
	
	def setFlags(self, options:enum.Flag):
		"""Set all options from a given flags enum"""

		if not isinstance(options, type(self._flags)):
			raise TypeError(f"Flags must be type {type(self._flags).__name__} (not ({type(options).__name__}))")
		
		self._flags = options
		
		self.updateCheckStates()
	
	def updateCheckStates(self):
		"""Update the check states"""

		for option, chk in self._option_mappings.items():
			chk.setCheckState(QtCore.Qt.CheckState.Checked if bool(self._flags & option) else QtCore.Qt.CheckState.Unchecked)
		


class BinDisplayItemTypesView(AbstractEnumFlagsView):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)
		
		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setSpacing(0)
		self.layout().setContentsMargins(3,0,3,0)

		grp_clips = QtWidgets.QGroupBox(title="Clip Types")

		grp_clips.setLayout(QtWidgets.QVBoxLayout())
		grp_clips.layout().setSpacing(0)
		grp_clips.layout().setContentsMargins(3,0,3,0)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.MASTER_CLIP]
		chk.setText("Master Clips")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.LINKED_MASTER_CLIP]
		chk.setText("Linked Master Clips")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.SUBCLIP]
		chk.setText("Subclips")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.SEQUENCE]
		chk.setText("Sequences")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.SOURCE]
		chk.setText("Sources")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.EFFECT]
		chk.setText("Effects")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.MOTION_EFFECT]
		chk.setText("Motion Effects")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.PRECOMP_RENDERED_EFFECT]
		chk.setText("Precompute Clips - Rendered Effects")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.PRECOMP_TITLE_MATTEKEY]
		chk.setText("Precompute Clips - Titles and Matte Keys")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.GROUP]
		chk.setText("Groups")
		grp_clips.layout().addWidget(chk)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.STEREOSCOPIC_CLIP]
		chk.setText("Stereoscopic Clips")
		grp_clips.layout().addWidget(chk)

		self.layout().addWidget(grp_clips)

		grp_origins = QtWidgets.QGroupBox(title="Clip Origins")
		grp_origins.setLayout(QtWidgets.QVBoxLayout())
		grp_origins.layout().setSpacing(0)
		grp_origins.layout().setContentsMargins(3,0,3,0)

		chk = self._option_mappings[avbutils.BinDisplayItemTypes.USER_CLIP]
		chk.setText("Show clips created by user")
		grp_origins.layout().addWidget(chk)
		
		chk = self._option_mappings[avbutils.BinDisplayItemTypes.REFERENCE_CLIP]
		chk.setText("Show reference clips")
		grp_origins.layout().addWidget(chk)
		

		self.layout().addWidget(grp_origins)

		self.layout().addStretch()

class BinSiftSettingsView(QtWidgets.QWidget):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.setContentsMargins(0,0,0,0)

		self.setLayout(QtWidgets.QVBoxLayout())
		self.layout().setContentsMargins(0,0,0,0)

		self._chk_sift_enabled = QtWidgets.QCheckBox("Sift Enabled")

		self._tree_siftsettings = BinTreeView()

		self.layout().addWidget(self._chk_sift_enabled)
		self.layout().addWidget(self._tree_siftsettings)


class BinAppearanceSettingsView(QtWidgets.QWidget):

	sig_font_changed = QtCore.Signal(QtGui.QFont)
	sig_palette_changed = QtCore.Signal(QtGui.QPalette)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.setLayout(QtWidgets.QVBoxLayout())

		self._spn_geo_x = QtWidgets.QSpinBox()
		self._spn_geo_x.setSuffix(" px")
		self._spn_geo_x.setMaximum(9999)
		self._spn_geo_x.setMinimum(-9999)
		self._spn_geo_x.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
		self._spn_geo_y = QtWidgets.QSpinBox()
		self._spn_geo_y.setSuffix(" px")
		self._spn_geo_y.setMaximum(9999)
		self._spn_geo_y.setMinimum(-9999)
		self._spn_geo_y.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

		self._spn_geo_w = QtWidgets.QSpinBox()
		self._spn_geo_w.setSuffix(" px")
		self._spn_geo_w.setMaximum(9999)
		self._spn_geo_w.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
		#self._spn_geo_w.setMinimum(-9999)
		self._spn_geo_h = QtWidgets.QSpinBox()
		self._spn_geo_h.setSuffix(" px")
		self._spn_geo_h.setMaximum(9999)
		self._spn_geo_h.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
		#self._spn_geo_h.setMinimum(-9999)

		self.layout().addWidget(QtWidgets.QLabel("Window Geometry"))
		
		lay_geo= QtWidgets.QGridLayout()
		lay_geo.addWidget(QtWidgets.QLabel("X:"), 0, 0, QtCore.Qt.AlignmentFlag.AlignRight)
		lay_geo.addWidget(self._spn_geo_x, 0, 1)
		lay_geo.addWidget(QtWidgets.QLabel("Y:"), 1, 0, QtCore.Qt.AlignmentFlag.AlignRight)
		lay_geo.addWidget(self._spn_geo_y, 1, 1)
		
		lay_geo.setColumnStretch(2, 1)
		
		lay_geo.addWidget(QtWidgets.QLabel("W:"), 0, 3, QtCore.Qt.AlignmentFlag.AlignRight)
		lay_geo.addWidget(self._spn_geo_w, 0, 4)
		lay_geo.addWidget(QtWidgets.QLabel("H:"), 1, 3, QtCore.Qt.AlignmentFlag.AlignRight)
		lay_geo.addWidget(self._spn_geo_h, 1, 4)
		#lay_geo_dimensions.addStretch()

		self.layout().addLayout(lay_geo)

		self._chk_was_iconic = QtWidgets.QCheckBox("Was Iconic")
		self.layout().addWidget(self._chk_was_iconic)

		lay_fonts = QtWidgets.QHBoxLayout()
		self._cmb_fonts = QtWidgets.QFontComboBox()
		self._spn_size  = QtWidgets.QSpinBox(minimum=8, maximum=100)	# Avid font dialog extents

		self.layout().addWidget(QtWidgets.QLabel("Font And Colors"))
		lay_fonts.addWidget(self._cmb_fonts)
		lay_fonts.addWidget(self._spn_size)

		self.layout().addLayout(lay_fonts)

		lay_colors = QtWidgets.QHBoxLayout()
		self._btn_fg_color = QtWidgets.QPushButton()
		self._btn_bg_color = QtWidgets.QPushButton()

		lay_colors.addWidget(self._btn_fg_color)
		lay_colors.addWidget(self._btn_bg_color)

		self.layout().addLayout(lay_colors)

		self._tree_column_widths = BinTreeView()
		self.layout().addWidget(QtWidgets.QLabel("Column Widths"))
		self.layout().addWidget(self._tree_column_widths)

		

		self._cmb_fonts.currentFontChanged.connect(self.sig_font_changed)
		self._spn_size.valueChanged.connect(lambda: self.sig_font_changed.emit(self.binFont()))

		self._btn_fg_color.clicked.connect(self.fgColorPickerRequested)
		self._btn_bg_color.clicked.connect(self.bgColorPickerRequested)

	@QtCore.Slot(bool)
	def setWasIconic(self, was_iconic:bool):
		#print(was_iconic)
		self._chk_was_iconic.setChecked(was_iconic)

	# TODO I'm sure this can be one method
	@QtCore.Slot()
	def bgColorPickerRequested(self):
		
		bg_color,_ = self.binPalette()
		new_color = QtWidgets.QColorDialog.getColor(bg_color, self._btn_fg_color, "Choose a text color")
		
		if new_color.isValid():
			self.setBinBackgroundColor(new_color)

	@QtCore.Slot()
	def fgColorPickerRequested(self):
		
		fg_color,_ = self.binPalette()
		new_color = QtWidgets.QColorDialog.getColor(fg_color, self._btn_fg_color, "Choose a text color")

		if new_color.isValid():
			self.setBinForegroundColor(new_color)
	
	@QtCore.Slot(QtCore.QRect)
	def setBinRect(self, rect:QtCore.QRect):
		#print(rect)
		
		self._spn_geo_x.setValue(rect.x())
		self._spn_geo_y.setValue(rect.y())
		self._spn_geo_w.setValue(rect.width())
		self._spn_geo_h.setValue(rect.height())

	@QtCore.Slot(QtGui.QFont)
	def setBinFont(self, font:QtGui.QFont):

		self._cmb_fonts.setCurrentFont(font)
		self._spn_size.setValue(font.pixelSize())

	@QtCore.Slot(QtGui.QColor)
	def setBinForegroundColor(self, color:QtGui.QColor):
		
		fg = self._btn_fg_color.palette()
		fg.setColor(QtGui.QPalette.ColorRole.Button, color)
		
		self._btn_fg_color.setPalette(fg)
		self._btn_fg_color.setText(self._format_color_text(fg.color(QtGui.QPalette.ColorRole.Button)))
		self.sig_palette_changed.emit(self.binPalette())

	@QtCore.Slot(QtGui.QColor)
	def setBinBackgroundColor(self, color:QtGui.QColor):
		
		bg = self._btn_bg_color.palette()
		bg.setColor(QtGui.QPalette.ColorRole.Button, color)
		
		self._btn_bg_color.setPalette(bg)
		self._btn_bg_color.setText(self._format_color_text(bg.color(QtGui.QPalette.ColorRole.Button)))

		self.sig_palette_changed.emit(self.binPalette())

	
	@staticmethod
	def _format_color_text(color:QtGui.QColor) -> str:
		return f"R: {color.red()}  G: {color.green()}  B: {color.blue()}"

	@QtCore.Slot(QtGui.QPalette)
	def setBinPalette(self, fg_color:QtGui.QColor, bg_color:QtGui.QColor):

		self.blockSignals(True)
		self.setBinForegroundColor(fg_color)
		self.setBinBackgroundColor(bg_color)
		self.blockSignals(False)
		self.sig_palette_changed.emit(self.binPalette())
	
	def binFont(self) -> QtGui.QFont:
		font = self._cmb_fonts.currentFont()
		font.setPixelSize(self._spn_size.value())
		return font
	
	def binPalette(self) -> tuple[QtGui.QColor, QtGui.QColor]:
		"""Returns a tuple of `(fg_color:QtGui.QColor, bg_color:QtGui.QColor)`.  Weird notation lol"""

		return (
			self._btn_fg_color.palette().color(QtGui.QPalette.ColorRole.Button),
			self._btn_bg_color.palette().color(QtGui.QPalette.ColorRole.Button),
		)


class BinTreeView(QtWidgets.QTreeView):
	"""QTreeView but nicer"""

	ITEM_DELEGATES_PER_FIELD_ID = {
		51: delegates.LBClipColorItemDelegate(),

	}
	"""Specialized one-off fields"""

	ITEM_DELEGATES_PER_FORMAT_ID = {
		avbutils.BinColumnFormat.TIMECODE: delegates.LBTimecodeItemDelegate(),
	}
	"""Delegate for generic field formats"""

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		
		self.setModel((viewmodels.TRTSortFilterProxyModel()))

		self.setSortingEnabled(True)
		self.setRootIsDecorated(False)
		self.setAlternatingRowColors(True)
		self.setUniformRowHeights(True)

		self.header().setFirstSectionMovable(True)
		self.header().setDefaultAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

		self.model().columnsInserted.connect(
			lambda parent_index, source_start, source_end:
			self.assignItemDelegates(parent_index, source_start)
		)
		self.model().columnsMoved.connect(
			lambda source_parent, source_logical_start, source_logical_end, destination_parent, destination_logical_start:	# NOTE: Won't work for heirarchical models
			self.assignItemDelegates(destination_parent, min(source_logical_start, destination_logical_start))
		)

	@QtCore.Slot(object, int, int)
	def assignItemDelegates(self, parent_index:QtCore.QModelIndex, logical_start_column:int):
		"""Assign item delegates starting with the first changed logical row, cascaded through to the end"""

		if parent_index.isValid():
			return
		
		for col in range(logical_start_column, self.model().columnCount()):
			
			field_id     = self.model().headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.UserRole+1)
			format_id    = self.model().headerData(col, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.UserRole+2)

			item_delegate = self.itemDelegate()


			# Look up specialized fields
			if field_id in self.ITEM_DELEGATES_PER_FIELD_ID:
				item_delegate = self.ITEM_DELEGATES_PER_FIELD_ID[field_id]
			# Look up specialized generic formats
			elif format_id in self.ITEM_DELEGATES_PER_FORMAT_ID:
				item_delegate = self.ITEM_DELEGATES_PER_FORMAT_ID[format_id]
			
			self.setItemDelegateForColumn(col, item_delegate)

	def columnDisplayNames(self) -> list[str]:
		"""Get all column display names, in order"""
		
		return [
			self.model().headerData(idx,
				QtCore.Qt.Orientation.Horizontal,
				QtCore.Qt.ItemDataRole.DisplayRole
			)
			for idx in range(self.header().count())
		]
	
	def setBinDisplayItemTypes(self, types:avbutils.BinDisplayItemTypes):
		self.model().setBinDisplayItemTypes(types)
	
	def binDisplayItemTypes(self) -> avbutils.BinDisplayItemTypes:
		return self.model().binDisplayItemTypes()
	
	@QtCore.Slot()
	def resizeAllColumnsToContents(self):
		for idx in range(self.header().count()):
			self.resizeColumnToContents(idx)

	@QtCore.Slot(object)
	def setColumnWidths(self, column_widths:dict[str,int]):

		if not column_widths:

			self.resizeAllColumnsToContents()
			return
		
		column_names = self.columnDisplayNames()

		for col, width in column_widths.items():
		
			try:
				col_idx = column_names.index(col)
			except ValueError:
				continue
		
			self.setColumnWidth(col_idx, width)
	
	@QtCore.Slot(str, QtCore.Qt.SortOrder)
	def sortByColumnName(self, column_name:str, sort_order:QtCore.Qt.SortOrder) -> bool:
		"""Sort by a column's display name"""

		column_names = self.columnDisplayNames()

		try:
			header_index = column_names.index(column_name)
		except ValueError:
			return False

		self.sortByColumn(header_index, sort_order)
		return True

	def sizeHintForColumn(self, column):
		return super().sizeHintForColumn(column) + 24




class BinViewColumDefinitionsPresenter(presenters.LBItemDefinitionView):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):
		self.viewModel().clear()

		headers = [
			viewitems.TRTAbstractViewHeaderItem("order", "Order"),
			viewitems.TRTAbstractViewHeaderItem("title", "Title"),
			viewitems.TRTAbstractViewHeaderItem("format", "Format"),
			viewitems.TRTAbstractViewHeaderItem("type", "Type"),
			viewitems.TRTAbstractViewHeaderItem("hidden", "Is Hidden"),
		]
		
		for header in headers[::-1]:
			super().addHeader(header)

		for idx, column in enumerate(bin_view.columns):
			column.update({"order": idx})
			self.addColumnDefinition(column)

	@QtCore.Slot(object)
	def addColumnDefinition(self, column_definition:dict[str,object]):

		column_definition["format"] = avbutils.BinColumnFormat(column_definition["format"])
		self.addRow(column_definition)

class BinViewPropertyDataPresenter(presenters.LBItemDefinitionView):

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):

		self.viewModel().clear()

		headers = [
			viewitems.TRTAbstractViewHeaderItem("name", "Name"),
			viewitems.TRTAbstractViewHeaderItem("value", "Value"),
		]
		
		for header in headers[::-1]:
			self.addHeader(header)
		
		for key,val in bin_view.property_data.items():
			self.addRow({"name": key, "value": val})

class BinAppearanceSettingsPresenter(presenters.LBItemDefinitionView):

	sig_font_changed          = QtCore.Signal(QtGui.QFont)
	sig_palette_changed       = QtCore.Signal(QtGui.QColor, QtGui.QColor)
	sig_column_widths_changed = QtCore.Signal(object)
	sig_window_rect_changed   = QtCore.Signal(object)
	sig_was_iconic_changed    = QtCore.Signal(bool)

	@QtCore.Slot(object, object, object, object, object, object, object)
	def setAppearanceSettings(self,
		bin_font:str|int,
		mac_font_size:int,
		foreground_color:list[int],
		background_color:list[int],
		column_widths:dict[str,int],
		window_rect:list[int],
		was_iconic:bool):
		
		font = QtGui.QFont()

		if isinstance(bin_font, str) and QtGui.QFontDatabase.hasFamily(bin_font):
			font.setFamily(bin_font)

		elif isinstance(bin_font, int) and len(QtGui.QFontDatabase.families()) > bin_font:
			font.setFamily(QtGui.QFontDatabase.families()[bin_font])
		
		font.setPixelSize(mac_font_size)

		self.setColumnWidths(column_widths)
		self.setWindowRect(window_rect)
		self.sig_was_iconic_changed.emit(was_iconic)
		self.sig_column_widths_changed.emit(column_widths)
		self.sig_font_changed.emit(font)
		self.sig_palette_changed.emit(
			QtGui.QColor.fromRgba64(*foreground_color),
			QtGui.QColor.fromRgba64(*background_color),
		)


	@QtCore.Slot(object)
	def setWindowRect(self, window_rect:list[int]):

		self.sig_window_rect_changed.emit(QtCore.QRect(
			QtCore.QPoint(*window_rect[:2]),
			QtCore.QPoint(*window_rect[2:])
		))

	
	@QtCore.Slot(object)
	def setColumnWidths(self, column_widths:dict[str,int]):
		"""Display column width settings"""

		self.viewModel().clear()

		for col, width in column_widths.items():
			self.addRow({
				"Width":  width,
				"Column": col,
			}, add_new_headers=True)

class BinSortingPropertiesPresenter(presenters.LBItemDefinitionView):
	"""Bin sorting"""

	sig_bin_sorting_changed = QtCore.Signal(object)

	@QtCore.Slot(object)
	def setBinSortingProperties(self, sorting:list[int,str]):
		
		self.viewModel().clear()

		headers = [
			viewitems.TRTAbstractViewHeaderItem("order", "Order"),
			viewitems.TRTAbstractViewHeaderItem("direction", "Direction"),
			viewitems.TRTAbstractViewHeaderItem("column", "Column")
		]

		for header in headers[::-1]:
			self.addHeader(header)
		
		for order, (direction, column_name) in enumerate(sorting):
			self.addRow({
				"order": order,
				"direction": QtCore.Qt.SortOrder(direction),
				"column": column_name
			})
		
		self.sig_bin_sorting_changed.emit([(QtCore.Qt.SortOrder(direction), column_name) for direction, column_name in sorting])

class BinSiftSettingsPresenter(presenters.LBItemDefinitionView):

	sig_sift_enabled = QtCore.Signal(bool)

	@QtCore.Slot(bool, object)
	def setSiftSettings(self, sift_enabled:bool, sift_settings:list[avb.bin.SiftItem]):
		self.sig_sift_enabled.emit(sift_enabled)

		self.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="string", display_name="String"))
		self.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="method", display_name="Method"))
		self.addHeader(viewitems.TRTAbstractViewHeaderItem(field_name="column", display_name="Column"))
		for idx, setting in enumerate(sift_settings):
			self.addRow({
				"order": idx,
				"method": viewitems.TRTEnumViewItem(avbutils.BinSiftMethod(setting.method)),
				"string": setting.string,
				"column": setting.column,
			})

class BinContentsPresenter(presenters.LBItemDefinitionView):

	@QtCore.Slot(object)
	def setBinView(self, bin_view:avb.bin.BinViewSetting):

		self.viewModel().clear()

		for column in bin_view.columns[::-1]:

			if column["hidden"]:
				continue

			self.addHeader(
				viewitems.TRTAbstractViewHeaderItem(
					field_name="40_"+column["title"] if column["type"] == 40 else str(column["type"]),
					field_id=column["type"],
					format_id=column["format"],
					display_name=column["title"],
				)
			)
	
	@QtCore.Slot(object)
	def addMob(self, mob_info:dict):
		self.addRow(mob_info)



class BinViewLoader(QtCore.QRunnable):
	"""Load a given bin"""

	class Signals(QtCore.QObject):

		sig_begin_loading = QtCore.Signal()
		sig_got_display_mode = QtCore.Signal(object)
		sig_got_bin_appearance_settings = QtCore.Signal(object, object, object, object, object, object, object)
		sig_got_display_options = QtCore.Signal(object)
		sig_got_view_settings = QtCore.Signal(object)
		sig_got_mob = QtCore.Signal(object)
		sig_got_sort_settings = QtCore.Signal(object)
		sig_got_sift_settings = QtCore.Signal(bool, object)
		sig_done_loading = QtCore.Signal()

	def __init__(self, bin_path:os.PathLike, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._bin_path = bin_path
		self._signals  = self.Signals()
	
	def run(self):
		self._signals.sig_begin_loading.emit()

		with avb.open(self._bin_path) as bin_handle:
			
			self._loadBinDisplayItemTypes(bin_handle.content)
			self._loadBinView(bin_handle.content)
			self._loadBinDisplayMode(bin_handle.content)
			self._loadBinSiftSettings(bin_handle.content.sifted, bin_handle.content.sifted_settings)
			self._loadBinSorting(bin_handle.content.sort_columns)
			self._loadBinAppearanceSettings(bin_handle.content)
			
			for bin_item in bin_handle.content.items:
				try:
					self._loadCompositionMob(bin_item)
				except Exception as e:
					print(f"{e} {bin_item.mob}")
		
		self._signals.sig_done_loading.emit()

	def _loadBinDisplayMode(self, bin_content:avb.bin.Bin):
		"""Load the display mode"""

		self.signals().sig_got_display_mode.emit(avbutils.BinDisplayModes.get_mode_from_bin(bin_content))

	def _loadBinAppearanceSettings(self, bin_content:avb.bin.Bin):
		"""General and misc appearance settings stored around the bin"""

		# Sus out that font name
		# Try for Bin Font Name (strongly preferred), or fall back on mac font index (not likely to work)
		if "attributes" in bin_content.property_data and "ATTR__BIN_FONT_NAME" in bin_content.attributes:
			bin_font = bin_content.attributes["ATTR__BIN_FONT_NAME"]
		else:
			bin_font = bin_content.mac_font

		# Try to load bin column widths from the "BIN_COLUMNS_WIDTHS" bytearray, which decodes to a JSON string
		# I'm decoding it as UTF-8 but I almost doubt that's truly what it is.
		try:
			import json
			bin_column_widths = json.loads(bin_content.attributes.get("BIN_COLUMNS_WIDTHS",{}).decode("utf-8"))
		except:
			bin_column_widths = {}

		self.signals().sig_got_bin_appearance_settings.emit(
			bin_font,
			bin_content.mac_font_size,
			bin_content.forground_color,
			bin_content.background_color,
			bin_column_widths,
			bin_content.home_rect,
			bin_content.was_iconic,
		)
		
	def _loadBinDisplayItemTypes(self, bin_content:avb.bin.Bin):
		self._signals.sig_got_display_options.emit(avbutils.BinDisplayItemTypes.get_options_from_bin(bin_content))
	
	def _loadBinView(self, bin_content:avb.bin.Bin):
		
		bin_view = bin_content.view_setting
		bin_view.property_data = avb.core.AVBPropertyData(bin_view.property_data) # Dereference before closing file
		
		self._signals.sig_got_view_settings.emit(bin_view)
	
	def _loadBinSiftSettings(self, is_sifted:bool, sifted_settings:list[avb.bin.SiftItem]):
		self._signals.sig_got_sift_settings.emit(is_sifted, sifted_settings)
	
	def _loadBinSorting(self, bin_sorting:list):
		self.signals().sig_got_sort_settings.emit(bin_sorting)

	def _loadCompositionMob(self, bin_item:avb.bin.BinItem):
			
			#if not bin_item.user_placed:
			#	return
			
			bin_item_role = avbutils.BinDisplayItemTypes.from_bin_item(bin_item)
			#print(display_options)

			comp = bin_item.mob


			tape_name = None
			source_file_name = None
			timecode_range = None
			user_attributes = dict()
			source_drive = None

			if avbutils.BinDisplayItemTypes.SEQUENCE in bin_item_role:
				timecode_range = avbutils.get_timecode_range_for_composition(comp)
				user_attributes = comp.attributes.get("_USER",{})

			else:

				#primary_track = avbutils.format_track_label(avbutils.sourcerefs.primary_track_for_composition(comp))

				if avbutils.sourcerefs.composition_has_physical_source(comp):
				
					if avbutils.sourcerefs.physical_source_type_for_composition(comp) == avbutils.SourceMobRole.SOURCE_FILE:
						source_file_name = avbutils.sourcerefs.physical_source_name_for_composition(comp)
					else:
						tape_name = avbutils.sourcerefs.physical_source_name_for_composition(comp)
				
				# Drive info
				if "descriptor" in comp.property_data and isinstance(comp.descriptor, avb.essence.MediaDescriptor) and isinstance(comp.descriptor.locator, avb.misc.MSMLocator):
					source_drive = comp.descriptor.locator.last_known_volume
				else:
					try:
					# TODO: Do if comp itself is file source first, otherwise...
						file_source_clip, offset = next(avbutils.file_references_for_component(avbutils.primary_track_for_composition(comp).component))
					except StopIteration as e:
						#print("No file soruce:",comp)
						pass
					else:
						if isinstance(file_source_clip.mob.descriptor.locator, avb.misc.MSMLocator):
							source_drive = file_source_clip.mob.descriptor.locator.last_known_volume
							#print(source_drive)
				
				# Timecode
				# NOTE: This is all pretty sloppy here.
				try:
					timecode_range = avbutils.get_timecode_range_for_composition(comp)
				except Exception as e:
					pass

				attributes_reverse = []
				for source, offset in avbutils.source_references_for_component(avbutils.sourcerefs.primary_track_for_composition(comp).component):
					
					if "attributes" in source.mob.property_data:
						attributes_reverse.append(source.mob.attributes.get("_USER",{}))
					
					# Timecode
					try:
						tc_track = next(avbutils.get_tracks_from_composition(source.mob, type=avbutils.TrackTypes.TIMECODE, index=1))
					except:
						pass
					else:
						tc_component, offset = avbutils.resolve_base_component_from_component(tc_track.component, offset + source.start_time)
						
						if not isinstance(tc_component, avb.components.Timecode):
							print("Hmm",tc_component)
							continue
						
						timecode_range = timecode.TimecodeRange(
							start = timecode.Timecode(tc_component.start + offset.frame_number, rate=offset.rate),
							duration=comp.length
						)
				for a in reversed(attributes_reverse):
					user_attributes.update(a)
				if "attributes" in comp.property_data:
					user_attributes.update(comp.attributes.get("_USER",{}))


					


			markers = avbutils.get_markers_from_timeline(comp)
			#print(comp.property_data)

			item = {
				avbutils.BIN_COLUMN_ROLES["Name"]: comp.name or "",
				avbutils.BIN_COLUMN_ROLES["Color"]: viewitems.TRTClipColorViewItem(avbutils.composition_clip_color(comp) if avbutils.composition_clip_color(comp) else None),
				avbutils.BIN_COLUMN_ROLES["Start"]: timecode_range.start if timecode_range else "",
				avbutils.BIN_COLUMN_ROLES["End"]: timecode_range.end if timecode_range else "",
				avbutils.BIN_COLUMN_ROLES["Duration"]: viewitems.TRTDurationViewItem(timecode_range.duration) if timecode_range else "",
				avbutils.BIN_COLUMN_ROLES["Modified Date"]: comp.last_modified,
				avbutils.BIN_COLUMN_ROLES["Creation Date"]: comp.creation_time,
				avbutils.BIN_COLUMN_ROLES[""]: bin_item_role,
				avbutils.BIN_COLUMN_ROLES["Marker"]: viewitems.TRTMarkerViewItem(markers[0]) if markers else None,
				avbutils.BIN_COLUMN_ROLES["Tracks"]: avbutils.format_track_labels(list(avbutils.get_tracks_from_composition(comp))) or None,
				avbutils.BIN_COLUMN_ROLES["Tape"]: tape_name or "",
				avbutils.BIN_COLUMN_ROLES["Drive"]: source_drive or "",
				avbutils.BIN_COLUMN_ROLES["Source File"]: source_file_name or "",
				avbutils.BIN_COLUMN_ROLES["Scene"]: user_attributes.get("Scene") or "",
				avbutils.BIN_COLUMN_ROLES["Take"]: user_attributes.get("Take") or "",
			}

			for key, val in user_attributes.items():
				item.update({"40_"+key: val})
			
			self._signals.sig_got_mob.emit(item)

	
	def signals(self) -> Signals:
		return self._signals

class MainApplication(QtWidgets.QApplication):

	#sig_load_bin_data = QtCore.Signal(object)

	def __init__(self):


		super().__init__()

		HIDE_DOCK = True
		
		self._threadpool = QtCore.QThreadPool(self)

		# Actions
		self._act_open = QtGui.QAction("Open Bin...", self)
		self._act_open.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.DocumentOpen))
		self._act_open.setToolTip("Choose a bin to open")
		self._act_open.setShortcut(QtGui.QKeySequence.StandardKey.Open)
		self._act_open.triggered.connect(self.browseForBin)

		self._act_quit = QtGui.QAction("Quit")
		self._act_quit.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ApplicationExit))
		self._act_quit.setShortcut(QtGui.QKeySequence.StandardKey.Quit)
		self._act_quit.setMenuRole(QtGui.QAction.MenuRole.QuitRole)
		self._act_quit.triggered.connect(self.quit)

		self._actgrp_file = QtGui.QActionGroup(self)
		self._actgrp_file.addAction(self._act_open)
		self._actgrp_file.addAction(self._act_quit)


		self._act_view_list   = QtGui.QAction("List View", checkable=True, checked=True)
		self._act_view_list.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FormatJustifyFill))
		self._act_view_list.setToolTip("Show items in list view mode")

		self._act_view_frame  = QtGui.QAction("Frame View", checkable=True)
		self._act_view_frame.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.AudioCard))
		self._act_view_frame.setToolTip("Show items in frame view mode")

		self._act_view_script = QtGui.QAction("Script View", checkable=True)
		self._act_view_script.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.ListAdd))
		self._act_view_script.setToolTip("Show items in script view mode")

		self._actgrp_view_mode = QtGui.QActionGroup(self)
		self._actgrp_view_mode.setExclusive(True)
		self._actgrp_view_mode.addAction(self._act_view_list)
		self._actgrp_view_mode.addAction(self._act_view_frame)
		self._actgrp_view_mode.addAction(self._act_view_script)


		self._prog_loading = QtWidgets.QProgressBar()
		self._prog_loading.setSizePolicy(self._prog_loading.sizePolicy().horizontalPolicy(), QtWidgets.QSizePolicy.Policy.Ignored)
		#self._prog_loading.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
		#self._prog_loading.setWindowFlag(QtCore.Qt.WindowType.Tool)
		self._prog_loading.setRange(0,0)
		#self._prog_loading.setWindowTitle("Loading bin...")

		self._col_defs_presenter = BinViewColumDefinitionsPresenter()
		self._prop_data_presenter = BinViewPropertyDataPresenter()
		self._contents_presenter = BinContentsPresenter()
		self._sorting_presenter = BinSortingPropertiesPresenter()
		self._sift_presenter = BinSiftSettingsPresenter()
		self._appearance_presenter = BinAppearanceSettingsPresenter()

		self._sorting_presenter.sig_bin_sorting_changed.connect(self.sortBinContents)

		self._btn_open = QtWidgets.QPushButton("Choose Bin...")
		self._btn_open.setIcon(QtGui.QIcon.fromTheme(QtGui.QIcon.ThemeIcon.FolderOpen))
		self._btn_open.clicked.connect(self.browseForBin)

		self._view_BinDisplayItemTypes = BinDisplayItemTypesView(avbutils.BinDisplayItemTypes.default_items())
		
		self._view_BinAppearanceSettings = BinAppearanceSettingsView()
		self._view_BinAppearanceSettings._tree_column_widths.model().setSourceModel(self._appearance_presenter.viewModel())
		self._appearance_presenter.sig_font_changed.connect(self._view_BinAppearanceSettings.setBinFont)
		self._appearance_presenter.sig_palette_changed.connect(self._view_BinAppearanceSettings.setBinPalette)
		self._view_BinAppearanceSettings.sig_font_changed.connect(self._appearance_presenter.sig_font_changed)
		self._appearance_presenter.sig_was_iconic_changed.connect(self._view_BinAppearanceSettings.setWasIconic)
		#self._view_BinAppearanceSettings.sig_palette_changed.connect(self._appearance_presenter.sig)
		# Incomplete

		self._view_binsiftsettings = BinSiftSettingsView()
		self._view_binsiftsettings._tree_siftsettings.model().setSourceModel(self._sift_presenter.viewModel())
		self._sift_presenter.sig_sift_enabled.connect(self._view_binsiftsettings._chk_sift_enabled.setChecked)

				
		self._tree_column_defs = BinTreeView()
		self._tree_column_defs.model().setSourceModel(self._col_defs_presenter.viewModel())
		self._tree_column_defs.activated.connect(self.focusBinColumn)

		self._tree_property_data = BinTreeView()
		self._tree_property_data.model().setSourceModel(self._prop_data_presenter.viewModel())

		self._main_bin_contents = BinContentsWidget()
		self._main_bin_contents.topSectionWidget().addWidget(PushButtonAction(action=self._act_open))
		sep = QtWidgets.QWidget()
		sep.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
		self._main_bin_contents.topSectionWidget().addWidget(sep)

		self._cmb_bin_view_list = QtWidgets.QComboBox()
		self._cmb_bin_view_list.setMinimumWidth(self._cmb_bin_view_list.fontMetrics().averageCharWidth()*20)
		self._cmb_bin_view_list.setMaximumWidth(self._cmb_bin_view_list.fontMetrics().averageCharWidth()*32)
		self._cmb_bin_view_list.setToolTip("Current bin view")
		#self._cmb_bin_view_list.addItem("Current View")
		self._main_bin_contents.topSectionWidget().addWidget(self._cmb_bin_view_list)

		self._main_bin_contents.topSectionWidget().addSeparator()

		self._main_bin_contents.topSectionWidget().addWidget(PushButtonAction(action=self._act_view_list, show_text=False))
		self._main_bin_contents.topSectionWidget().addWidget(PushButtonAction(action=self._act_view_frame, show_text=False))
		self._main_bin_contents.topSectionWidget().addWidget(PushButtonAction(action=self._act_view_script, show_text=False))

		self._main_bin_contents.bottomSectionWidget().layout().insertWidget(0, self._prog_loading)

		self._txt_search = QtWidgets.QLineEdit()
		self._txt_search.setFixedWidth(self._txt_search.fontMetrics().averageCharWidth() * 20)
		self._txt_search.setPlaceholderText("Find in bin...")
		self._txt_search.setToolTip("Filter all items based on this text")
		self._txt_search.setClearButtonEnabled(True)

		self._main_bin_contents.topSectionWidget().addSeparator()

		self._main_bin_contents.topSectionWidget().addWidget(self._txt_search)

		self._main_bin_contents.sig_request_open_bin.connect(self.browseForBin)
		
		
		self._tree_bin_contents = self._main_bin_contents.treeView()
		self._tree_bin_contents.model().setSourceModel(self._contents_presenter.viewModel())

		self._tree_bin_contents.model().rowsInserted.connect(self._main_bin_contents.updateBinStats)
		self._tree_bin_contents.model().rowsRemoved.connect(self._main_bin_contents.updateBinStats)
		self._tree_bin_contents.model().modelReset.connect(self._main_bin_contents.updateBinStats)
		self._tree_bin_contents.model().sourceModel().rowsInserted.connect(self._main_bin_contents.updateBinStats)
		self._tree_bin_contents.model().sourceModel().rowsRemoved.connect(self._main_bin_contents.updateBinStats)
		self._tree_bin_contents.model().sourceModel().modelReset.connect(self._main_bin_contents.updateBinStats)

		self._txt_search.textEdited.connect(self._tree_bin_contents.model().setSearchText)

		self._view_BinDisplayItemTypes.sig_flags_changed.connect(self._tree_bin_contents.setBinDisplayItemTypes)
		
		#self._tree_bin_contents.setItemDelegateForColumn(0, delegates.LBClipColorItemDelegate())
		self._appearance_presenter.sig_font_changed.connect(self._tree_bin_contents.setFont)
		self._appearance_presenter.sig_palette_changed.connect(self._set_tree_palette)
		self._appearance_presenter.sig_column_widths_changed.connect(self._tree_bin_contents.setColumnWidths)
		
		self._tree_sort_properties = BinTreeView()
		self._tree_sort_properties.model().setSourceModel(self._sorting_presenter.viewModel())

		# Main Window Setup
		self._wnd_main = QtWidgets.QMainWindow()
		self._wnd_main.resize(1024, 600)
		self._wnd_main.setCentralWidget(self._main_bin_contents)

		self._mnu_file = QtWidgets.QMenu("&File")
		self._mnu_file.addAction(self._act_open)
		self._mnu_file.addAction(self._act_quit)

		self._mnu_view = QtWidgets.QMenu("&View")
		self._mnu_view.addAction(self._act_view_list)
		self._mnu_view.addAction(self._act_view_frame)
		self._mnu_view.addAction(self._act_view_script)

		self._wnd_main.menuBar().addMenu(self._mnu_file)
		self._wnd_main.menuBar().addMenu(self._mnu_view)

		self._appearance_presenter.sig_window_rect_changed.connect(self._view_BinAppearanceSettings.setBinRect)

		dock_font = QtWidgets.QDockWidget().font()
		dock_font.setPointSizeF(dock_font.pointSizeF() * 0.8)

		self.dock_displayoptions = QtWidgets.QDockWidget("Bin Display Settings")
		self.dock_displayoptions.setFont(dock_font)
		self.dock_displayoptions.setWidget(QtWidgets.QScrollArea())
		self.dock_displayoptions.widget().setWidgetResizable(True)
		self.dock_displayoptions.widget().setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
		self.dock_displayoptions.widget().setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
		self.dock_displayoptions.widget().setWidget(self._view_BinDisplayItemTypes)

		self._main_bin_contents.sig_request_bin_display.connect(self.dock_displayoptions.show)

		dock_appearance = QtWidgets.QDockWidget("Bin Appearance Settings")
		dock_appearance.setFont(dock_font)
		dock_appearance.setWidget(self._view_BinAppearanceSettings)

		dock_propdefs = QtWidgets.QDockWidget("Property Data")
		dock_propdefs.setFont(dock_font)
		dock_propdefs.setWidget(self._tree_property_data)

		dock_coldefs = QtWidgets.QDockWidget("Column Definitions")
		dock_coldefs.setFont(dock_font)
		dock_coldefs.setWidget(self._tree_column_defs)


		dock_btn_open = QtWidgets.QDockWidget("Options")
		dock_btn_open.setFont(dock_font)
		dock_btn_open.setWidget(self._btn_open)

		dock_sortoptions = QtWidgets.QDockWidget("Bin Sorting")
		dock_sortoptions.setFont(dock_font)
		dock_sortoptions.setWidget(self._tree_sort_properties)

		dock_sift = QtWidgets.QDockWidget("Sift Settings")
		dock_sift.setFont(dock_font)
		dock_sift.setWidget(self._view_binsiftsettings)

		#self._wnd_main.setDockOptions(QtWidgets.QMainWindow.DockOption.)


		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_sortoptions)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_sift)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_propdefs)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_coldefs)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, self.dock_displayoptions)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_appearance)
		self._wnd_main.addDockWidget(QtCore.Qt.DockWidgetArea.RightDockWidgetArea, dock_btn_open)

		if HIDE_DOCK:
			for dock_widget in (dock_sortoptions, dock_sift, dock_propdefs, dock_coldefs, self.dock_displayoptions, dock_appearance, dock_btn_open):
				dock_widget.hide()

		self._wnd_main.show()
	
	@QtCore.Slot(QtGui.QColor, QtGui.QColor)
	def _set_tree_palette(self, fg:QtGui.QColor, bg:QtGui.QColor):

		VARIATION     = 110  # Must be >100 to  have effect
		VARIATION_MID = 105  # Must be >100 to  have effect

		palette = self._main_bin_contents.palette()

		palette.setColor(QtGui.QPalette.ColorRole.Text, fg)
		palette.setColor(QtGui.QPalette.ColorRole.ButtonText, fg)
		palette.setColor(QtGui.QPalette.ColorRole.Base, bg)
		palette.setColor(QtGui.QPalette.ColorRole.AlternateBase, bg.darker(VARIATION))
		palette.setColor(QtGui.QPalette.ColorRole.Button, bg.darker(VARIATION))

		palette.setColor(QtGui.QPalette.ColorRole.Window, bg.darker(VARIATION).darker(VARIATION))
		palette.setColor(QtGui.QPalette.ColorRole.WindowText, fg)
		palette.setColor(QtGui.QPalette.ColorRole.PlaceholderText, bg.lighter(VARIATION).lighter(VARIATION).lighter(VARIATION))


		# Fusion scrollbar uses these colors per https://doc.qt.io/qtforpython-6/PySide6/QtGui/QPalette.html
		# Although it... like... doesn't? lol
		palette.setColor(QtGui.QPalette.ColorRole.Light,    palette.color(QtGui.QPalette.ColorRole.Button).lighter(VARIATION))      # Lighter than Button color
		palette.setColor(QtGui.QPalette.ColorRole.Midlight, palette.color(QtGui.QPalette.ColorRole.Button).lighter(VARIATION_MID))  # Between Button and Light
		palette.setColor(QtGui.QPalette.ColorRole.Mid,      palette.color(QtGui.QPalette.ColorRole.Button).darker(VARIATION_MID))   # Between Button and Dark
		palette.setColor(QtGui.QPalette.ColorRole.Dark,     palette.color(QtGui.QPalette.ColorRole.Button).darker(VARIATION))       # Darker than Button
		
		self._main_bin_contents.setPalette(palette)

	@QtCore.Slot(QtCore.QModelIndex)
	def focusBinColumn(self, index:QtCore.QModelIndex):

		# TODO: Probably re-work

		# Get column name from column defs list
		headers = [self._tree_column_defs.model().headerData(idx, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole) for idx in range(self._tree_column_defs.header().count())]
		#print(headers)

		# Find column index for "Title"
		try:
			idx_name = headers.index("Title")
		except ValueError:
			return
		
		column_name = index.siblingAtColumn(idx_name).data(QtCore.Qt.ItemDataRole.DisplayRole)
		
		#print("Focus on ", column_name)

		
		# Figure out where the column is in bin contents tree
		tree_names = [self._tree_bin_contents.model().headerData(idx,
				QtCore.Qt.Orientation.Horizontal,
				QtCore.Qt.ItemDataRole.DisplayRole
			)
			for idx in range(self._tree_bin_contents.header().count())
		]

		try:
			idx_tree_name = tree_names.index(column_name)
		except ValueError:
			return
		
		selected = self._tree_bin_contents.selectedIndexes()

		selected = selected[0] if selected else self._tree_bin_contents.model().index(0, 0, QtCore.QModelIndex())
		
		self._tree_bin_contents.scrollTo(selected.siblingAtColumn(idx_tree_name), self._tree_bin_contents.ScrollHint.PositionAtCenter)


	
	@QtCore.Slot(object)
	def sortBinContents(self, sorting:list[tuple[QtCore.Qt.SortOrder, str]]):
		
		# Get column names from treeview
		names = []
		for column in range(self._tree_bin_contents.header().count()):
			names.append(self._tree_bin_contents.model().headerData(column, QtCore.Qt.Orientation.Horizontal, QtCore.Qt.ItemDataRole.DisplayRole))

		#print(names)

		for direction, column_name in sorting:
			self._tree_bin_contents.sortByColumnName(column_name, direction)

	def loadBin(self, bin_path:str):
		"""Load the bin in another thread"""


		print(bin_path)
		self._worker = BinViewLoader(bin_path)
		self._worker.signals().sig_begin_loading.connect(lambda: self._wnd_main.setWindowFilePath(bin_path))
		self._worker.signals().sig_begin_loading.connect(lambda: self._wnd_main.setWindowFilePath(bin_path))
		self._worker.signals().sig_begin_loading.connect(self._prog_loading.show)

		self._worker.signals().sig_got_display_options.connect(self._view_BinDisplayItemTypes.setFlags)
		self._worker.signals().sig_got_display_options.connect(self._tree_bin_contents.model().setBinDisplayItemTypes)

		self._worker.signals().sig_got_display_mode.connect(self._main_bin_contents.setDisplayMode)

		self._worker.signals().sig_got_bin_appearance_settings.connect(self._appearance_presenter.setAppearanceSettings)
		
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_column_defs.setWindowTitle(f"{binview.name} | Column Definitions"))
		self._worker.signals().sig_got_view_settings.connect(lambda binview: self._tree_property_data.setWindowTitle(f"{binview.name} | Property Data"))
		
		self._worker.signals().sig_got_view_settings.connect(self._col_defs_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._prop_data_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(self._contents_presenter.setBinView)
		self._worker.signals().sig_got_view_settings.connect(lambda view: self._cmb_bin_view_list.insertItem(0,view.name))
		self._worker.signals().sig_got_view_settings.connect(lambda view: self._cmb_bin_view_list.setCurrentIndex(0))
#		self._worker.signals().sig_got_view_settings.connect(self._main_bin_contents.setBinView)

		self._worker.signals().sig_got_sift_settings.connect(self._sift_presenter.setSiftSettings)

		self._worker.signals().sig_got_sort_settings.connect(self._sorting_presenter.setBinSortingProperties)

		self._worker.signals().sig_got_mob.connect(self._contents_presenter.addMob)

		#self._worker.signals().sig_done_loading.connect(self._tree_bin_contents.resizeAllColumnsToContents)
		self._worker.signals().sig_done_loading.connect(self._tree_column_defs.resizeAllColumnsToContents)
		self._worker.signals().sig_done_loading.connect(self._tree_property_data.resizeAllColumnsToContents)
		self._worker.signals().sig_done_loading.connect(self._tree_sort_properties.resizeAllColumnsToContents)
		
		# Once content is loaded, resize bin columns to fit, then re-apply any custom widths that were lost
		self._worker.signals().sig_done_loading.connect(self._tree_bin_contents.resizeAllColumnsToContents)
		# NOTE: Column widths aren't stored outside of the view model, need to implement
		#self._worker.signals().sig_done_loading.connect(lambda: self._tree_bin_contents.setColumnWidths(self._view_BinAppearanceSettings._tree_column_widths))

		#self._worker.signals().sig_done_loading.connect(lambda: self._tree_bin_contents.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder))
		self._worker.signals().sig_done_loading.connect(lambda: self._tree_column_defs.sortByColumn(0, QtCore.Qt.SortOrder.AscendingOrder))
		self._worker.signals().sig_done_loading.connect(lambda: self._tree_property_data.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder))
		self._worker.signals().sig_done_loading.connect(self._prog_loading.hide)
		self._threadpool.start(self._worker)
	
	@QtCore.Slot()
	def browseForBin(self):

		file_path, _  = QtWidgets.QFileDialog.getOpenFileName(self._btn_open, "Choose an Avid bin...", filter="Avid Bin (*.avb);;All Files (*)", dir=self._wnd_main.windowFilePath())
		if not file_path:
			return
		self.loadBin(file_path)

if __name__ == "__main__":

	
	app = MainApplication()
	app.setStyle("Fusion")

	if len(sys.argv) < 2:
		app.browseForBin()
	else:
		app.loadBin(sys.argv[1])
		
	sys.exit(app.exec())