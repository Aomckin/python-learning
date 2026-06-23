class Title:
    def get_title(self, tasks):
        total = sum(t.completed_count for t in tasks)

        if total >= 10:
            return "任务支配者 🐉"
        elif total >= 5:
            return "熟练执行者 ⚙️"
        elif total >= 1:
            return "初学者 🌱"
        return "无称号"
