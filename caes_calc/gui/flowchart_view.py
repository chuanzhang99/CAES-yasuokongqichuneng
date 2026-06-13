"""流程图视图：使用 QGraphicsView/Scene 绘制压缩机、膨胀机、换热器图标。"""

from PyQt5.QtCore import Qt, QRectF, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QGraphicsItem,
    QGraphicsScene,
    QGraphicsView,
    QMessageBox,
)

from caes_calc.config import make_entries
from caes_calc.core.compression import calculate_compression_power
from caes_calc.core.expansion import calculate_expansion_power
from caes_calc.gui.flowchart_dialogs import (
    GeneralConstantsDialog,
    HeatExchangerDialog,
    StageDialog,
    TrainParamsDialog,
)
from caes_calc.gui.flowchart_model import (
    CompressorStage,
    ExpansionStage,
    FlowchartModel,
    HeatExchanger,
    MAX_STAGES,
    ProcessTrain,
    model_to_flat,
)


class InletItem(QGraphicsItem):
    """管线起点，显示入口温度和压力。"""

    WIDTH = 90
    HEIGHT = 75

    def __init__(self, train: ProcessTrain, train_name: str):
        super().__init__()
        self.train = train
        self.train_name = train_name
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setToolTip(f"{train_name}入口参数\n温度: {train.inlet_temperature} ℃\n压力: {train.inlet_pressure} MPa")

    def boundingRect(self):
        return QRectF(0, 0, self.WIDTH, self.HEIGHT + 45)

    def paint(self, painter: QPainter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(QRectF(0, 0, self.WIDTH, self.HEIGHT), QColor("#E5E5EA"))
        painter.setPen(QPen(QColor("#C7C7CC"), 2))
        painter.drawRoundedRect(QRectF(0, 0, self.WIDTH, self.HEIGHT), 10, 10)

        painter.setPen(QColor("#000000"))
        font = QFont("Microsoft YaHei", 9)
        painter.setFont(font)
        painter.drawText(QRectF(0, 8, self.WIDTH, 20), Qt.AlignCenter, "起点")

        font2 = QFont("Microsoft YaHei", 8)
        painter.setFont(font2)
        painter.drawText(QRectF(0, 32, self.WIDTH, 18), Qt.AlignCenter, f"T={self.train.inlet_temperature:.1f}℃")
        painter.drawText(QRectF(0, 50, self.WIDTH, 18), Qt.AlignCenter, f"P={self.train.inlet_pressure:.4f}MPa")

        painter.drawText(QRectF(0, self.HEIGHT + 6, self.WIDTH, 18), Qt.AlignCenter, "入口参数")
        painter.drawText(QRectF(0, self.HEIGHT + 24, self.WIDTH, 18), Qt.AlignCenter, f"时长={self.train.design_duration:.1f}h")

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        dialog = TrainParamsDialog(self.train, self.train_name, QApplication.activeWindow())
        if dialog.exec_() == QDialog.Accepted:
            scene.refresh_from_model()
            scene.model_changed.emit()
        event.accept()


class CompressorItem(QGraphicsItem):
    ICON_WIDTH = 95
    ICON_HEIGHT = 60
    LEFT_MARGIN = 50
    RIGHT_LABEL_WIDTH = 60
    WIDTH = 150 #压缩机输出显示框宽度
    HEIGHT = 60

    def __init__(
        self,
        stage: CompressorStage,
        global_inlet_temp: float,
        global_inlet_pressure: float,
        results: dict = None,
    ):
        super().__init__()
        self.stage = stage
        self.global_inlet_temp = global_inlet_temp
        self.global_inlet_pressure = global_inlet_pressure
        self.results = results or {}
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        # 入口参数（第1级取全局，第2级及以后取本级设定或默认40℃）
        if stage.index == 1:
            self.inlet_temp = global_inlet_temp
            self.inlet_pressure = global_inlet_pressure
        else:
            self.inlet_temp = stage.inlet_temp if stage.inlet_temp is not None else 40.0
            self.inlet_pressure = self.results.get(f"{stage.index}级压缩机入口压力(MPa)")

        # 出口参数
        self.outlet_pressure = self.results.get(f"{stage.index}级压缩机出口压力(MPa)")
        self.outlet_temp = self.results.get(f"{stage.index}级压缩机出口温度（℃）")
        self.power = self.results.get(f"{stage.index}级压缩机轴功率（MW）")

        tooltip = (
            f"第 {stage.index} 级压缩机\n"
            f"压缩比: {stage.ratio}\n"
            f"效率: {stage.efficiency}\n"
            f"入口温度: {self.inlet_temp:.1f} ℃"
        )
        if self.inlet_pressure is not None:
            tooltip += f"\n入口压力: {self.inlet_pressure:.4f} MPa"
        self.setToolTip(tooltip)

    def boundingRect(self):
        return QRectF(-self.LEFT_MARGIN, 0, self.WIDTH, self.HEIGHT + 60)

    def paint(self, painter: QPainter, option, widget):
        # 前大后小的等腰梯形（左大右小）
        path = QPainterPath()
        path.moveTo(0, 0)
        path.lineTo(self.ICON_WIDTH, 10)
        path.lineTo(self.ICON_WIDTH, self.ICON_HEIGHT - 10)
        path.lineTo(0, self.ICON_HEIGHT)
        path.closeSubpath()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(path, QColor("#4A90D9"))
        pen = QPen(QColor("#2C5A8C"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

        # 轴功率显示在图标正中
        if self.power is not None:
            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Microsoft YaHei", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT),
                Qt.AlignCenter,
                f"{self.power:.2f}MW",
            )

        # 左侧：入口压力和温度
        left_x = -self.LEFT_MARGIN + 2
        left_y = self.ICON_HEIGHT / 2 - 12
        painter.setPen(QColor("#000000"))
        font_side = QFont("Microsoft YaHei", 7)
        painter.setFont(font_side)
        if self.inlet_pressure is not None:
            painter.drawText(
                QRectF(left_x, left_y, self.LEFT_MARGIN - 4, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Pin={self.inlet_pressure:.2f}MPa",
            )
        if self.inlet_temp is not None:
            painter.drawText(
                QRectF(left_x, left_y + 14, self.LEFT_MARGIN - 4, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Tin={self.inlet_temp:.1f}℃",
            )

        # 右侧：出口压力和温度
        right_x = self.ICON_WIDTH + 4
        right_y = self.ICON_HEIGHT / 2 - 12
        if self.outlet_pressure is not None:
            painter.drawText(
                QRectF(right_x, right_y, self.RIGHT_LABEL_WIDTH, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{self.outlet_pressure:.2f}MPa",
            )
        if self.outlet_temp is not None:
            painter.drawText(
                QRectF(right_x, right_y + 14, self.RIGHT_LABEL_WIDTH, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"{self.outlet_temp:.2f}℃",
            )

        # 标签（位于图标正下方，按图标宽度居中）
        painter.setPen(QColor("#000000"))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        y = self.ICON_HEIGHT + 8
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 18), Qt.AlignCenter, f"C{self.stage.index}")
        y += 18
        font2 = QFont("Microsoft YaHei", 8)
        painter.setFont(font2)
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 16), Qt.AlignCenter, f"π={self.stage.ratio:.2f}")
        y += 16
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 16), Qt.AlignCenter, f"η={self.stage.efficiency:.2f}")

    def mouseDoubleClickEvent(self, event):
        # 第1级默认入口温度为全局入口温度，第2级及以后默认40℃
        default_temp = self.global_inlet_temp if self.stage.index == 1 else 40.0
        scene = self.scene()
        dialog = StageDialog(
            self.stage,
            scene.model.compression.global_efficiency,
            default_temp,
            "压缩机",
            QApplication.activeWindow(),
        )
        if dialog.exec_() == QDialog.Accepted:
            scene.refresh_from_model()
            scene.model_changed.emit()
        event.accept()


class ExpansionItem(QGraphicsItem):
    ICON_WIDTH = 95
    ICON_HEIGHT = 60
    LEFT_MARGIN = 50
    RIGHT_LABEL_WIDTH = 60
    WIDTH = 150 #膨胀机输出参数框
    HEIGHT = 60

    def __init__(
        self,
        stage: ExpansionStage,
        global_inlet_temp: float,
        global_inlet_pressure: float,
        results: dict = None,
    ):
        super().__init__()
        self.stage = stage
        self.global_inlet_temp = global_inlet_temp
        self.global_inlet_pressure = global_inlet_pressure
        self.results = results or {}
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        # 入口参数（第1级取全局，第2级及以后取本级设定或回退到全局入口温度）
        if stage.index == 1:
            self.inlet_temp = global_inlet_temp
            self.inlet_pressure = global_inlet_pressure
        else:
            self.inlet_temp = stage.inlet_temp if stage.inlet_temp is not None else global_inlet_temp
            self.inlet_pressure = self.results.get(f"{stage.index}级膨胀机入口压力(MPa)")

        # 出口参数
        self.outlet_pressure = self.results.get(f"{stage.index}级膨胀机出口压力(MPa)")
        self.outlet_temp = self.results.get(f"{stage.index}级膨胀机出口温度（℃）")
        self.power = self.results.get(f"{stage.index}级膨胀机轴功率（MW）")

        tooltip = (
            f"第 {stage.index} 级膨胀机\n"
            f"膨胀比: {stage.ratio}\n"
            f"效率: {stage.efficiency}\n"
            f"入口温度: {self.inlet_temp:.1f} ℃"
        )
        if self.inlet_pressure is not None:
            tooltip += f"\n入口压力: {self.inlet_pressure:.4f} MPa"
        self.setToolTip(tooltip)

    def boundingRect(self):
        return QRectF(-self.LEFT_MARGIN, 0, self.WIDTH, self.HEIGHT + 60)

    def paint(self, painter: QPainter, option, widget):
        # 前小后大的等腰梯形（左小右大）
        path = QPainterPath()
        path.moveTo(0, 10)
        path.lineTo(self.ICON_WIDTH, 0)
        path.lineTo(self.ICON_WIDTH, self.ICON_HEIGHT)
        path.lineTo(0, self.ICON_HEIGHT - 10)
        path.closeSubpath()

        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillPath(path, QColor("#E74C3C"))
        pen = QPen(QColor("#9B2C22"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPath(path)

        # 轴功率显示在图标正中
        if self.power is not None:
            painter.setPen(QColor("#FFFFFF"))
            font = QFont("Microsoft YaHei", 9, QFont.Bold)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, 0, self.ICON_WIDTH, self.ICON_HEIGHT),
                Qt.AlignCenter,
                f"{self.power:.2f}MW",
            )

        # 左侧：入口压力和温度
        left_x = -self.LEFT_MARGIN + 2
        left_y = self.ICON_HEIGHT / 2 - 12
        painter.setPen(QColor("#000000"))
        font_side = QFont("Microsoft YaHei", 7)
        painter.setFont(font_side)
        if self.inlet_pressure is not None:
            painter.drawText(
                QRectF(left_x, left_y, self.LEFT_MARGIN - 4, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Pi={self.inlet_pressure:.2f}MPa",
            )
        if self.inlet_temp is not None:
            painter.drawText(
                QRectF(left_x, left_y + 14, self.LEFT_MARGIN - 4, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Ti={self.inlet_temp:.1f}℃",
            )

        # 右侧：出口压力和温度
        right_x = self.ICON_WIDTH + 4
        right_y = self.ICON_HEIGHT / 2 - 12
        if self.outlet_pressure is not None:
            painter.drawText(
                QRectF(right_x, right_y, self.RIGHT_LABEL_WIDTH, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Po={self.outlet_pressure:.2f}MPa",
            )
        if self.outlet_temp is not None:
            painter.drawText(
                QRectF(right_x, right_y + 14, self.RIGHT_LABEL_WIDTH, 14),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"To={self.outlet_temp:.2f}℃",
            )

        # 标签（位于图标正下方，按图标宽度居中）
        painter.setPen(QColor("#000000"))
        font = QFont("Microsoft YaHei", 10)
        painter.setFont(font)
        y = self.ICON_HEIGHT + 8
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 18), Qt.AlignCenter, f"E{self.stage.index}")
        y += 18
        font2 = QFont("Microsoft YaHei", 8)
        painter.setFont(font2)
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 16), Qt.AlignCenter, f"π={self.stage.ratio:.2f}")
        y += 16
        painter.drawText(QRectF(0, y, self.ICON_WIDTH, 16), Qt.AlignCenter, f"η={self.stage.efficiency:.2f}")

    def mouseDoubleClickEvent(self, event):
        scene = self.scene()
        dialog = StageDialog(
            self.stage,
            scene.model.expansion.global_efficiency,
            self.global_inlet_temp,
            "膨胀机",
            QApplication.activeWindow(),
        )
        if dialog.exec_() == QDialog.Accepted:
            scene.refresh_from_model()
            scene.model_changed.emit()
        event.accept()


class HeatExchangerItem(QGraphicsItem):
    WIDTH = 28
    HEIGHT = 55

    def __init__(self, hx: HeatExchanger):
        super().__init__()
        self.hx = hx
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        name = "冷却器" if hx.hx_type == "cooler" else "加热器"
        self.setToolTip(name)

    def boundingRect(self):
        return QRectF(0, 0, self.WIDTH, self.HEIGHT + 24)

    def paint(self, painter: QPainter, option, widget):
        color = QColor("#5DADE2") if self.hx.hx_type == "cooler" else QColor("#F39C12")
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(QRectF(0, 0, self.WIDTH, self.HEIGHT), color)
        painter.setPen(QPen(QColor("#2C3E50"), 2))
        painter.drawRect(QRectF(0, 0, self.WIDTH, self.HEIGHT))

        # 中间折线（原来的锯齿形）
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        y = 8
        while y + 10 <= self.HEIGHT - 8:
            painter.drawLine(4, y, self.WIDTH - 4, y + 5)
            painter.drawLine(self.WIDTH - 4, y + 5, 4, y + 10)
            y += 10

        # 标签
        painter.setPen(QColor("#000000"))
        font = QFont("Microsoft YaHei", 8)
        painter.setFont(font)
        painter.drawText(QRectF(0, self.HEIGHT + 4, self.WIDTH, 18), Qt.AlignCenter, "HX")

    def mouseDoubleClickEvent(self, event):
        dialog = HeatExchangerDialog(self.hx, QApplication.activeWindow())
        dialog.exec_()
        event.accept()


class FlowchartScene(QGraphicsScene):
    ITEM_SPACING = 60
    START_X = 30
    COMPRESSION_Y = 60
    EXPANSION_Y = 240

    model_changed = pyqtSignal()
    content_width_changed = pyqtSignal(int)

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.row_items = []
        self._rebuild()

    def set_model(self, model):
        self.model = model
        self._rebuild()

    def refresh_from_model(self):
        self._rebuild()

    def _rebuild(self):
        self.clear()
        self.row_items = []

        flat = model_to_flat(self.model)
        entries = make_entries(flat)
        try:
            compression_results = calculate_compression_power(entries)
        except Exception:
            compression_results = {}
        try:
            expansion_results = calculate_expansion_power(entries)
        except Exception:
            expansion_results = {}

        comp_items = self._layout_train(
            self.model.compression,
            self.COMPRESSION_Y,
            CompressorItem,
            "压缩机",
            compression_results,
        )
        exp_items = self._layout_train(
            self.model.expansion,
            self.EXPANSION_Y,
            ExpansionItem,
            "膨胀机",
            expansion_results,
        )

        self.row_items.extend(comp_items)
        self.row_items.extend(exp_items)

        max_x = 0
        for item in comp_items + exp_items:
            right = item.x() + item.boundingRect().right()
            if right > max_x:
                max_x = right
        self.content_width_changed.emit(int(max_x + self.START_X))

    def _layout_train(self, train: ProcessTrain, y_base: int, item_class, train_name: str, results: dict):
        """按顺序排布 Inlet -> HX_before -> Stage_1 -> HX_between -> Stage_2 -> ... -> HX_after。

        每个图元之间的水平间距统一为 ITEM_SPACING（从上一个图元的右边界到下一个图元原点）。
        """
        items = []
        x = self.START_X

        def _place(item, y_offset=0):
            nonlocal x
            item.setPos(x, y_base + y_offset)
            self.addItem(item)
            items.append(item)
            x += item.boundingRect().right() + self.ITEM_SPACING

        # 起点参数图标
        _place(InletItem(train, train_name))

        # 按 index 排序换热器
        hx_by_index = {hx.index: hx for hx in train.heat_exchangers}

        # 先画第 1 级前的换热器（index=0）
        if 0 in hx_by_index:
            _place(HeatExchangerItem(hx_by_index[0]), y_offset=5)

        for i, stage in enumerate(train.stages):
            _place(item_class(stage, train.inlet_temperature, train.inlet_pressure, results))

            # 该级之后的换热器（index=i+1）
            if i + 1 in hx_by_index:
                _place(HeatExchangerItem(hx_by_index[i + 1]), y_offset=5)

        return items

    def contextMenuEvent(self, event):
        # 禁用右键菜单，改为工具栏按钮操作
        event.accept()

    def _add_compressor_stage(self):
        self._add_stage(self.model.compression, CompressorStage, "cooler")

    def _add_turbine_stage(self):
        self._add_stage(self.model.expansion, ExpansionStage, "heater")

    def _add_stage(self, train: ProcessTrain, stage_class, hx_type: str):
        if len(train.stages) >= MAX_STAGES:
            QMessageBox.warning(None, "提示", f"最多支持 {MAX_STAGES} 级")
            return
        old_last = len(train.stages)
        new_index = old_last + 1
        stage = stage_class(
            index=new_index,
            ratio=1.0,
            efficiency=train.global_efficiency,
            inlet_temp=None,
        )
        train.stages.append(stage)

        if new_index > 1:
            # 查找是否已有 after_last 换热器
            after_last_hx = None
            for hx in train.heat_exchangers:
                if hx.position == "after_last":
                    after_last_hx = hx
                    break
            if after_last_hx is not None:
                # 把原来的 after_last 改成级间换热器
                after_last_hx.position = "between"
                after_last_hx.index = old_last
                # 新增最后一级后的换热器
                train.heat_exchangers.append(HeatExchanger(position="after_last", index=new_index, hx_type=hx_type))
            else:
                train.heat_exchangers.append(HeatExchanger(position="between", index=old_last, hx_type=hx_type))

        train.heat_exchangers.sort(key=lambda h: (h.position != "before_first", h.index))
        self._rebuild()
        self.model_changed.emit()

    def _remove_stage(self, stage, train: ProcessTrain):
        idx = stage.index
        train.stages.pop(idx - 1)
        # 重排编号
        for i, s in enumerate(train.stages, start=1):
            s.index = i
        # 删除与该级相关的换热器，并重排换热器 index
        new_hxs = []
        for hx in train.heat_exchangers:
            if hx.position == "between":
                if hx.index == idx - 1 or hx.index == idx:
                    continue
                new_index = hx.index
                if new_index >= idx:
                    new_index -= 1
                new_hxs.append(HeatExchanger(position="between", index=new_index, hx_type=hx.hx_type))
            else:
                new_hxs.append(hx)
        # 修正 after_last 的 index
        final_hxs = []
        for hx in new_hxs:
            if hx.position == "after_last":
                hx.index = len(train.stages)
            final_hxs.append(hx)
        train.heat_exchangers = final_hxs
        self._rebuild()
        self.model_changed.emit()

    def _remove_last_stage(self, train: ProcessTrain):
        if not train.stages:
            QMessageBox.warning(None, "提示", "当前没有可删除的级")
            return
        self._remove_stage(train.stages[-1], train)

    def edit_general_constants(self):
        parent = QApplication.activeWindow()
        dialog = GeneralConstantsDialog(self.model.globals, parent)
        if dialog.exec_() == QDialog.Accepted:
            self.model.globals = dialog.get_globals()
            self.refresh_from_model()
            self.model_changed.emit()


class FlowchartView(QGraphicsView):
    def __init__(self, model=None, parent=None):
        # uic.loadUi 实例化时会以父窗口作为第一个位置参数传入，需要做兼容
        if model is not None and not isinstance(model, FlowchartModel):
            parent = model
            model = None
        super().__init__(parent)
        if model is None:
            model = FlowchartModel(
                compression=ProcessTrain(),
                expansion=ProcessTrain(),
            )
        self.scene = FlowchartScene(model, parent=self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMinimumHeight(420)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("background-color: #F2F2F7; border: none;")

    def set_model(self, model):
        self.scene.set_model(model)
