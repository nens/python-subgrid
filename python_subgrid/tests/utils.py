import psutil
from functools import wraps
def printinfo(f):
    """print info of the being called"""
    # needed because it does not show up if the test segfaults
    # this can probably be done easier
    @wraps(f)
    def wrapper(*args, **kwds):
        print("### running test {f}".format(f=f))
        print("available physical memory before {}".format(psutil.virtual_memory()))
        print("available swap memory before {}".format(psutil.swap_memory()))
        result = f(*args, **kwds)
        print("available physical memory after {}".format(psutil.virtual_memory()))
        print("available swap memory after {}".format(psutil.swap_memory()))

        return result
    return wrapper
