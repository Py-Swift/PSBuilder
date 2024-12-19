from os.path import join, dirname, realpath, exists, isdir, basename, splitext
from os import listdir, unlink, makedirs, environ, chdir, getcwd, walk
from kivy_ios.toolchain import ensure_dir, logger
import json
import sh

class ChangeDir:
    last_path: None
    new_path: None
    
    def __init__(self, path: str):
        self.last_path = None
        self.new_path = path
    
    def __enter__(self):
        self.last_path = getcwd()
        chdir(self.new_path)
        
    
    def __exit__(self, exc_type, exc_value, traceback):
        chdir(self.last_path)
        
        
class JsonStore:
    """Replacement of shelve using json, needed for support python 2 and 3.
    """

    def __init__(self, filename):
        self.filename = filename
        self.data = {}
        if exists(filename):
            try:
                with open(filename, encoding='utf-8') as fd:
                    self.data = json.load(fd)
            except ValueError:
                print("Unable to read the state.db, content will be replaced.")

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self.sync()

    def __delitem__(self, key):
        del self.data[key]
        self.sync()

    def __contains__(self, item):
        return item in self.data

    def get(self, item, default=None):
        return self.data.get(item, default)

    def keys(self):
        return self.data.keys()

    def remove_all(self, prefix):
        for key in tuple(self.data.keys()):
            if not key.startswith(prefix):
                continue
            del self.data[key]
        self.sync()

    def sync(self):
        with open(self.filename, 'w') as fd:
            json.dump(self.data, fd, ensure_ascii=False)
            
            
def cache_execution(f):
    def _cache_execution(self, *args, **kwargs):
        state = self.ctx.packages_state
        key = "{}.{}".format(self.name, f.__name__)
        force = kwargs.pop("force", False)
        if args:
            for arg in args:
                key += ".{}".format(arg)
        if key in state and not force:
            logger.info("Cached result: {} {}. Ignoring".format(f.__name__.capitalize(), self.name))
            return
        logger.info("{} {}".format(f.__name__.capitalize(), self.name))
        f(self, *args, **kwargs)
        self.update_state(key, True)
    return _cache_execution


def zip_to_path(src: str, destination: str):
    sh.zip("-r", join(destination, f"{basename(src)}.zip"), src)