import cherrypy
import hashlib
from time import time
from threading import Lock
from os.path import getmtime, abspath

import PressUI.cherrypy.PressProduction as PressProduction

__lock = Lock()
# { paths sha1 => { "timestamp" => created timestamp, "dig" => file sha1 }
__stamps = {}
# { file sha1 => file contents }
__contents = {}

def press_static_file(paths):
    global __stamps, __contents

    for path in paths:
        if abspath(path) != path:
            raise AttributeError("Expected absolute paths")

    pdig = hashlib.sha1("\n".join(paths).encode("utf-8")).hexdigest()
    with __lock:
        if __should_rebuild(pdig, paths):
            contents = []
            for path in paths:
                with open(path, "rb") as f:
                    contents.append(f.read())
            contents = b"\n".join(contents)
            dig = hashlib.sha1(contents).hexdigest()
            __contents[dig] = contents
            __stamps[pdig] = {
                "timestamp": time(),
                "dig": dig,
            }
    return __stamps[pdig]["dig"]

def __should_rebuild(pdig, paths):
    if pdig in __stamps:
        if PressProduction.is_production():
            return False
        max_m_time = max([getmtime(path) for path in paths])
        return max_m_time > __stamps[pdig]["timestamp"]
    return True

def press_get_static_file_by_dig(dig, content_type):
    if dig in __contents:
        cherrypy.response.headers["Content-Type"] = content_type
        # 1yr
        cherrypy.response.headers["Cache-Control"] = "private, max-age=31536000"
        cherrypy.response.headers["ETag"] = dig
        return __contents[dig]
    else:
        raise cherrypy.HTTPError(404)