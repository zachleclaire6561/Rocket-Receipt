from driveUtils import driveUtils
import sched, time

def update(util):
    util.updateDirectory()


def main():
    scheduler = sched.scheduler(time.time, time.sleep)

    util = driveUtils()
        
    print('script initialized')
    scheduler.enter(1, 1, update, kwargs= {'util':util})
    scheduler.run()

main()