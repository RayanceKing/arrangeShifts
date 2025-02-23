import sys
import pandas as pd
import random
import re
from collections import defaultdict
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt

class SchedulerUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("现代化排班系统")
        self.setGeometry(100, 100, 900, 600)  # 增加宽度以容纳更多列
        self.file_path = ""
        self.schedule = {}

        # 设置中央窗口和整体布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # 标题
        title_label = QLabel("排班系统")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        main_layout.addWidget(title_label)

        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_line_edit = QLineEdit()
        self.file_line_edit.setPlaceholderText("请选择包含排班信息的 Excel 文件")
        self.file_line_edit.setReadOnly(True)
        file_layout.addWidget(self.file_line_edit)
        browse_button = QPushButton("浏览")
        browse_button.clicked.connect(self.browse_file)
        file_layout.addWidget(browse_button)
        main_layout.addLayout(file_layout)

        # 生成排班按钮
        generate_button = QPushButton("生成排班")
        generate_button.clicked.connect(self.generate_schedule)
        main_layout.addWidget(generate_button)

        # 排班结果表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)  # 调整为5列
        self.table_widget.setHorizontalHeaderLabels(["工作日", "值班人数", "机务部人员", "播音部人员", "部门分配"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setColumnWidth(2, 200)  # 机务部人员列宽度
        self.table_widget.setColumnWidth(3, 200)  # 播音部人员列宽度
        self.table_widget.setColumnWidth(4, 150)  # 部门分配列宽度
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setAlternatingRowColors(True)
        main_layout.addWidget(self.table_widget)

        # 保存排班结果按钮
        save_button = QPushButton("保存排班结果")
        save_button.clicked.connect(self.save_schedule)
        main_layout.addWidget(save_button)

        # 设置现代化的样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f2f5;
            }
            QWidget {
                font-family: "Segoe UI", Helvetica, Arial, sans-serif;
                font-size: 14px;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 6px;
                background-color: #fff;
            }
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
            QTableWidget {
                background-color: #fff;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #fafafa;
                padding: 8px;
                border: 1px solid #ddd;
            }
        """)

    def browse_file(self):
        """选择 Excel 文件并显示路径"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.file_line_edit.setText(file_name)

    def generate_schedule(self):
        """生成排班并显示结果，考虑部门分配和不重复要求"""
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return

        try:
            # 读取 Excel 文件，假设无标题，三列：姓名、空闲天数、工作部门
            df = pd.read_excel(self.file_path, header=None, names=['姓名', '空闲天数', '工作部门'])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取 Excel 文件失败:\n{str(e)}")
            return

        # 初始化数据
        available_days = defaultdict(lambda: {'机务部': [], '播音部': []})
        used_staff = set()  # 跟踪已排班人员，确保不重复
        schedule = {day: {'机务部': [], '播音部': []} for day in ['周一', '周二', '周三', '周四', '周五']}
        department_count = {day: {'机务部': 0, '播音部': 0} for day in schedule.keys()}

        # 数据清洗：提取空闲天数并按部门分组
        for _, row in df.iterrows():
            name = row['姓名']
            dept = row['工作部门']
            if dept not in ['机务部', '播音部']:
                continue  # 跳过无效部门
            raw_days = str(row['空闲天数'])
            days = re.findall(r'(?:星期|周)?([一二三四五])', raw_days)
            for day in [f"周{day}" for day in days]:
                available_days[day][dept].append(name)

        # 按可用人数排序并生成排班
        errors = []
        sorted_days = sorted(schedule.keys(), key=lambda x: len(available_days[x]['机务部']) + len(available_days[x]['播音部']))
        for day in sorted_days:
            mech_candidates = [p for p in available_days[day]['机务部'] if p not in used_staff]
            sound_candidates = [p for p in available_days[day]['播音部'] if p not in used_staff]

            # 检查机务部最低人数要求
            if len(mech_candidates) < 3:
                errors.append(f"{day} 机务部可用人数不足3人，仅有 {len(mech_candidates)} 人")
                mech_selected = mech_candidates
            else:
                random.shuffle(mech_candidates)
                mech_selected = mech_candidates[:3]

            # 检查播音部最低人数要求
            if len(sound_candidates) < 4:
                errors.append(f"{day} 播音部可用人数不足4人，仅有 {len(sound_candidates)} 人")
                sound_selected = sound_candidates
            else:
                random.shuffle(sound_candidates)
                sound_selected = sound_candidates[:4]

            # 记录当天的排班名单
            if mech_selected or sound_selected:
                schedule[day]['机务部'] = mech_selected
                schedule[day]['播音部'] = sound_selected
                used_staff.update(mech_selected + sound_selected)
                department_count[day]['机务部'] = len(mech_selected)
                department_count[day]['播音部'] = len(sound_selected)

        self.schedule = schedule
        self.department_count = department_count

        # 更新表格显示结果，分列显示部门人员
        self.table_widget.setRowCount(0)
        for day in schedule:
            mech_staff = schedule[day]['机务部']
            sound_staff = schedule[day]['播音部']
            total_staff = mech_staff + sound_staff
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem(day))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem(str(len(total_staff))))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem(", ".join(mech_staff) if mech_staff else "无"))
            self.table_widget.setItem(row_position, 3, QTableWidgetItem(", ".join(sound_staff) if sound_staff else "无"))
            dept_info = f"机务部: {department_count[day]['机务部']}, 播音部: {department_count[day]['播音部']}"
            self.table_widget.setItem(row_position, 4, QTableWidgetItem(dept_info))

        # 显示结果反馈
        if errors:
            QMessageBox.warning(self, "排班警告", "\n".join(errors))
        else:
            QMessageBox.information(self, "成功", "排班成功生成！")

    def save_schedule(self):
        """保存排班结果到 Excel 文件"""
        if not self.schedule:
            QMessageBox.warning(self, "警告", "请先生成排班结果")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存排班结果", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            # 自动添加 .xlsx 扩展名
            if not file_name.endswith('.xlsx'):
                file_name += '.xlsx'
            try:
                data = []
                for day in self.schedule:
                    mech_staff = self.schedule[day]['机务部']
                    sound_staff = self.schedule[day]['播音部']
                    total_staff = mech_staff + sound_staff
                    data.append({
                        '工作日': day,
                        '值班人数': len(total_staff),
                        '机务部人员': ", ".join(mech_staff) if mech_staff else "无",
                        '播音部人员': ", ".join(sound_staff) if sound_staff else "无",
                        '部门分配': f"机务部: {self.department_count[day]['机务部']}, 播音部: {self.department_count[day]['播音部']}"
                    })
                df_result = pd.DataFrame(data)
                df_result.to_excel(file_name, index=False)
                QMessageBox.information(self, "成功", f"排班结果成功保存到\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件失败:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SchedulerUI()
    window.show()
    sys.exit(app.exec_())