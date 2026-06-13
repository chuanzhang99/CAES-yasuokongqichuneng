"""输入参数校验逻辑。

所有检查均返回中文警告字符串列表；不直接弹出 GUI 对话框，以便 CLI 和 GUI 统一调用。
"""

from typing import Dict, List

from caes_calc.config import make_entries
from caes_calc.core.compression import calculate_compression_power
from caes_calc.core.expansion import calculate_expansion_power
from caes_calc.core.thermal import calculate_thermal_oil_need
from caes_calc.gui.flowchart_model import flat_to_model


def _get_stage_inlet_temp(train, stage_index: int, default_temp: float) -> float:
    """获取某级入口空气温度（℃），优先使用级独立设定，否则按规则回退。"""
    if 1 <= stage_index <= len(train.stages):
        stage = train.stages[stage_index - 1]
        if stage.inlet_temp is not None:
            return stage.inlet_temp
    if stage_index == 1:
        return train.inlet_temperature
    return default_temp


def validate(inputs: Dict[str, str]) -> List[str]:
    """对输入字典执行全部校验规则，返回警告列表。"""
    entries = make_entries(inputs)
    warnings: List[str] = []
    warning_index = 0

    compression_results = calculate_compression_power(entries)
    model = flat_to_model(inputs)

    # 确定使用中的压缩机级数
    max_compression_stage = 0
    for stage in range(1, 6):
        key = f"{stage}级压缩机压缩比"
        if key in inputs and float(inputs[key]) != 0:
            max_compression_stage = stage

    # 相邻压缩机级出口温度差距提示已移除：末级因控温需要通常与前级差异较大，
    # 该提示会与其他约束冲突，导致可行域过窄。

    # 判断最后一级压缩机的出口压力
    storage_pressure_limit = float(inputs["储能压力上限 (MPa)"]) * 1.01
    last_compressor_outlet_key = f"{max_compression_stage}级压缩机出口压力(MPa)"
    if last_compressor_outlet_key in compression_results:
        if compression_results[last_compressor_outlet_key] > storage_pressure_limit:
            warning_index += 1
            warnings.append(f"{warning_index}、压缩系统出口压力超过储能设计压力上限，不合理。")

    # 检查最后一级压缩机的出口温度（考虑末级后仍有冷却器，放宽到 150℃）
    last_compressor_temp_key = f"{max_compression_stage}级压缩机出口温度（℃）"
    if last_compressor_temp_key in compression_results:
        if compression_results[last_compressor_temp_key] > 150:
            warning_index += 1
            warnings.append(
                f"{warning_index}、最后1级压缩机出口温度过高，会降低系统整体效率，"
                "建议控制在150℃以下，建议调整压缩比或增加压缩机级数。"
            )

    # 油温匹配已由下方“换热器入口油温与下级入口空气温度”校验覆盖，
    # 但还需确保压缩侧导热油出口温度低于被冷却空气入口温度（即上级压缩机出口温度）。
    compression_oil_out_temp = float(inputs["压缩时导热油出口温度(℃)"])
    for hx in model.compression.heat_exchangers:
        if hx.position == "before_first":
            continue
        if hx.position == "after_last":
            source_stage = len(model.compression.stages)
        else:  # between
            source_stage = hx.index
        source_key = f"{source_stage}级压缩机出口温度（℃）"
        if source_key in compression_results:
            air_temp = compression_results[source_key]
            if compression_oil_out_temp >= air_temp:
                warning_index += 1
                pos_text = "最后1级后" if hx.position == "after_last" else f"第 {hx.index} 级后"
                warnings.append(
                    f"{warning_index}、压缩侧{pos_text}冷却器出口油温 "
                    f"[{compression_oil_out_temp:.1f}℃] 高于或等于被冷却空气入口温度 "
                    f"[{air_temp:.1f}℃]，无法有效换热。"
                )

    # 检查油温输入值是否错误
    if "膨胀时导热油入口温度(℃)" in inputs and "压缩时导热油出口温度(℃)" in inputs:
        expansion_temp = float(inputs["膨胀时导热油入口温度(℃)"])
        compression_temp = float(inputs["压缩时导热油出口温度(℃)"])
        if expansion_temp > compression_temp:
            warning_index += 1
            warnings.append(
                f"{warning_index}、膨胀时导热油入口温度不应高于压缩时导热油出口温度，需要调整。"
            )

    # 导热油温度应在 4℃~400℃ 之间
    oil_temp_keys = [
        ("压缩时导热油入口温度(℃)", "压缩侧导热油入口温度"),
        ("压缩时导热油出口温度(℃)", "压缩侧导热油出口温度"),
        ("膨胀时导热油入口温度(℃)", "膨胀侧导热油入口温度"),
        ("膨胀时导热油出口温度(℃)", "膨胀侧导热油出口温度"),
    ]
    for key, name in oil_temp_keys:
        if key in inputs:
            temp = float(inputs[key])
            if temp < 4 or temp > 400:
                warning_index += 1
                warnings.append(
                    f"{warning_index}、{name} [{temp:.1f}℃] 超出 4℃~400℃ 的合理范围。"
                )

    # 检查膨胀机入口温度不应大于导热油温
    if "膨胀时导热油入口温度(℃)" in inputs and "膨胀机入口空气温度 (℃)" in inputs:
        expansion_temp = float(inputs["膨胀时导热油入口温度(℃)"])
        air_temp = float(inputs["膨胀机入口空气温度 (℃)"])
        if expansion_temp < air_temp:
            warning_index += 1
            warnings.append(
                f"{warning_index}、膨胀机入口空气温度不应高于导热油入口温度！"
            )

    expansion_results = calculate_expansion_power(entries)

    # 确定使用中的膨胀机级数
    max_expansion_stage = 0
    for stage in range(1, 6):
        key = f"{stage}级膨胀机膨胀比"
        if key in inputs and float(inputs[key]) != 0:
            max_expansion_stage = stage

    # 检查最后一级膨胀机出口压力是否过大
    last_expansion_outlet_key = f"{max_expansion_stage}级膨胀机出口压力(MPa)"
    if last_expansion_outlet_key in expansion_results:
        if expansion_results[last_expansion_outlet_key] > 0.2:
            warning_index += 1
            warnings.append(
                f"{warning_index}、最后1级膨胀机出口压力 "
                f"{expansion_results[last_expansion_outlet_key]:.2f} MPa，"
                "可增加膨胀比提高效率。"
            )

    # 检查最后一级膨胀出口温度超过72℃提示
    last_expansion_temp_key = f"{max_expansion_stage}级膨胀机出口温度（℃）"
    if last_expansion_temp_key in expansion_results:
        if expansion_results[last_expansion_temp_key] > 72:
            warning_index += 1
            warnings.append(
                f"{warning_index}、最后1级膨胀机出口温度 "
                f"{expansion_results[last_expansion_temp_key]:.2f} ℃，"
                "影响整体效率，建议增大膨胀比。"
            )

    # 膨胀侧油温匹配已由下方“换热器入口油温与下级入口空气温度”校验覆盖，
    # 此处不再重复要求“导热油出口温度大于膨胀机出口空气温度”。

    # 检查换热器油温与下一级入口空气温度的匹配
    compression_oil_in_temp = float(inputs["压缩时导热油入口温度(℃)"])
    for hx in model.compression.heat_exchangers:
        if hx.position == "after_last":
            continue
        if hx.position == "before_first":
            target_stage = 1
        else:  # between
            target_stage = hx.index + 1
        target_temp = _get_stage_inlet_temp(model.compression, target_stage, 40.0)
        if compression_oil_in_temp > target_temp:
            warning_index += 1
            pos_text = "第 1 级前" if hx.position == "before_first" else f"第 {hx.index} 级后"
            warnings.append(
                f"{warning_index}、压缩侧{pos_text}冷却器入口油温 "
                f"[{compression_oil_in_temp:.1f}℃] 高于第 {target_stage} 级压缩机入口空气温度 "
                f"[{target_temp:.1f}℃]，无法有效冷却。"
            )

    expansion_oil_in_temp = float(inputs["膨胀时导热油入口温度(℃)"])
    for hx in model.expansion.heat_exchangers:
        if hx.position == "after_last":
            continue
        if hx.position == "before_first":
            target_stage = 1
        else:  # between
            target_stage = hx.index + 1
        target_temp = _get_stage_inlet_temp(
            model.expansion, target_stage, model.expansion.inlet_temperature
        )
        if expansion_oil_in_temp < target_temp:
            warning_index += 1
            pos_text = "第 1 级前" if hx.position == "before_first" else f"第 {hx.index} 级后"
            warnings.append(
                f"{warning_index}、膨胀侧{pos_text}加热器入口油温 "
                f"[{expansion_oil_in_temp:.1f}℃] 低于第 {target_stage} 级膨胀机入口空气温度 "
                f"[{target_temp:.1f}℃]，无法有效加热。"
            )

    # 检查膨胀机每级出口温度是否大于等于0摄氏度，气压是否小于大气压
    inlet_air_pressure = float(inputs["进口空气气压 (MPa)"])
    for stage in range(1, max_expansion_stage + 1):
        temp_key = f"{stage}级膨胀机出口温度（℃）"
        if temp_key in expansion_results:
            if expansion_results[temp_key] < 0:
                warning_index += 1
                warnings.append(
                    f"{warning_index}、第{stage}级膨胀机的出口温度 "
                    f"{expansion_results[temp_key]:.2f}℃ 低于0℃。"
                )
        pressure_key = f"{stage}级膨胀机出口压力(MPa)"
        if pressure_key in expansion_results:
            if expansion_results[pressure_key] < inlet_air_pressure:
                warning_index += 1
                warnings.append(
                    f"{warning_index}、第{stage}级膨胀机的出口压力 "
                    f"{expansion_results[pressure_key]:.2f} MPa "
                    f"低于第一级压缩机入口压力 {inlet_air_pressure:.4f} MPa。"
                )

    # 专门检查最后一级膨胀机出口压力是否低于第一级压缩机入口压力
    # 已由上方逐级循环覆盖，此处不再重复。

    # 检查导热油需求量：发电过程不能超过储能过程
    thermal_results = calculate_thermal_oil_need(entries)
    compression_oil_demand = thermal_results["储能过程导热油需求量（t）"]
    expansion_oil_demand = thermal_results["发电过程导热油需求量（t）"]
    if expansion_oil_demand > compression_oil_demand:
        warning_index += 1
        warnings.append(
            f"{warning_index}、发电过程导热油需求量（{expansion_oil_demand:.2f} t）"
            f"超过储能过程导热油需求量（{compression_oil_demand:.2f} t），参数不合理，"
            "建议降低膨胀机入口空气温度。"
        )

    # 计算盐穴的地层压力值
    cavern_depth = float(inputs["盐穴深度 (m)"])
    max_storage_pressure = float(inputs["储能压力上限 (MPa)"])
    cutoff_pressure = float(inputs["释放截止压力 (MPa)"])
    expansion_inlet_pressure = float(inputs["膨胀机进口气压 (MPa)"])

    # 膨胀机进口气压允许低于释放截止压力（入口设有减压阀），此处不再校验。

    formation_pressure = cavern_depth * 0.012
    max_allowable_pressure = formation_pressure * 1.2
    pressure_warnings = []
    if max_storage_pressure > max_allowable_pressure:
        pressure_warnings.append(
            f"储能压力上限 {max_storage_pressure:.2f} MPa 超过盐穴深度 {cavern_depth:.0f}m "
            f"允许上限 {max_allowable_pressure:.2f} MPa（地层压力 {formation_pressure:.2f} MPa × 1.2）"
        )
    if cutoff_pressure > max_allowable_pressure:
        pressure_warnings.append(
            f"释放截止压力 {cutoff_pressure:.2f} MPa 超过盐穴深度 {cavern_depth:.0f}m "
            f"允许上限 {max_allowable_pressure:.2f} MPa"
        )
    if cutoff_pressure >= max_storage_pressure:
        pressure_warnings.append(
            f"释放截止压力 {cutoff_pressure:.2f} MPa 不应高于储能压力上限 {max_storage_pressure:.2f} MPa"
        )
    if pressure_warnings:
        warning_index += 1
        warnings.append(
            f"{warning_index}、" + "；".join(pressure_warnings) + "。"
        )

    return warnings
