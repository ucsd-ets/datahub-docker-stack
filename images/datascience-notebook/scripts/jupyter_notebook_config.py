import os

if 'NB_UMASK' in os.environ:
    os.umask(int(os.environ['NB_UMASK'], 8))
    