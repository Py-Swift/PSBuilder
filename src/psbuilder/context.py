from os.path import join, dirname, realpath, exists, isdir, basename, splitext
from os import listdir, unlink, makedirs, environ, chdir, getcwd, walk

from kivy_ios.toolchain import Context as Context
from kivy_ios.toolchain import JsonStore
from kivy_ios.toolchain import iPhoneOSARM64Platform, iPhoneSimulatorx86_64Platform, iPhoneSimulatorARM64Platform

initial_working_directory = getcwd()

class PackageContext(Context):
    
    package_state: JsonStore
    site_packages_root: str
    
    def __init__(self):
        super().__init__()
        self.packages_state = JsonStore(join(self.swift_packages, "packages_state.db"))
        platforms = [
            iPhoneOSARM64Platform(self),
            iPhoneSimulatorARM64Platform(self),
            iPhoneSimulatorx86_64Platform(self),
        ]
        self.supported_platforms = [*platforms]
        self.selected_platforms = [*platforms]
        
        self.site_packages_root = join(self.dist_dir, "root/python3/lib/python3.11/site-packages")
        #self.package_state = JsonStore(join(self.dist_dir, "state.db"))
        
    
    
    @property
    def swift_packages(self) -> str:
        return join(initial_working_directory, "swift_packages")


    