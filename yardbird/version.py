VERSION = 'Ah-Leu-Cha'
TARGET = '0.1'

def sdist_ver():
    import re
    if VERSION == TARGET:
        return VERSION
    codename = re.sub(r'\W', '.', VERSION)
    return '%s~%s' % ( TARGET, codename )
