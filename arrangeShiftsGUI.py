import sys
import pandas as pd
import random
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
        self.setGeometry(100, 100, 800, 600)
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
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(["工作日", "值班人数", "人员列表"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            self.file_path = file_name
            self.file_line_edit.setText(file_name)

    def generate_schedule(self):
        if not self.file_path:
            QMessageBox.warning(self, "警告", "请先选择Excel文件")
            return

        try:
            # 读取 Excel 文件（假设文件中没有标题行，第一列为姓名，第二列为空闲天数）
            df = pd.read_excel(self.file_path, header=None, names=['姓名', '空闲天数'])
        except Exception as e:
            QMessageBox.critical(self, "错误", f"读取 Excel 文件失败:\n{str(e)}")
            return

        # 初始化数据
        available_days = defaultdict(list)
        shifts_count = {row['姓名']: 0 for _, row in df.iterrows()}
        schedule = {'周一': [], '周二': [], '周三': [], '周四': [], '周五': []}

        # 数据清洗（保持原逻辑）
        for _, row in df.iterrows():
            name = row['姓名']
            raw_days = str(row['空闲天数']).replace("星期", "").replace("周", "").split(',')
            days = [d.strip() for d in raw_days if d.strip()]
            days = [f"周{day}" for day in days if day in ['一','二','三','四','五']]
            for day in days:
                available_days[day].append(name)

        # 按可用人数排序
        sorted_days = sorted(schedule.keys(), key=lambda x: len(available_days[x]))

        errors = []
        # 修正后的排班逻辑
        for day in sorted_days:
            candidates = available_days[day]
            if len(candidates) < 3:
                errors.append(f"{day} 可用人数不足3人，跳过排班")
                continue

            required = 4 if len(candidates) >= 4 else 3
            random.shuffle(candidates)
            candidates_sorted = sorted(candidates, key=lambda x: shifts_count[x])
            selected = candidates_sorted[:required]
            for person in selected:
                shifts_count[person] += 1
            schedule[day] = selected

        self.schedule = schedule

        # 更新表格显示排班结果
        self.table_widget.setRowCount(0)
        for day, staff in schedule.items():
            row_position = self.table_widget.rowCount()
            self.table_widget.insertRow(row_position)
            self.table_widget.setItem(row_position, 0, QTableWidgetItem(day))
            self.table_widget.setItem(row_position, 1, QTableWidgetItem(str(len(staff))))
            self.table_widget.setItem(row_position, 2, QTableWidgetItem(", ".join(staff)))

        if errors:
            QMessageBox.warning(self, "排班警告", "\n".join(errors))
        else:
            QMessageBox.information(self, "成功", "排班成功生成！")

    def save_schedule(self):
        if not self.schedule:
            QMessageBox.warning(self, "警告", "请先生成排班结果")
            return

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "保存排班结果", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if file_name:
            try:
                data = [{
                    '工作日': day,
                    '值班人数': len(staff),
                    '人员列表': ', '.join(staff)
                } for day, staff in self.schedule.items()]
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
