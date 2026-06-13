"""导热油需求与盐穴体积计算。

按流程图中实际存在的换热器逐个计算换热量：
- 压缩侧冷却器：根据上级出口温度与下级入口温度（或全局级间温度）的差值计算。
- 膨胀侧加热器：根据上级出口温度与下级入口温度（或全局入口温度）的差值计算。
- 第一级前、最后一级后的换热器也纳入计算。
"""


def calculate_thermal_oil_need(entries):
    """导热油需求与盐穴体积计算。"""
    from caes_calc.core.compression import calculate_compression_power
    from caes_calc.core.expansion import calculate_expansion_power
    from caes_calc.gui.flowchart_model import flat_to_model

    compression_results = calculate_compression_power(entries)
    expansion_results = calculate_expansion_power(entries)

    # 把 entries 转回普通字典，用于重建流程图模型
    flat = {k: v.get() for k, v in entries.items()}
    model = flat_to_model(flat)

    # 提取所需参数
    cavern_depth = float(entries["盐穴深度 (m)"].get())
    max_storage_pressure = float(entries["储能压力上限 (MPa)"].get())
    cutoff_pressure = float(entries["释放截止压力 (MPa)"].get())
    expansion_inlet_pressure = float(entries["膨胀机进口气压 (MPa)"].get())
    geothermal_gradient = float(entries["地温梯度(℃/100m)"].get())
    pipeline_temp_loss = float(entries["输气管道热损失(℃)"].get())
    thermal_oil_specific_heat = float(entries["导热油的比热容(kJ/（kg·K）)"].get())
    compression_oil_in_temp = float(entries["压缩时导热油入口温度(℃)"].get()) + 273.15
    compression_oil_out_temp = float(entries["压缩时导热油出口温度(℃)"].get()) + 273.15
    expansion_oil_in_temp = float(entries["膨胀时导热油入口温度(℃)"].get()) + 273.15
    expansion_oil_out_temp = float(entries["膨胀时导热油出口温度(℃)"].get()) + 273.15
    air_specific_heat = float(entries["空气的比热容(kJ/（kg·K）)"].get())
    air_mass_flow = float(entries["注入空气流量 (t/h)"].get())
    storage_duration = float(entries["储能设计时长 (h)"].get())
    generation_duration = float(entries["发电设计时长 (h)"].get())
    joule_thomson_coefficient = float(entries["空气的焦耳-汤姆逊系数(K/MPa)"].get())
    expansion_inlet_temp = float(entries["膨胀机入口空气温度 (℃)"].get()) + 273.15

    # 膨胀侧第 1 级前换热器入口温度（盐穴出口经管道热损和节流）
    cavern_temperature = 15 + cavern_depth * geothermal_gradient / 100
    exchanger_inlet_temp = (
        cavern_temperature
        - pipeline_temp_loss
        - joule_thomson_coefficient * (max_storage_pressure - expansion_inlet_pressure)
        + 273.15
    )

    expansion_air_mass_flow = air_mass_flow * storage_duration / generation_duration

    def _get_stage_inlet_temp(train, stage_index: int):
        """获取某级入口温度（K），优先使用级独立设定，否则按默认规则回退。"""
        if 1 <= stage_index <= len(train.stages):
            stage = train.stages[stage_index - 1]
            if stage.inlet_temp is not None:
                return stage.inlet_temp + 273.15
        if train is model.compression:
            # 第1级默认15℃，第2级及以后默认40℃
            if stage_index == 1:
                return model.compression.inlet_temperature + 273.15
            return 40 + 273.15
        return expansion_inlet_temp

    def _get_stage_outlet_temp(results: dict, stage_type: str, index: int):
        """从计算结果取某级出口温度（K），不存在返回 None。"""
        key = f"{index}级{stage_type}出口温度（℃）"
        if key in results:
            return results[key] + 273.15
        return None

    def _compression_hx_duty(hx):
        """计算单个压缩侧冷却器换热量（kW，正表示需冷却）。"""
        if hx.position == "before_first":
            # 第一级前冷却器：把入口空气从环境温度降到第 1 级入口温度。
            # 模型未提供环境空气温度，近似认为 source 为第 1 级入口温度，
            # 因此换热量为 0；若需计入环境冷却，可在此扩展。
            return 0.0

        if hx.position == "after_last":
            source = _get_stage_outlet_temp(compression_results, "压缩机", len(model.compression.stages))
            target = 40 + 273.15
        else:  # between
            source = _get_stage_outlet_temp(compression_results, "压缩机", hx.index)
            target = _get_stage_inlet_temp(model.compression, hx.index + 1)

        if source is None:
            return 0.0
        # 原代码逻辑：压缩机出口温度高于 100℃ 才需要导热油冷却
        if source <= 373.15:
            return 0.0
        duty = air_mass_flow * air_specific_heat * (source - target)
        return duty if duty > 0 else 0.0

    def _expansion_hx_duty(hx):
        """计算单个膨胀侧加热器换热量（kW，正表示需加热）。"""
        if hx.position == "before_first":
            source = exchanger_inlet_temp
            target = _get_stage_inlet_temp(model.expansion, 1)
        elif hx.position == "after_last":
            source = _get_stage_outlet_temp(expansion_results, "膨胀机", len(model.expansion.stages))
            target = expansion_inlet_temp
        else:  # between
            source = _get_stage_outlet_temp(expansion_results, "膨胀机", hx.index)
            target = _get_stage_inlet_temp(model.expansion, hx.index + 1)

        if source is None:
            return 0.0
        duty = expansion_air_mass_flow * air_specific_heat * (target - source)
        return duty if duty > 0 else 0.0

    compression_oil_total_flow = 0.0
    for hx in model.compression.heat_exchangers:
        duty = _compression_hx_duty(hx)
        if duty > 0:
            compression_oil_total_flow += duty / (
                abs(compression_oil_out_temp - compression_oil_in_temp) * thermal_oil_specific_heat
            )

    expansion_oil_total_flow = 0.0
    for hx in model.expansion.heat_exchangers:
        duty = _expansion_hx_duty(hx)
        if duty > 0:
            expansion_oil_total_flow += duty / (
                abs(expansion_oil_out_temp - expansion_oil_in_temp) * thermal_oil_specific_heat
            )

    compression_oil_total_mass = compression_oil_total_flow * storage_duration
    expansion_oil_total_mass = expansion_oil_total_flow * generation_duration

    # 计算需求盐穴体积
    gas_constant = float(entries["理想气体常数(J/(mol·K))"].get())
    air_molar_mass = float(entries["空气摩尔质量(kg/mol)"].get())
    salt_cavern_volume = (
        air_mass_flow * storage_duration
        * (gas_constant * (cavern_temperature + 273.15))
        / ((max_storage_pressure - cutoff_pressure) * 10 ** 7 * air_molar_mass)
    )

    return {
        "储气库空气温度(℃)": cavern_temperature,
        "储能过程导热油需求量（t）": round(compression_oil_total_mass, 2),
        "发电过程导热油需求量（t）": round(expansion_oil_total_mass, 2),
        "盐穴体积需求（万m³）": round(salt_cavern_volume, 2),
    }
