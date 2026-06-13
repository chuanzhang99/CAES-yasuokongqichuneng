"""iOS 风格 QSS 样式表与配色常量。"""

# iOS 系统色
IOS_SYSTEM_BLUE = "#007AFF"
IOS_SYSTEM_GREEN = "#34C759"
IOS_SYSTEM_RED = "#FF3B30"
IOS_SYSTEM_GRAY = "#8E8E93"
IOS_SYSTEM_GRAY2 = "#AEAEB2"
IOS_SYSTEM_GRAY5 = "#E5E5EA"
IOS_SYSTEM_GRAY6 = "#F2F2F7"
IOS_SYSTEM_BACKGROUND = "#FFFFFF"
IOS_SECONDARY_BACKGROUND = "#F2F2F7"
IOS_GROUPED_BACKGROUND = "#F2F2F7"
IOS_LABEL = "#000000"
IOS_SECONDARY_LABEL = "#3C3C4399"  # 60% 不透明
IOS_SEPARATOR = "#C6C6C8"


def get_ios_stylesheet() -> str:
    """返回全局 iOS 风格 QSS。"""
    return f"""
    /* 全局背景与字体 */
    QWidget {{
        font-family: "Microsoft YaHei", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
        font-size: 16px;
        color: {IOS_LABEL};
        background-color: {IOS_GROUPED_BACKGROUND};
    }}

    QMainWindow {{
        background-color: {IOS_GROUPED_BACKGROUND};
    }}

    /* 大标题标签 */
    QLabel#titleLabel {{
        font-size: 32px;
        font-weight: bold;
        color: {IOS_LABEL};
        background-color: transparent;
        padding: 16px 0 8px 0;
    }}

    QLabel#sectionHeader {{
        font-size: 15px;
        font-weight: bold;
        text-transform: uppercase;
        color: {IOS_SECONDARY_LABEL};
        background-color: transparent;
        padding: 16px 12px 6px 12px;
    }}

    QLabel {{
        background-color: transparent;
    }}

    /* 卡片容器：QGroupBox */
    QGroupBox {{
        background-color: {IOS_SYSTEM_BACKGROUND};
        border: 1px solid {IOS_SYSTEM_GRAY5};
        border-radius: 12px;
        margin-top: 8px;
        padding-top: 12px;
        padding-bottom: 8px;
        padding-left: 12px;
        padding-right: 12px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 12px;
        top: -8px;
        color: {IOS_SECONDARY_LABEL};
        font-size: 12px;
        font-weight: bold;
        background-color: transparent;
    }}

    /* 输入框 */
    QLineEdit {{
        background-color: {IOS_SYSTEM_BACKGROUND};
        border: 1px solid {IOS_SYSTEM_GRAY5};
        border-radius: 10px;
        padding: 10px 14px;
        min-height: 26px;
        selection-background-color: {IOS_SYSTEM_BLUE};
    }}

    QLineEdit:focus {{
        border: 2px solid {IOS_SYSTEM_BLUE};
    }}

    QLineEdit:disabled {{
        background-color: {IOS_SYSTEM_GRAY6};
        color: {IOS_SYSTEM_GRAY};
    }}

    /* 按钮 */
    QPushButton {{
        background-color: {IOS_SYSTEM_BLUE};
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 18px;
        font-weight: 600;
        min-height: 26px;
    }}

    QPushButton:hover {{
        background-color: #0056CC;
    }}

    QPushButton:pressed {{
        background-color: #004494;
    }}

    QPushButton:disabled {{
        background-color: {IOS_SYSTEM_GRAY5};
        color: {IOS_SYSTEM_GRAY2};
    }}

    QPushButton#dangerButton {{
        background-color: {IOS_SYSTEM_RED};
    }}

    QPushButton#dangerButton:hover {{
        background-color: #D32F2F;
    }}

    /* 次要按钮 */
    QPushButton#secondaryButton {{
        background-color: {IOS_SYSTEM_GRAY6};
        color: {IOS_SYSTEM_BLUE};
    }}

    QPushButton#secondaryButton:hover {{
        background-color: {IOS_SYSTEM_GRAY5};
    }}

    QPushButton#secondaryButton:pressed {{
        background-color: #D1D1D6;
    }}

    /* 标签页：iOS 分段控制器风格 */
    QTabWidget::pane {{
        border: none;
        background-color: {IOS_GROUPED_BACKGROUND};
        top: -1px;
    }}

    QTabWidget::tab-bar {{
        alignment: center;
    }}

    QTabBar::tab {{
        background-color: transparent;
        color: {IOS_SYSTEM_BLUE};
        border-top: 1px solid {IOS_SYSTEM_BLUE};
        border-bottom: 1px solid {IOS_SYSTEM_BLUE};
        border-left: none;
        border-right: 1px solid {IOS_SYSTEM_BLUE};
        padding: 10px 22px;
        font-weight: 600;
        min-width: 70px;
    }}

    QTabBar::tab:first {{
        border-left: 1px solid {IOS_SYSTEM_BLUE};
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
    }}

    QTabBar::tab:last {{
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}

    QTabBar::tab:only-one {{
        border: 1px solid {IOS_SYSTEM_BLUE};
        border-radius: 8px;
    }}

    QTabBar::tab:selected {{
        background-color: {IOS_SYSTEM_BLUE};
        color: white;
    }}

    QTabBar::tab:!selected:hover {{
        background-color: #E5F1FF;
    }}

    QTabBar::tab:selected:hover {{
        background-color: {IOS_SYSTEM_BLUE};
    }}

    /* 表格 */
    QTableWidget {{
        background-color: {IOS_SYSTEM_BACKGROUND};
        border: 1px solid {IOS_SYSTEM_GRAY5};
        border-radius: 12px;
        gridline-color: {IOS_SEPARATOR};
        selection-background-color: #E5F1FF;
        selection-color: {IOS_LABEL};
    }}

    QTableWidget::item {{
        padding: 10px 14px;
        border-bottom: 1px solid {IOS_SEPARATOR};
    }}

    QTableWidget::item:selected {{
        background-color: #E5F1FF;
    }}

    QHeaderView::section {{
        background-color: {IOS_SYSTEM_BACKGROUND};
        color: {IOS_SECONDARY_LABEL};
        font-size: 14px;
        font-weight: bold;
        padding: 10px 14px;
        border: none;
        border-bottom: 1px solid {IOS_SEPARATOR};
    }}

    /* 滚动条 */
    QScrollBar:vertical {{
        background-color: transparent;
        width: 8px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background-color: {IOS_SYSTEM_GRAY2};
        border-radius: 4px;
        min-height: 30px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {IOS_SYSTEM_GRAY};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* 消息框 */
    QMessageBox {{
        background-color: {IOS_SYSTEM_BACKGROUND};
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}

    /* 菜单 */
    QMenu {{
        background-color: {IOS_SYSTEM_BACKGROUND};
        border: 1px solid {IOS_SYSTEM_GRAY5};
        border-radius: 12px;
        padding: 8px 0;
    }}

    QMenu::item {{
        padding: 12px 26px;
        background-color: transparent;
    }}

    QMenu::item:selected {{
        background-color: {IOS_SYSTEM_GRAY5};
    }}

    /* 对话框 */
    QDialog {{
        background-color: {IOS_GROUPED_BACKGROUND};
    }}

    QDialog QLineEdit {{
        background-color: {IOS_SYSTEM_BACKGROUND};
    }}
"""
