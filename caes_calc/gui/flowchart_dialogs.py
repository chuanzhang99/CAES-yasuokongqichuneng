"""流程图双击弹出的参数编辑对话框。"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)


class StageDialog(QDialog):
    """压缩机/膨胀机级参数编辑对话框。"""

    def __init__(
        self,
        stage,
        global_efficiency: float,
        global_inlet_temp: float,
        stage_type: str = "压缩机",
        parent=None,
    ):
        super().__init__(parent)
        self.stage = stage
        self.global_efficiency = global_efficiency
        self.global_inlet_temp = global_inlet_temp
        self.stage_type = stage_type
        ratio_name = "压缩比" if stage_type == "压缩机" else "膨胀比"
        self.setWindowTitle(f"编辑第 {stage.index} 级{stage_type}")
        self.resize(320, 220)
        self.setMinimumSize(280, 200)

        layout = QFormLayout(self)

        self.ratio_edit = QLineEdit(str(stage.ratio))
        self.eff_edit = QLineEdit(str(stage.efficiency))
        self.eff_edit.setPlaceholderText(f"默认 {global_efficiency}")
        self.temp_edit = QLineEdit(str(stage.inlet_temp) if stage.inlet_temp is not None else "")
        self.temp_edit.setPlaceholderText(f"默认 {global_inlet_temp}")

        layout.addRow(f"{ratio_name}:", self.ratio_edit)
        layout.addRow("效率:", self.eff_edit)
        layout.addRow("入口温度(℃):", self.temp_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _on_accept(self):
        try:
            ratio = float(self.ratio_edit.text())
            eff_text = self.eff_edit.text().strip()
            efficiency = float(eff_text) if eff_text else self.global_efficiency
            temp_text = self.temp_edit.text().strip()
            inlet_temp = float(temp_text) if temp_text else None
            if ratio <= 0:
                raise ValueError(f"{self.stage_type}比必须大于 0")
            if efficiency <= 0 or efficiency > 1:
                raise ValueError("效率应在 0~1 之间")
            if inlet_temp is not None and inlet_temp < -273.15:
                raise ValueError("入口温度不能低于绝对零度")
            self.stage.ratio = ratio
            self.stage.efficiency = efficiency
            self.stage.inlet_temp = inlet_temp
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", str(e))


class HeatExchangerDialog(QDialog):
    def __init__(self, hx, parent=None):
        super().__init__(parent)
        self.hx = hx
        self.setWindowTitle("换热器")
        self.resize(320, 150)
        self.setMinimumSize(260, 130)

        layout = QVBoxLayout(self)

        type_name = "冷却器" if hx.hx_type == "cooler" else "加热器"
        if hx.position == "before_first":
            pos_text = f"第 1 级{type_name}之前"
        elif hx.position == "after_last":
            pos_text = f"最后 1 级{type_name}之后"
        else:
            pos_text = f"第 {hx.index} 级与第 {hx.index + 1} 级之间"

        layout.addWidget(QLabel(f"类型: {type_name}"))
        layout.addWidget(QLabel(f"位置: {pos_text}"))

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addStretch()
        layout.addWidget(btn_box)


class TrainParamsDialog(QDialog):
    """编辑某一条工艺管线的系统级参数。"""

    def __init__(self, train, train_name: str, parent=None):
        super().__init__(parent)
        self.train = train
        self.train_name = train_name
        self.setWindowTitle(f"{train_name}系统参数")
        self.resize(380, 450)
        self.setMinimumSize(320, 360)

        layout = QFormLayout(self)

        self.inlet_temp_edit = QLineEdit(str(train.inlet_temperature))
        self.inlet_pressure_edit = QLineEdit(str(train.inlet_pressure))
        self.design_duration_edit = QLineEdit(str(train.design_duration))
        self.oil_inlet_edit = QLineEdit(str(train.oil_inlet_temp))
        self.oil_outlet_edit = QLineEdit(str(train.oil_outlet_temp))
        self.global_eff_edit = QLineEdit(str(train.global_efficiency))

        layout.addRow("入口空气温度(℃):", self.inlet_temp_edit)
        layout.addRow("进口气压(MPa):", self.inlet_pressure_edit)
        layout.addRow("设计时长(h):", self.design_duration_edit)
        layout.addRow("导热油入口温度(℃):", self.oil_inlet_edit)
        layout.addRow("导热油出口温度(℃):", self.oil_outlet_edit)
        layout.addRow("级效率(默认):", self.global_eff_edit)

        if train_name == "压缩机":
            self.limit_pressure_edit = QLineEdit(str(train.max_pressure))
            self.aux_eff_edit = QLineEdit(str(train.motor_efficiency))
            self.air_flow_edit = QLineEdit(str(getattr(train, "air_mass_flow", 0)))
            layout.addRow("储能压力上限(MPa):", self.limit_pressure_edit)
            layout.addRow("储能电动机效率(%):", self.aux_eff_edit)
            layout.addRow("注入空气流量(t/h):", self.air_flow_edit)
        else:
            self.limit_pressure_edit = QLineEdit(str(train.min_pressure))
            self.aux_eff_edit = QLineEdit(str(train.generator_efficiency))
            layout.addRow("释放截止压力(MPa):", self.limit_pressure_edit)
            layout.addRow("发电机效率(%):", self.aux_eff_edit)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _on_accept(self):
        try:
            self.train.inlet_temperature = float(self.inlet_temp_edit.text())
            self.train.inlet_pressure = float(self.inlet_pressure_edit.text())
            self.train.design_duration = float(self.design_duration_edit.text())
            self.train.oil_inlet_temp = float(self.oil_inlet_edit.text())
            self.train.oil_outlet_temp = float(self.oil_outlet_edit.text())
            self.train.global_efficiency = float(self.global_eff_edit.text())
            limit = float(self.limit_pressure_edit.text())
            aux = float(self.aux_eff_edit.text())
            if self.train_name == "压缩机":
                self.train.max_pressure = limit
                self.train.motor_efficiency = aux
                self.train.air_mass_flow = float(self.air_flow_edit.text())
            else:
                self.train.min_pressure = limit
                self.train.generator_efficiency = aux
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"请输入有效数字: {e}")


class GeneralConstantsDialog(QDialog):
    """编辑通用常数。"""

    def __init__(self, globals_dict: dict, parent=None):
        super().__init__(parent)
        self.globals_dict = dict(globals_dict)
        self.setWindowTitle("通用常数")
        self.resize(460, 520)
        self.setMinimumSize(360, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)

        self.edits = {}
        # 按字母顺序展示，方便查找
        for key in sorted(self.globals_dict.keys()):
            edit = QLineEdit(str(self.globals_dict[key]))
            edit.setMinimumWidth(180)
            self.edits[key] = edit
            form.addRow(key + ":", edit)

        layout.addLayout(form)
        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self._on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _on_accept(self):
        for key, edit in self.edits.items():
            self.globals_dict[key] = edit.text().strip()
        self.accept()

    def get_globals(self) -> dict:
        return self.globals_dict
