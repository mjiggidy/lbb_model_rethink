import sys, functools
import avb, avbutils
from PySide6 import QtCore, QtGui, QtWidgets

class BinDisplayOptionsView(QtWidgets.QWidget):

	sig_option_toggled  = QtCore.Signal(object, bool)
	sig_options_changed = QtCore.Signal(object)

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self.setLayout(QtWidgets.QGridLayout())
		self.layout().setSpacing(0)
		self.layout().setContentsMargins(0,0,0,0)

		self._option_mappings:dict[avbutils.BinDisplayOptions, QtWidgets.QCheckBox] = dict()

		for option in avbutils.BinDisplayOptions:

			chk_option = QtWidgets.QCheckBox(text=option.name.replace("_"," ").title())
			chk_option.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
			self._option_mappings[option] = chk_option
			self.layout().addWidget(chk_option)
		
	@QtCore.Slot(QtCore.Qt.CheckState)
	def what(self, state:QtCore.Qt.CheckState):
		print(state)
	
	@QtCore.Slot(object)
	def _optionToggled(self, option:avbutils.BinDisplayOptions):
		print(option)
	
	def setOptions(self, options:avbutils.BinDisplayOptions):
		"""Set all options from a given `avbutils.BinDisplayOptions` enum"""

		for option in self._option_mappings:
			self.setOption(option, option in options)
	
	def setOption(self, option:avbutils.BinDisplayOptions, is_enabled:bool):
		"""Toggle a single option"""

		if not len(option) == 1:
			raise ValueError("Only one option is allowed.  Use setOptions() for multiple flags.")

		self._option_mappings[option].setChecked(is_enabled)




class BinDisplayApp(QtWidgets.QApplication):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


if __name__ == "__main__":

	if not len(sys.argv) > 1:
		sys.exit(f"Usage: {__file__} bin_path.avb")

	app = BinDisplayApp()

	wdg_options = BinDisplayOptionsView()
	wdg_options.show()
	
	with avb.open(sys.argv[1]) as bin_handle:
		display_options = avbutils.BinDisplayOptions.get_options_from_bin(bin_handle.content)
		wdg_options.setOptions(display_options)
	
	print(list(display_options))

	sys.exit(app.exec())
	
