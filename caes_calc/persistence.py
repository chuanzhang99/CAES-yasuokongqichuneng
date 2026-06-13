"""输入参数的持久化：读写 data/ 目录下的 txt 文件。"""

import os
from typing import Dict

from caes_calc.config import INPUT_GROUPS


def read_or_create_file(filepath: str, default_content: Dict[str, str]) -> str:
    """若文件存在则读取，否则按默认值创建。"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as file:
            return file.read()
    with open(filepath, "w", encoding="utf-8") as file:
        for key, value in default_content.items():
            file.write(f"{key}: {value}\n")
    return "\n".join(f"{key}: {value}" for key, value in default_content.items())


def parse_content_to_dict(content: str) -> Dict[str, str]:
    """把 'key: value' 文本解析成字典。"""
    result = {}
    for line in content.split("\n"):
        if ": " in line:
            key, value = line.split(": ", 1)
            result[key.strip()] = value.strip()
    return result


def load_inputs(data_dir: str = "data") -> Dict[str, str]:
    """从 data_dir 加载三组输入并与默认值合并。"""
    inputs = {}
    for filename, defaults in INPUT_GROUPS.items():
        filepath = os.path.join(data_dir, filename)
        content = read_or_create_file(filepath, defaults)
        parsed = parse_content_to_dict(content)
        merged = dict(defaults)
        merged.update(parsed)
        inputs.update(merged)
    return inputs


def save_inputs(inputs: Dict[str, str], data_dir: str = "data"):
    """按组把输入写回 txt 文件。"""
    os.makedirs(data_dir, exist_ok=True)
    for filename, group_defaults in INPUT_GROUPS.items():
        filepath = os.path.join(data_dir, filename)
        with open(filepath, "w", encoding="utf-8") as file:
            for key in group_defaults:
                value = inputs.get(key, group_defaults[key])
                file.write(f"{key}: {value}\n")
