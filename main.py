from driveUtils import driveUtils
import sched, time

def update(util):
    if (util.is_creds_expired()):
        util.updateToken()
        print("updating credentials")
    result = util.updateDirectory()
    print(result)


def main():
    scheduler = sched.scheduler(time.time, time.sleep)

    util = driveUtils()

    util.get_creds()
    util.load_user_info()
    
    if (util.get_creds() == None or util.load_user_info() == None):
        print('error: could load information. creds: %s ; user info: %s' % (util.get_creds(), util.load_user_info()))
        return
        
    print('script initialized')
    scheduler.enter(1, 1, update, kwargs= {'util':util})
    scheduler.run()

main()