# 非补燃压缩空气储能参数计算工具

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](./caes_calc/__init__.py)
<img width="2404" height="1860" alt="image" src="https://github.com/user-attachments/assets/0f7fd6c4-8d0c-470d-af8e-75cc2332f2ca" />


用于非补燃压缩空气储能（CAES）系统热力学参数计算与方案评估的免费工具，支持可视化流程图编辑、命令行计算与数据校验。

> 本程序由四川省非金属（盐业）地质调查研究所开发，计算结果仅供参考。

---

## 功能特性

### 1. 可视化流程图编辑
- 压缩管线与膨胀管线独立展示
- 压缩机图标为"前大后小"等腰梯形，透平机图标相反
- 双击图标编辑单级参数（压缩比 / 膨胀比）
- 支持增删压缩机 / 膨胀机级数（最多各 5 级）
- 自动在级间添加换热器，并实时联动计算

### 2. 核心计算
- 多级压缩机功率与出口温度、压力
- 多级膨胀机功率与出口温度、压力
- 导热油需求量（储能 / 发电两侧）
- 盐穴有效容积需求
- 系统总效率、储能需求电功率、发电输出电功率

### 3. 物理一致性校验
- 导热油温度范围：4℃ ~ 400℃
- 冷却器出口油温必须低于被冷却空气入口温度
- 加热器入口油温必须高于被加热空气入口温度
- 发电过程导热油用量 ≤ 储能过程导热油用量
- 盐穴深度决定承压上限（地层压力 × 1.2）
- 膨胀机出口压力不低于第一级压缩机入口压力
- 末级压缩机出口温度 ≤ 150℃，末级膨胀机出口温度 ≤ 72℃

### 4. 双入口
- **GUI**：`python gui.py`
- **CLI**：`python cli.py --check`

---

## 安装

```bash
# 1. 克隆仓库
git clone <repository-url>
cd yasuokongqichuneng

# 2. 创建虚拟环境（推荐）
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

依赖：
- Python 3.8+
- PyQt5 >= 5.15

---

## 使用方法

### 图形界面

```bash
python gui.py
```

启动后：
1. 在"流程图"标签页中双击压缩机 / 膨胀机图标修改级参数
2. 使用顶部按钮增删级数
3. 在"结果汇总"标签页查看计算结果
4. 点击"检查数据"查看物理校验警告

### 命令行

```bash
# 运行默认参数并打印结果
python cli.py

# 运行数据检查
python cli.py --check

# 导出结果到文件
python cli.py --export result.txt

# 指定输入目录
python cli.py --input-dir data --check --export out.txt
```

---

## 默认参数

当前默认配置为经过物理约束优化的可行解，典型结果如下：

| 项目 | 数值 |
|------|------|
| 系统效率 | **67.27%** |
| 压缩机总轴功率 | 542.21 MW |
| 储能需求电功率 | 593.04 MW |
| 膨胀机总轴功率 | 685.58 MW |
| 发电输出电功率 | 638.27 MW |
| 储能导热油需求 | 22905.59 t |
| 发电导热油需求 | 22857.69 t |
| 盐穴体积需求 | 65.28 万 m³ |

压缩 / 膨胀级数与压缩比：
- 3 级压缩：`14.0 / 8.5 / 1.4489`
- 2 级膨胀：`13.131 / 13.131`

> 程序首次运行会在 `data/` 目录生成输入参数文本文件；删除该目录即可恢复默认值。

---

## 项目结构

```
yasuokongqichuneng/
├── caes_calc/              # 核心包
│   ├── __init__.py
│   ├── config.py           # 默认参数与配置
│   ├── calculations.py     # 计算编排与系统汇总
│   ├── validation.py       # 物理一致性校验
│   ├── persistence.py      # data/ 目录参数持久化
│   ├── core/               # 核心热力学计算
│   │   ├── compression.py
│   │   ├── expansion.py
│   │   └── thermal.py
│   └── gui/                # PyQt5 图形界面
│       ├── main_window.py
│       ├── flowchart_model.py
│       ├── flowchart_view.py
│       ├── flowchart_dialogs.py
│       └── styles.py
├── data/                   # 运行期输入参数文件（首次运行时生成）
├── cli.py                  # 命令行入口
├── gui.py                  # 图形界面入口
├── requirements.txt        # 依赖
└── README.md
```

---

## 开发与调试

### 运行单元校验

```bash
python -c "from caes_calc.persistence import load_inputs; from caes_calc.validation import validate; print(len(validate(load_inputs('data'))))"
```

预期输出为 `0`。

---

## 作者与联系方式

- 作者：刘茂宇
- 邮箱：23578001@qq.com
- 单位：四川省非金属（盐业）地质调查研究所
- 咨询电话：0813-5591996

---

## 免责声明

本程序为技术交流工具，计算结果仅供工程前期估算参考。盐穴的实际承压能力、热力学性能及经济性需通过专业勘探、试验与详细设计确定。
