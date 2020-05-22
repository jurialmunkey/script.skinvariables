import sys
import xbmc
import xbmcvfs


def kodi_log(value, level=0):
    try:
        if isinstance(value, bytes):
            value = value.decode('utf-8')
        logvalue = u'{0}{1}'.format('[script.skinvariables]\n', value)
        if sys.version_info < (3, 0):
            logvalue = logvalue.encode('utf-8', 'ignore')
        if level == 1:
            xbmc.log(logvalue, level=xbmc.LOGNOTICE)
        else:
            xbmc.log(logvalue, level=xbmc.LOGDEBUG)
    except Exception as exc:
        xbmc.log(u'Logging Error: {}'.format(exc), level=xbmc.LOGNOTICE)


def load_filecontent(filename=None):
    try:
        vfs_file = xbmcvfs.File(filename)
        content = vfs_file.read()
    finally:
        vfs_file.close()
    return content


def try_parse_int(string):
    '''helper to parse int from string without erroring on empty or misformed string'''
    try:
        return int(string)
    except Exception:
        return 0


def try_decode_string(string, encoding='utf-8'):
    """helper to decode strings for PY 2 """
    if sys.version_info.major == 3:
        return string
    try:
        return string.decode(encoding)
    except Exception:
        return string


def try_encode_string(string, encoding='utf-8'):
    """helper to encode strings for PY 2 """
    if sys.version_info.major == 3:
        return string
    try:
        return string.encode(encoding)
    except Exception:
        return string
