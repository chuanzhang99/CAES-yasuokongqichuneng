"""PyQt5 主窗口，替代原 tkinter 实现。"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from caes_calc import __author__, __contact__, __version__
from caes_calc.calculations import run_all_calculations
from caes_calc.gui.flowchart_model import flat_to_model, model_to_flat
from caes_calc.gui.flowchart_view import FlowchartView
from caes_calc.gui.styles import get_ios_stylesheet
from caes_calc.persistence import load_inputs, save_inputs
from caes_calc.validation import validate


# 结果区域标题
SECTION_TITLES = {
    "compression": "压缩机计算结果",
    "expansion": "膨胀机计算结果",
    "thermal": "导热油与盐穴计算结果",
    "system": "系统汇总",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("非补燃压缩空气储能参数计算")
        self.setMinimumSize(1200, 900)
        self.resize(1200, 900)

        self.result_tables = {}
        self.flowchart_model = None

        self._load_inputs()
        self._build_ui()

    def _load_inputs(self):
        self.current_data = load_inputs("data")

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # iOS 大标题
        title = QLabel("非补燃压缩空气储能")
        title.setObjectName("titleLabel")
        layout.addWidget(title)

        subtitle = QLabel("参数计算与流程图")
        subtitle.setStyleSheet("font-size: 18px; color: #3C3C4399; background-color: transparent; padding-bottom: 8px;")
        layout.addWidget(subtitle)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)

        self.result_tab = self._build_result_tab()
        self.flowchart_tab = self._build_flowchart_tab()
        self.tabs.addTab(self.flowchart_tab, "流程图")
        self.tabs.addTab(self.result_tab, "结果汇总")

        # 按钮栏
        layout.addLayout(self._build_button_bar())

    def _build_result_tab(self) -> QWidget:
        tab = QWidget()
        layout = QGridLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(12, 12, 12, 12)

        sections = ["compression", "expansion", "thermal", "system"]
        positions = [(0, 0), (0, 1), (1, 0), (1, 1)]

        for section, (row, col) in zip(sections, positions):
            group = QGroupBox(SECTION_TITLES[section])
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(8, 12, 8, 8)

            table = QTableWidget()
            table.setColumnCount(2)
            table.setHorizontalHeaderLabels(["参数", "值"])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionBehavior(QTableWidget.SelectRows)
            table.setMinimumHeight(240)
            table.setShowGrid(False)

            group_layout.addWidget(table)
            layout.addWidget(group, row, col)
            self.result_tables[section] = table

        return tab

    def _build_flowchart_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 工具栏
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        btn_add_comp = QPushButton("+ 压缩机级")
        btn_add_comp.setFixedSize(120, 34)
        btn_add_comp.clicked.connect(self._on_add_compressor_stage)

        btn_rem_comp = QPushButton("- 压缩机级")
        btn_rem_comp.setObjectName("dangerButton")
        btn_rem_comp.setFixedSize(120, 34)
        btn_rem_comp.clicked.connect(self._on_remove_compressor_stage)

        btn_add_exp = QPushButton("+ 膨胀机级")
        btn_add_exp.setFixedSize(120, 34)
        btn_add_exp.clicked.connect(self._on_add_expansion_stage)

        btn_rem_exp = QPushButton("- 膨胀机级")
        btn_rem_exp.setObjectName("dangerButton")
        btn_rem_exp.setFixedSize(120, 34)
        btn_rem_exp.clicked.connect(self._on_remove_expansion_stage)

        btn_constants = QPushButton("通用常数")
        btn_constants.setObjectName("secondaryButton")
        btn_constants.setFixedSize(120, 34)
        btn_constants.clicked.connect(self._on_edit_constants)

        toolbar.addWidget(btn_add_comp)
        toolbar.addWidget(btn_rem_comp)
        toolbar.addWidget(btn_add_exp)
        toolbar.addWidget(btn_rem_exp)
        toolbar.addStretch()
        toolbar.addWidget(btn_constants)
        layout.addLayout(toolbar)

        # 流程图视图
        self.flowchart_model = flat_to_model(self.current_data)
        self.flowchart_view = FlowchartView(self.flowchart_model)
        self.flowchart_view.scene.model_changed.connect(self._save_model)
        self.flowchart_view.scene.model_changed.connect(self._recalculate)
        self.flowchart_view.scene.content_width_changed.connect(self._on_flowchart_width_changed)
        layout.addWidget(self.flowchart_view)

        # 程序启动时自动计算一次
        self._recalculate()

        # 提示标签
        hint = QLabel(
            "提示：双击起点编辑系统参数，双击压缩机/膨胀机编辑级参数；"
            "使用上方按钮增删级数。"
        )
        hint.setStyleSheet("color: #8E8E93; font-size: 14px; background-color: transparent;")
        layout.addWidget(hint)

        return tab

    def _build_button_bar(self):
        bar = QHBoxLayout()
        bar.setSpacing(12)
        bar.setContentsMargins(0, 8, 0, 0)

        btn_check = QPushButton("检查数据")
        btn_check.setObjectName("secondaryButton")
        btn_check.setFixedSize(120, 40)
        btn_check.clicked.connect(self.on_check)

        btn_export = QPushButton("导出到文件")
        btn_export.setObjectName("secondaryButton")
        btn_export.setFixedSize(120, 40)
        btn_export.clicked.connect(self.on_export)

        btn_instructions = QPushButton("使用说明")
        btn_instructions.setObjectName("secondaryButton")
        btn_instructions.setFixedSize(100, 40)
        btn_instructions.clicked.connect(self.show_instructions)

        btn_version = QPushButton("版本信息")
        btn_version.setObjectName("secondaryButton")
        btn_version.setFixedSize(100, 40)
        btn_version.clicked.connect(self.show_version_info)

        bar.addStretch()
        bar.addWidget(btn_check)
        bar.addWidget(btn_export)
        bar.addWidget(btn_instructions)
        bar.addWidget(btn_version)
        bar.addStretch()

        # 作者标签
        author_label = QLabel(f"作者: {__author__}，一个喜欢写代码的电气工程师。")
        author_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        author_label.setStyleSheet("color: #8E8E93; font-size: 14px; background-color: transparent;")
        bar.addWidget(author_label)

        return bar

    def _on_add_compressor_stage(self):
        self.flowchart_view.scene._add_compressor_stage()

    def _on_remove_compressor_stage(self):
        self.flowchart_view.scene._remove_last_stage(self.flowchart_view.scene.model.compression)

    def _on_add_expansion_stage(self):
        self.flowchart_view.scene._add_turbine_stage()

    def _on_remove_expansion_stage(self):
        self.flowchart_view.scene._remove_last_stage(self.flowchart_view.scene.model.expansion)

    def _on_edit_constants(self):
        self.flowchart_view.scene.edit_general_constants()

    def _save_model(self):
        inputs = model_to_flat(self.flowchart_model)
        save_inputs(inputs, "data")

    def _on_flowchart_width_changed(self, width: int):
        margins = 100
        new_width = max(width + margins, 900)
        self.setMinimumWidth(new_width)
        self.resize(new_width, self.height())

    def _populate_results(self, results: dict):
        for section, data in results.items():
            table = self.result_tables[section]
            table.setRowCount(len(data))
            for row, (param, value) in enumerate(data.items()):
                table.setItem(row, 0, table.item(row, 0) or QTableWidgetItem())
                table.setItem(row, 1, table.item(row, 1) or QTableWidgetItem())
                table.item(row, 0).setText(str(param))
                table.item(row, 1).setText(str(value))

    def _recalculate(self):
        """根据当前流程图模型自动计算并刷新结果汇总。"""
        inputs = model_to_flat(self.flowchart_model)
        results = run_all_calculations(inputs)
        self._populate_results(results)

    def on_check(self):
        inputs = model_to_flat(self.flowchart_model)
        warnings = validate(inputs)

        if warnings:
            QMessageBox.information(self, "数据检查结果", "\n\n".join(warnings))
        else:
            QMessageBox.information(self, "结果", "所有计算值均在预期范围内")

    def on_export(self):
        inputs = model_to_flat(self.flowchart_model)
        results = run_all_calculations(inputs)

        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存计算结果", "result.txt", "Text files (*.txt);;All files (*.*)"
        )
        if not filepath:
            return

        with open(filepath, "w", encoding="utf-8") as file:
            for section, title in SECTION_TITLES.items():
                file.write(f"{title}\n")
                file.write("参数,值\n")
                for param, val in results[section].items():
                    file.write(f"{param},{val}\n")
                file.write("\n")

        QMessageBox.information(self, "导出成功", f"结果已保存到：\n{filepath}")

    def show_instructions(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("使用说明")
        dialog.setIcon(QMessageBox.Information)
        text = (
            "1、本程序由四川省非金属（盐业）地质调查研究所开发，用于计算非补燃压缩空气储能相关参数的免费软件。\n\n"
            "2、盐穴的承压能力受盐穴的深度、盖层和形状等多方面的影响，需采用专业探测手段和试验确定。\n\n"
            "3、详细咨询盐穴储能相关事宜，敬请垂询0813-5591996。\n\n"
            "4、程序运行后会生成一个data文件夹用于保存输入参数，需要恢复默认值只用删除该文件夹内的文本文件即可。\n\n"
            "5、通过调整[注入空气流量]这个参数，就能估算出发电能力。\n\n"
            "6、适当调整盐穴[储能压力上限]和[释放截止压力]，配合注入空气流量，就能估算出需求的盐穴有效容积。\n\n"
            "7、本程序计算结果仅供参考。"
        )
        dialog.setText(text)
        dialog.exec_()

    def show_version_info(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("版本信息")
        dialog.setIcon(QMessageBox.Information)
        text = (
            f"当前版本：{__version__}\n"
            f"bug反馈邮箱：{__contact__}\n\n"
            "【1.0.1 → 2.0.0 更新概要】\n\n"
            "一、界面与交互\n"
            "1、从 tkinter 全面迁移到 PyQt5，采用 iOS 风格样式与高清屏适配。\n"
            "2、新增可视化流程图编辑页，可在图上直接增删压缩机/膨胀机级数和换热器。\n"
            "3、双击图标即可编辑单级参数；入口/出口压力、温度、轴功率直接显示在图标上。\n"
            "4、主窗口宽度随流程图级数自动伸缩。\n\n"
            "二、计算模型\n"
            "1、取消“多级压缩机入口空气温度”全局常数，改为逐级读取入口温度（第1级默认15℃，后续默认40℃）。\n"
            "2、压缩机、膨胀机、导热油、盐穴体积等计算结果与流程图实时联动。\n"
            "3、导热油需求量按实际配置的换热器逐个计算。\n\n"
            "三、数据检查\n"
            "新增并完善了十余项校验：\n"
            "· 发电导油量不超过储能导油量\n"
            "· 冷却器油温不高于下级压缩机入口气温\n"
            "· 加热器油温不低于下级膨胀机入口气温\n"
            "· 膨胀机出口压力不低于第一级压缩机入口压力\n"
            "· 盐穴设计压力合理性等\n\n"
            "四、工程化\n"
            "1、GUI 与 CLI 分离，新增 cli.py，支持 --check 和 --export。\n"
            "2、输入参数统一保存在 data/ 目录，删除该目录即可恢复默认值。\n"
            "3、修复了双击编辑、右键菜单、计算结果展示等若干稳定性问题。"
        )
        dialog.setText(text)
        dialog.exec_()


def main():
    # 启用 Windows 高 DPI 缩放支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 应用 iOS 风格样式表
    app.setStyleSheet(get_ios_stylesheet())

    # 设置全局字体
    font = QFont("Microsoft YaHei", 11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
