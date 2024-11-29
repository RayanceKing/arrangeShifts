from itertools import combinations

# 每天至少3人、最多4人
MIN_PEOPLE_PER_DAY = 3
MAX_PEOPLE_PER_DAY = 4


def assign_shifts(availability):
    days = ['周一', '周二', '周三', '周四', '周五']
    total_people = len(availability)
    used_people = set()  # 已经被分配的人
    schedule = {day: [] for day in days}  # 初始化排班表

    # 确定需要安排4人的天数和3人的天数
    four_person_days = 2
    three_person_days = len(days) - four_person_days

    def backtrack(day_index, four_days_count):
        """递归地为每天分配班次"""
        if len(used_people) == total_people:  # 所有人都已分配
            return True
        if day_index >= len(days):  # 所有天已处理完
            return False

        day = days[day_index]

        # 找出当天的可用人员且未被分配过
        available_people = [
            person for person in availability if day in availability[person] and person not in used_people
        ]

        # 确定当天的人数要求
        required_people = 4 if four_days_count < four_person_days else 3

        # 尝试所有符合条件的组合
        for combo in combinations(available_people, required_people):
            # 更新状态
            schedule[day] = list(combo)
            used_people.update(combo)

            # 递归处理下一天
            if backtrack(day_index + 1, four_days_count + (required_people == 4)):
                return True

            # 回溯（撤销选择）
            for person in combo:
                used_people.remove(person)
            schedule[day] = []

        return False

    if not backtrack(0, 0):
        print("未找到满足条件的排班方案。")
    return schedule


# 输入：每个人的可用时间（移除18-22号）
availability = {
    1: ['周一', '周二', '周三'],
    2: ['周三'],
    3: ['周二', '周四'],
    4: ['周一', '周三', '周五'],
    5: ['周三', '周四'],
    6: ['周四', '周五'],
    7: ['周二'],
    8: ['周四', '周五'],
    9: ['周一', '周二', '周三', '周五'],
    10: ['周一', '周三', '周五'],
    11: ['周二', '周五'],
    12: ['周四'],
    13: ['周三', '周四', '周五'],
    14: ['周二', '周五'],
    15: ['周三', '周五'],
    16: ['周一', '周二'],
    17: ['周四', '周五']
}

# 执行排班并打印结果
schedule = assign_shifts(availability)
for day, people in schedule.items():
    print(f"{day}: {people}")
