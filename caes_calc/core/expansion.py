def calculate_expansion_power(entries):
    """多级膨胀机功率计算。"""
    # 提取所需参数
    heat_capacity_ratio = float(entries["空气的绝热系数"].get())
    air_mass_flow = float(entries["注入空气流量 (t/h)"].get())
    gas_constant = float(entries["理想气体常数(J/(mol·K))"].get())
    air_molar_mass = float(entries["空气摩尔质量(kg/mol)"].get())
    storage_duration = float(entries["储能设计时长 (h)"].get())
    generation_duration = float(entries["发电设计时长 (h)"].get())
    expansion_efficiency = float(entries["膨胀机效率 (%)"].get())
    expansion_ratio_first = float(entries["1级膨胀机膨胀比"].get())

    # 计算膨胀过程空气流量，并把理想气体常数换算成 J/(t·K)
    expansion_air_mass_flow = air_mass_flow * storage_duration / generation_duration
    specific_gas_constant = gas_constant * 1000 / air_molar_mass

    result = {}
    initial_temp = float(entries["膨胀机入口空气温度 (℃)"].get()) + 273.15
    initial_pressure = float(entries["膨胀机进口气压 (MPa)"].get())

    # 第1级膨胀计算
    if expansion_ratio_first != 0:
        outlet_pressure_first = initial_pressure / expansion_ratio_first
        outlet_temp_first = initial_temp * (
            1 - expansion_efficiency * (1 - expansion_ratio_first ** ((1 - heat_capacity_ratio) / heat_capacity_ratio))
        )
        power_first = (
            (heat_capacity_ratio / (heat_capacity_ratio - 1))
            * (expansion_air_mass_flow * specific_gas_constant * initial_temp * expansion_efficiency)
            * (1 - expansion_ratio_first ** ((1 - heat_capacity_ratio) / heat_capacity_ratio))
            / 3.6e9
        )
        prev_outlet_pressure = outlet_pressure_first
        first_stage_outlet_temp = outlet_temp_first
        result["1级膨胀机出口压力(MPa)"] = round(outlet_pressure_first, 2)
        result["1级膨胀机出口温度（℃）"] = round(outlet_temp_first - 273.15, 2)
        result["1级膨胀机轴功率（MW）"] = round(power_first, 2)

    # 第2至5级膨胀计算
    for stage in range(2, 6):
        expansion_ratio = float(entries[f"{stage}级膨胀机膨胀比"].get())
        if expansion_ratio != 0:
            # 优先使用本级的独立入口温度，否则使用全局膨胀机入口温度
            stage_temp_key = f"{stage}级膨胀机入口空气温度(℃)"
            if stage_temp_key in entries and float(entries[stage_temp_key].get()) != 0:
                stage_inlet_temp = float(entries[stage_temp_key].get()) + 273.15
            else:
                stage_inlet_temp = initial_temp
            # 级间加热后等熵升压
            inlet_pressure = prev_outlet_pressure * (stage_inlet_temp / first_stage_outlet_temp) ** (
                (heat_capacity_ratio - 1) / heat_capacity_ratio
            )
            outlet_pressure = inlet_pressure / expansion_ratio
            outlet_temp = stage_inlet_temp * (
                1 - expansion_efficiency * (1 - expansion_ratio ** ((1 - heat_capacity_ratio) / heat_capacity_ratio))
            )
            power = (
                (heat_capacity_ratio / (heat_capacity_ratio - 1))
                * (expansion_air_mass_flow * specific_gas_constant * stage_inlet_temp * expansion_efficiency)
                * (1 - expansion_ratio ** ((1 - heat_capacity_ratio) / heat_capacity_ratio))
                / 3.6e9
            )
            result[f"{stage}级膨胀机入口压力(MPa)"] = round(inlet_pressure, 2)
            result[f"{stage}级膨胀机出口压力(MPa)"] = round(outlet_pressure, 2)
            result[f"{stage}级膨胀机出口温度（℃）"] = round(outlet_temp - 273.15, 2)
            result[f"{stage}级膨胀机轴功率（MW）"] = round(power, 2)
            prev_outlet_pressure = outlet_pressure

    # 移除值为0的条目
    result = {k: v for k, v in result.items() if v != 0}

    return result
