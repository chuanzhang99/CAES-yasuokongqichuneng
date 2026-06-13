"""流程图数据模型：结构化表示压缩机/膨胀机/换热器，并与扁平输入字典互转。"""

from dataclasses import dataclass, field
from typing import Dict, List
import re


MAX_STAGES = 5


@dataclass
class CompressorStage:
    index: int
    ratio: float
    efficiency: float
    inlet_temp: float = None  # 该级独立入口温度（℃），None 表示使用全局默认值


@dataclass
class ExpansionStage:
    index: int
    ratio: float
    efficiency: float
    inlet_temp: float = None  # 该级独立入口温度（℃），None 表示使用全局默认值


@dataclass
class HeatExchanger:
    """换热器。

    position: "before_first" | "between" | "after_last"
    index: 所在间隙编号。0 表示第 1 级之前，N 表示第 N 级之后。
    hx_type: "cooler"（压缩侧冷却器）或 "heater"（膨胀侧加热器）。
    """

    position: str
    index: int
    hx_type: str


@dataclass
class ProcessTrain:
    stages: List = field(default_factory=list)
    heat_exchangers: List[HeatExchanger] = field(default_factory=list)
    global_efficiency: float = 0.0
    # 系统级参数
    inlet_temperature: float = 0.0  # 第一级入口温度（℃）
    inlet_pressure: float = 0.0  # 第一级入口压力（MPa）
    design_duration: float = 0.0  # 设计时长（h）
    max_pressure: float = 0.0  # 压缩侧：储能压力上限（MPa）
    min_pressure: float = 0.0  # 膨胀侧：释放截止压力（MPa）
    oil_inlet_temp: float = 0.0  # 导热油入口温度（℃）
    oil_outlet_temp: float = 0.0  # 导热油出口温度（℃）
    motor_efficiency: float = 0.0  # 压缩侧：电动机效率
    generator_efficiency: float = 0.0  # 膨胀侧：发电机效率
    air_mass_flow: float = 0.0  # 注入空气流量（t/h），逻辑上挂在压缩侧


@dataclass
class FlowchartModel:
    compression: ProcessTrain
    expansion: ProcessTrain
    globals: Dict[str, str] = field(default_factory=dict)


def _parse_stages(flat: Dict[str, str], stage_type: str, stage_class, global_efficiency: float):
    """从扁平字典解析某类级。"""
    stages = []
    ratio_key = "压缩比" if stage_type == "压缩机" else "膨胀比"
    temp_key_prefix = "压缩机" if stage_type == "压缩机" else "膨胀机"
    for i in range(1, MAX_STAGES + 1):
        value = float(flat.get(f"{i}级{stage_type}{ratio_key}", "0"))
        if value != 0:
            temp_value = flat.get(f"{i}级{temp_key_prefix}入口空气温度(℃)", "").strip()
            inlet_temp = float(temp_value) if temp_value else None
            stages.append(stage_class(index=i, ratio=value, efficiency=global_efficiency, inlet_temp=inlet_temp))
    return stages


def _build_default_heat_exchangers(stages: List, hx_type: str) -> List[HeatExchanger]:
    """根据级数生成默认级间换热器（每级之间一个）。"""
    heat_exchangers = []
    for i in range(1, len(stages)):
        heat_exchangers.append(HeatExchanger(position="between", index=i, hx_type=hx_type))
    return heat_exchangers


def flat_to_model(flat: Dict[str, str]) -> FlowchartModel:
    """把现有扁平参数字典转换为流程图模型。"""
    comp_eff = float(flat.get("压缩机效率 (%)", "0.85"))
    exp_eff = float(flat.get("膨胀机效率 (%)", "0.9"))

    compression_stages = _parse_stages(flat, "压缩机", CompressorStage, comp_eff)
    expansion_stages = _parse_stages(flat, "膨胀机", ExpansionStage, exp_eff)

    compression_hxs = _build_default_heat_exchangers(compression_stages, "cooler")
    expansion_hxs = _build_default_heat_exchangers(expansion_stages, "heater")

    # 前后换热器根据持久化标志添加
    if flat.get("压缩前冷却器", "0") == "1":
        compression_hxs.append(HeatExchanger(position="before_first", index=0, hx_type="cooler"))
    if flat.get("压缩后冷却器", "0") == "1":
        compression_hxs.append(HeatExchanger(position="after_last", index=len(compression_stages), hx_type="cooler"))
    if flat.get("膨胀前加热器", "0") == "1":
        expansion_hxs.append(HeatExchanger(position="before_first", index=0, hx_type="heater"))
    if flat.get("膨胀后加热器", "0") == "1":
        expansion_hxs.append(HeatExchanger(position="after_last", index=len(expansion_stages), hx_type="heater"))

    # 按 index 排序，便于布局和显示
    compression_hxs.sort(key=lambda hx: hx.index)
    expansion_hxs.sort(key=lambda hx: hx.index)

    # 全局参数：复制所有非级参数、非系统级参数
    system_keys = {
        "压缩机入口空气温度 (℃)", "进口空气气压 (MPa)", "储能设计时长 (h)", "储能压力上限 (MPa)",
        "压缩时导热油入口温度(℃)", "压缩时导热油出口温度(℃)", "压缩机效率 (%)", "储能电动机效率 (%)",
        "压缩前冷却器", "压缩后冷却器",
        "膨胀机入口空气温度 (℃)", "膨胀机进口气压 (MPa)", "发电设计时长 (h)", "释放截止压力 (MPa)",
        "膨胀时导热油入口温度(℃)", "膨胀时导热油出口温度(℃)", "膨胀机效率 (%)", "发电机效率 (%)",
        "膨胀前加热器", "膨胀后加热器",
        "注入空气流量 (t/h)",  # 逻辑上挂在压缩侧起点
        "多级压缩机入口空气温度(℃)",  # 已弃用，不再作为通用常数
    }
    # 排除每级压缩比/膨胀比和每级独立入口温度
    per_stage_temp_pattern = re.compile(r"^\d+级(压缩机|膨胀机)入口空气温度")
    globals_dict = {}
    for k, v in flat.items():
        if k in system_keys:
            continue
        if "压缩比" in k or "膨胀比" in k:
            continue
        if per_stage_temp_pattern.search(k):
            continue
        globals_dict[k] = v

    return FlowchartModel(
        compression=ProcessTrain(
            stages=compression_stages,
            heat_exchangers=compression_hxs,
            global_efficiency=comp_eff,
            inlet_temperature=float(flat.get("压缩机入口空气温度 (℃)", "15")),
            inlet_pressure=float(flat.get("进口空气气压 (MPa)", "0.1015")),
            design_duration=float(flat.get("储能设计时长 (h)", "8")),
            max_pressure=float(flat.get("储能压力上限 (MPa)", "17.5")),
            oil_inlet_temp=float(flat.get("压缩时导热油入口温度(℃)", "25")),
            oil_outlet_temp=float(flat.get("压缩时导热油出口温度(℃)", "350")),
            motor_efficiency=float(flat.get("储能电动机效率 (%)", "0.96")),
            air_mass_flow=float(flat.get("注入空气流量 (t/h)", "2650")),
        ),
        expansion=ProcessTrain(
            stages=expansion_stages,
            heat_exchangers=expansion_hxs,
            global_efficiency=exp_eff,
            inlet_temperature=float(flat.get("膨胀机入口空气温度 (℃)", "345")),
            inlet_pressure=float(flat.get("膨胀机进口气压 (MPa)", "10")),
            design_duration=float(flat.get("发电设计时长 (h)", "5")),
            min_pressure=float(flat.get("释放截止压力 (MPa)", "14.5")),
            oil_inlet_temp=float(flat.get("膨胀时导热油入口温度(℃)", "345")),
            oil_outlet_temp=float(flat.get("膨胀时导热油出口温度(℃)", "75")),
            generator_efficiency=float(flat.get("发电机效率 (%)", "0.98")),
        ),
        globals=globals_dict,
    )


def model_to_flat(model: FlowchartModel) -> Dict[str, str]:
    """把流程图模型转回扁平参数字典，供现有计算和持久化使用。"""
    flat = dict(model.globals)

    # 压缩机系统级参数
    flat["压缩机入口空气温度 (℃)"] = str(model.compression.inlet_temperature)
    flat["进口空气气压 (MPa)"] = str(model.compression.inlet_pressure)
    flat["储能设计时长 (h)"] = str(model.compression.design_duration)
    flat["储能压力上限 (MPa)"] = str(model.compression.max_pressure)
    flat["压缩时导热油入口温度(℃)"] = str(model.compression.oil_inlet_temp)
    flat["压缩时导热油出口温度(℃)"] = str(model.compression.oil_outlet_temp)
    flat["压缩机效率 (%)"] = str(model.compression.global_efficiency)
    flat["储能电动机效率 (%)"] = str(model.compression.motor_efficiency)
    flat["注入空气流量 (t/h)"] = str(model.compression.air_mass_flow)

    # 膨胀机系统级参数
    flat["膨胀机入口空气温度 (℃)"] = str(model.expansion.inlet_temperature)
    flat["膨胀机进口气压 (MPa)"] = str(model.expansion.inlet_pressure)
    flat["发电设计时长 (h)"] = str(model.expansion.design_duration)
    flat["释放截止压力 (MPa)"] = str(model.expansion.min_pressure)
    flat["膨胀时导热油入口温度(℃)"] = str(model.expansion.oil_inlet_temp)
    flat["膨胀时导热油出口温度(℃)"] = str(model.expansion.oil_outlet_temp)
    flat["膨胀机效率 (%)"] = str(model.expansion.global_efficiency)
    flat["发电机效率 (%)"] = str(model.expansion.generator_efficiency)

    # 压缩机级
    for stage in model.compression.stages:
        flat[f"{stage.index}级压缩机压缩比"] = f"{stage.ratio:g}"
        if stage.inlet_temp is not None:
            flat[f"{stage.index}级压缩机入口空气温度(℃)"] = str(stage.inlet_temp)
    for i in range(len(model.compression.stages) + 1, MAX_STAGES + 1):
        flat[f"{i}级压缩机压缩比"] = "0"

    # 膨胀机级
    for stage in model.expansion.stages:
        flat[f"{stage.index}级膨胀机膨胀比"] = f"{stage.ratio:g}"
        if stage.inlet_temp is not None:
            flat[f"{stage.index}级膨胀机入口空气温度(℃)"] = str(stage.inlet_temp)
    for i in range(len(model.expansion.stages) + 1, MAX_STAGES + 1):
        flat[f"{i}级膨胀机膨胀比"] = "0"

    # 前后换热器标志
    flat["压缩前冷却器"] = "1" if any(hx.position == "before_first" for hx in model.compression.heat_exchangers) else "0"
    flat["压缩后冷却器"] = "1" if any(hx.position == "after_last" for hx in model.compression.heat_exchangers) else "0"
    flat["膨胀前加热器"] = "1" if any(hx.position == "before_first" for hx in model.expansion.heat_exchangers) else "0"
    flat["膨胀后加热器"] = "1" if any(hx.position == "after_last" for hx in model.expansion.heat_exchangers) else "0"

    return flat
