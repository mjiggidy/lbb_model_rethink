from PySide6 import QtCore, QtGui, QtWidgets

class LBClipColorItemDelegate(QtWidgets.QStyledItemDelegate):

	def __init__(self, *args, **kwargs):

		super().__init__(*args, **kwargs)

		self._margins = QtCore.QMargins(*[4]*4)

		self._aspect_ratio = QtCore.QSize(4,3)

	def sizeHint(self, option:QtWidgets.QStyleOption, index:QtCore.QModelIndex) -> QtCore.QSize:
		orig = super().sizeHint(option, index)
		return QtCore.QSize(orig.height(), orig.height() * (self._aspect_ratio.width()/self._aspect_ratio.height()))

	def paint(self, painter:QtGui.QPainter, option:QtWidgets.QStyleOptionViewItem, index:QtCore.QModelIndex):

		super().paint(painter, option, index)
		painter.save()

		# Center, size and shape the canvas QRect
		canvas = QtCore.QRect(option.rect)
		canvas.setWidth(canvas.height() * (self._aspect_ratio.width()/self._aspect_ratio.height()))
		canvas.moveCenter(option.rect.center())
		canvas = canvas.marginsRemoved(self._margins)
		
		# Draw border and fill
		pen = painter.pen()
		pen.setColor(QtGui.QColor("Black"))
		painter.setPen(pen)

		brush = painter.brush()
		brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern)
		color = index.data(QtCore.Qt.ItemDataRole.UserRole)
		brush.setStyle(QtCore.Qt.BrushStyle.SolidPattern if color.isValid() else QtCore.Qt.BrushStyle.NoBrush)
		brush.setColor(color if color.isValid() else QtGui.QColor())
		painter.setBrush(brush)

		painter.drawRect(canvas)

		# Draw shadow
		canvas.translate(1,1)

		painter.setBrush(QtGui.QBrush(QtCore.Qt.BrushStyle.NoBrush))
		
		pen = painter.pen()
		color = QtGui.QColor("Black")
		color.setAlphaF(0.25)
		pen.setColor(color)
		painter.setPen(pen)

		painter.drawRect(canvas)

		painter.restore()