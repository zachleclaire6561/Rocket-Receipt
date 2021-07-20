import time
import re

class timing:
    @staticmethod
    def has_exp(year, month, day, hour, mins, sec, exp_buff):
        months = {
            'Jan': 1,
            'Feb': 2,
            'Mar': 3,
            'Apr': 4,
            'May': 5,
            'Jun': 6,
            'Jul': 7,
            'Aug': 8,
            'Sep': 9,
            'Oct': 10, 
            'Nov': 11, 
            'Dec': 12
        }
        times = re.search(r'([a-zA-Z]*)\s*([a-zA-Z]*)\s*([0-9]*)\s*([0-9]*):([0-9]*):([0-9]*)\s*([0-9]*)', time.asctime())
        hr_min_sec = [times.group(4), times.group(5), times.group(6)]
        curr_year = times.group(7)
        curr_month = times.group(2)
        curr_day = times.group(3)
        
        # compares times
        return not (int(curr_year) < year \
        or (int(curr_year) == year and months.get(curr_month) < month) \
        or (int(curr_year) == year and months.get(curr_month) == month and int(curr_day) < day) \
        or (int(curr_year) == year and months.get(curr_month) == month and int(curr_day) == day and int(hr_min_sec[0]) < hour) \
        or (int(curr_year) == year and months.get(curr_month) == month and int(curr_day) == day and int(hr_min_sec[1]) < mins ) \
        or (int(curr_year) == year and months.get(curr_month) == month and int(curr_day) == day and int(hr_min_sec[1]) == mins and int(hr_min_sec[2])+exp_buff < sec))

#print(timing.has_exp(2021, 7, 7, 10, 27, 10, 10))