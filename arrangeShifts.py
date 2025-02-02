import pandas as pd
import random
from collections import defaultdict

df = pd.read_excel('index.xlsx', header=None, names=['姓名', '空闲天数'])

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

# 修正后的排班逻辑
for day in sorted_days:
    candidates = available_days[day]
    
    if len(candidates) < 3:
        print(f"错误：{day} 可用人数不足3人，跳过排班")
        continue
    
    required = 4 if len(candidates) >=4 else 3
    random.shuffle(candidates)
    candidates_sorted = sorted(candidates, key=lambda x: shifts_count[x])
    
    selected = candidates_sorted[:required]
    
    for person in selected:
        shifts_count[person] += 1
    
    schedule[day] = selected

# 输出结果（保持原逻辑）
pd.DataFrame([{
    '工作日': day,
    '值班人数': len(staff),
    '人员列表': ', '.join(staff)
} for day, staff in schedule.items()]).to_excel('排班结果.xlsx', index=False)