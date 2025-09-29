from PySide6 import QtCore, QtGui, QtWidgets
import avbutils, enum		

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
			#chk_option.setChecked(bool(initial_values & option))
			
			chk_option.clicked.connect(lambda is_checked, option=option:self._option_changed(option, is_checked))
			
			self._option_mappings[option] = chk_option

		self.updateCheckStates()
		
	@QtCore.Slot(object)
	def _option_changed(self, option:enum.Flag, is_enabled:bool):

		self.sig_flag_toggled.emit(option, is_enabled)

		if is_enabled:
			self._flags |= option
		else:
			self._flags &= ~option

		self.sig_flags_changed.emit(self.flags())
	
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
		self.layout().setContentsMargins(0,0,0,0)

		grp_clips = QtWidgets.QGroupBox()

		grp_clips.setLayout(QtWidgets.QVBoxLayout())
		
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.MASTER_CLIPS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.LINKED_MASTER_CLIPS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.SUBCLIPS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.SEQUENCES])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.SOURCES])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.EFFECTS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.MOTION_EFFECTS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.PRECOMP_RENDERED_EFFECTS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.PRECOMP_TITLES_MATTEKEYS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.GROUPS])
		grp_clips.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.STEREOSCOPIC_CLIPS])

		self.layout().addWidget(grp_clips)

		grp_origins = QtWidgets.QGroupBox()

		grp_origins.setLayout(QtWidgets.QVBoxLayout())
		grp_origins.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.SHOW_CLIPS_CREATED_BY_USER])
		grp_origins.layout().addWidget(self._option_mappings[avbutils.BinDisplayItemTypes.SHOW_REFERENCE_CLIPS])

		self.layout().addWidget(grp_origins)

		self.layout().addStretch()


if __name__ == "__main__":

	import sys

	app = QtWidgets.QApplication()

	test = avbutils.BinDisplayItemTypes.MASTER_CLIPS|avbutils.BinDisplayItemTypes.SUBCLIPS

	wdg_bindisplay = BinDisplayItemTypesView(test)
	wdg_bindisplay.setFlags(avbutils.BinDisplayItemTypes.default_options())
	wdg_bindisplay.show()
	wdg_bindisplay.sig_flags_changed.connect(print)
	print(wdg_bindisplay.flags())

	sys.exit(app.exec())