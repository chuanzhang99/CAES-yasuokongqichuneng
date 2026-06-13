"""默认参数、路径和字符串适配器。

计算核心原本依赖 GUI Entry 控件的 .get() 方法。通过 make_entries 把普通字符串字典
包装成具有 .get() 的对象，计算函数无需修改即可同时服务于 GUI、CLI 和单元测试。
"""

import os
from typing import Dict


class _StringEntry:
    """模拟 tkinter Entry / QLineEdit 的 .get() 行为，但只保存字符串。"""

    def __init__(self, value: str):
        self._value = str(value)

    def get(self) -> str:
        return self._value


def make_entries(raw_dict: Dict[str, str]) -> Dict[str, _StringEntry]:
    """把 {label: value_str} 转换成计算函数可用的 entries 字典。"""
    return {k: _StringEntry(v) for k, v in raw_dict.items()}


DATA_DIR = os.path.join(os.getcwd(), "data")

DEFAULT_VARIABLE_ENTRIES = {
    "压缩机入口空气温度 (℃)": "15",
    "进口空气气压 (MPa)": "0.1015",
    "储能设计时长 (h)": "8",
    "储能压力上限 (MPa)": "17.5",
    "压缩时导热油入口温度(℃)": "25",
    "压缩时导热油出口温度(℃)": "350",
    "压缩机效率 (%)": "0.85",
    "储能电动机效率 (%)": "0.96",
    "压缩前冷却器": "0",
    "压缩后冷却器": "0",
    "1级压缩机压缩比": "14.0",
    "2级压缩机压缩比": "8.5",
    "3级压缩机压缩比": "1.4489",
    "4级压缩机压缩比": "0",
    "5级压缩机压缩比": "0",
}

DEFAULT_MIDDLE_ENTRIES = {
    "膨胀机入口空气温度 (℃)": "345",
    "膨胀机进口气压 (MPa)": "17.5",
    "发电设计时长 (h)": "5",
    "释放截止压力 (MPa)": "14.5",
    "膨胀时导热油入口温度(℃)": "346",
    "膨胀时导热油出口温度(℃)": "75",
    "膨胀机效率 (%)": "0.9",
    "发电机效率 (%)": "0.98",
    "膨胀前加热器": "1",
    "膨胀后加热器": "0",
    "1级膨胀机膨胀比": "13.131",
    "2级膨胀机膨胀比": "13.131",
    "3级膨胀机膨胀比": "0",
    "4级膨胀机膨胀比": "0",
    "5级膨胀机膨胀比": "0",
}

DEFAULT_CONSTANT_ENTRIES = {
    "理想气体常数(J/(mol·K))": "8.314",
    "空气摩尔质量(kg/mol)": "0.02897",
    "空气的绝热系数": "1.4",
    "空气的比热容(kJ/（kg·K）)": "1.005",
    "空气的焦耳-汤姆逊系数(K/MPa)": "0.22",
    "导热油的比热容(kJ/（kg·K）)": "2.05",
    "地温梯度(℃/100m)": "2.5",
    "厂用电占比 (%)": "0.05",
    "输气管道热损失(℃)": "10",
    "盐穴深度 (m)": "1350",
    "注入空气流量 (t/h)": "2650",
}

INPUT_GROUPS = {
    "variable_entries.txt": DEFAULT_VARIABLE_ENTRIES,
    "middle_entries.txt": DEFAULT_MIDDLE_ENTRIES,
    "constant_entries.txt": DEFAULT_CONSTANT_ENTRIES,
}

# 合并后的全部参数，便于模块间引用
ALL_DEFAULTS = {
    **DEFAULT_VARIABLE_ENTRIES,
    **DEFAULT_MIDDLE_ENTRIES,
    **DEFAULT_CONSTANT_ENTRIES,
}
