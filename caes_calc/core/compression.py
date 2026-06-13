def calculate_compression_power(entries):
    """多级压缩机功率计算。"""
    # 提取所需参数
    heat_capacity_ratio = float(entries["空气的绝热系数"].get())
    air_mass_flow = float(entries["注入空气流量 (t/h)"].get())
    gas_constant = float(entries["理想气体常数(J/(mol·K))"].get())
    air_molar_mass = float(entries["空气摩尔质量(kg/mol)"].get())
    compression_efficiency = float(entries["压缩机效率 (%)"].get())
    compression_ratio_first = float(entries["1级压缩机压缩比"].get())
    initial_temp = float(entries["压缩机入口空气温度 (℃)"].get()) + 273.15
    initial_pressure = float(entries["进口空气气压 (MPa)"].get())

    # 把理想气体常数换算成 J/(t·K)
    specific_gas_constant = gas_constant * 1000 / air_molar_mass

    result = {}

    # 第1级压缩计算
    if compression_ratio_first != 0:
        outlet_pressure_first = initial_pressure * compression_ratio_first
        outlet_temp_first = initial_temp * (compression_ratio_first ** ((heat_capacity_ratio - 1) / heat_capacity_ratio)) ** (1 / compression_efficiency)
        power_first = (
            (heat_capacity_ratio / (heat_capacity_ratio - 1))
            * (air_mass_flow * specific_gas_constant * initial_temp / compression_efficiency)
            * (compression_ratio_first ** ((heat_capacity_ratio - 1) / heat_capacity_ratio) - 1)
            / 3.6e9
        )
        prev_outlet_temp, prev_outlet_pressure = outlet_temp_first, outlet_pressure_first
        result["1级压缩机出口压力(MPa)"] = round(outlet_pressure_first, 2)
        result["1级压缩机出口温度（℃）"] = round(outlet_temp_first - 273.15, 2)
        result["1级压缩机轴功率（MW）"] = round(power_first, 2)

    # 第2至5级压缩计算
    for stage in range(2, 6):
        compression_ratio = float(entries[f"{stage}级压缩机压缩比"].get())
        if compression_ratio != 0:
            # 优先使用本级的独立入口温度，否则默认第2级及以后为40℃
            stage_temp_key = f"{stage}级压缩机入口空气温度(℃)"
            if stage_temp_key in entries and float(entries[stage_temp_key].get()) != 0:
                stage_inlet_temp = float(entries[stage_temp_key].get()) + 273.15
            else:
                stage_inlet_temp = 40 + 273.15
            # 级间冷却后等熵降压
            inlet_pressure = prev_outlet_pressure * (stage_inlet_temp / prev_outlet_temp) ** (
                (heat_capacity_ratio - 1) / heat_capacity_ratio
            )
            outlet_pressure = inlet_pressure * compression_ratio
            outlet_temp = stage_inlet_temp * (compression_ratio ** ((heat_capacity_ratio - 1) / heat_capacity_ratio)) ** (1 / compression_efficiency)
            power = (
                (heat_capacity_ratio / (heat_capacity_ratio - 1))
                * (air_mass_flow * specific_gas_constant * stage_inlet_temp / compression_efficiency)
                * (compression_ratio ** ((heat_capacity_ratio - 1) / heat_capacity_ratio) - 1)
                / 3.6e9
            )
            result[f"{stage}级压缩机入口压力(MPa)"] = round(inlet_pressure, 2)
            result[f"{stage}级压缩机出口压力(MPa)"] = round(outlet_pressure, 2)
            result[f"{stage}级压缩机出口温度（℃）"] = round(outlet_temp - 273.15, 2)
            result[f"{stage}级压缩机轴功率（MW）"] = round(power, 2)
            prev_outlet_temp, prev_outlet_pressure = outlet_temp, outlet_pressure

    # 移除值为0的条目
    result = {k: v for k, v in result.items() if v != 0}

    return result
