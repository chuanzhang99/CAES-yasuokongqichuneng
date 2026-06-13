"""计算编排与系统汇总。"""

from typing import Dict

from caes_calc.config import make_entries
from caes_calc.core.compression import calculate_compression_power
from caes_calc.core.expansion import calculate_expansion_power
from caes_calc.core.thermal import calculate_thermal_oil_need


def calculate_system_summary(
    compression_results: Dict,
    expansion_results: Dict,
    entries,
) -> Dict[str, object]:
    """汇总储能系统总效率、输入/输出功率与电量。"""
    total_compression_power = sum(v for k, v in compression_results.items() if "轴功率" in k)

    motor_efficiency = float(entries["储能电动机效率 (%)"].get())
    plant_use_ratio = float(entries["厂用电占比 (%)"].get())
    storage_duration = float(entries["储能设计时长 (h)"].get())
    total_input_power = total_compression_power / motor_efficiency * (1 + plant_use_ratio)
    total_energy_consumption = total_input_power * storage_duration

    total_expansion_power = sum(v for k, v in expansion_results.items() if "轴功率" in k)
    generator_efficiency = float(entries["发电机效率 (%)"].get())
    generation_duration = float(entries["发电设计时长 (h)"].get())
    total_output_power = total_expansion_power * generator_efficiency * (1 - plant_use_ratio)
    total_generation_energy = total_output_power * generation_duration
    total_efficiency = total_generation_energy / total_energy_consumption

    return {
        "压缩空气储能系统效率": "{:.2%}".format(total_efficiency),
        "压缩机总轴功率（MW）": round(total_compression_power, 2),
        "储能需求电功率（MW）": round(total_input_power, 2),
        "储能总电能消耗（MWh）": round(total_energy_consumption, 2),
        "膨胀机总轴功率（MW）": round(total_expansion_power, 2),
        "发电输出电功率（MW）": round(total_output_power, 2),
        "发电输出总电量（MWh）": round(total_generation_energy, 2),
    }


def run_all_calculations(inputs: Dict[str, str]) -> Dict[str, Dict]:
    """运行全部计算并返回分类结果字典。"""
    entries = make_entries(inputs)
    compression_results = calculate_compression_power(entries)
    expansion_results = calculate_expansion_power(entries)
    thermal_results = calculate_thermal_oil_need(entries)
    system_results = calculate_system_summary(compression_results, expansion_results, entries)

    return {
        "compression": compression_results,
        "expansion": expansion_results,
        "thermal": thermal_results,
        "system": system_results,
    }
