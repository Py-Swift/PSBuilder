from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import sdl2, sdl2_image, sdl2_mixer, sdl2_ttf

from os.path import basename, join, exists
import os
import plistlib
import shutil


PackageDependency = SwiftTarget.PackageDependency

class SDL2CoreTarget(SwiftTarget):
    
    name = "SDL2Core"
    
    recipes = [
        sdl2.recipe,
        sdl2_image.recipe,
        sdl2_mixer.recipe,
        sdl2_ttf.recipe
    ]
    
    dependencies = [
        PackageDependency.product("libpng", "ImageCore"),
    ]


class SDL2Core(SwiftPackage):
    
    repo_url = "https://github.com/kv-swift/SDL2Core"
    
    include_pythoncore = True
    include_pythonswiftlink = True
    
    products = [
        SwiftPackage.Product("SDL2Core", ["SDL2Core", "libSDL2"])
    ]
    
    targets = [
        SDL2CoreTarget()
    ]
    
    @property
    def xc_platforms(self) -> list[str]:
        return [
            "ios-arm64",
            "ios-arm64_x86_64-simulator"
        ]
    
    @property
    def dependencies(self) -> list[SwiftPackage.Dependency]:
        return [
            SwiftPackage.Dependency("https://github.com/kv-swift/ImageCore", version=self.version)
        ]
        
    def process_plist(self, plist: str, header_fn: str):
        with open(plist, "rb") as rp:
            plist_data = plistlib.load(rp)
        
        for lib in plist_data["AvailableLibraries"]:
            lib["HeadersPath"] = header_fn
        
        with open(plist, "wb") as fp:
            fp.write(
                plistlib.dumps(plist_data)
            )
        
    def process_xc(self, xc: str):
        sdl_header_fn = "sdl2"
        sdl_headers = join(self.ctx.dist_dir, "include", "common", sdl_header_fn)
        
        with open(join(sdl_headers, "module.modulemap"), "w") as fp:
            fp.write(self.module_map)
            
        for plat in self.xc_platforms:
            xc_plat = join(xc, plat)
            xc_target = join(xc_plat, sdl_header_fn)
            if os.path.exists(xc_target): continue
            
            shutil.copytree(
                sdl_headers,
                xc_target
            )
        
        self.process_plist(
            join(xc,"Info.plist"),
            sdl_header_fn
        )
        
    def pre_zip_xc_frameworks(self):
        for xc in self.get_all_xcframeworks():
            xc_name = basename(xc)
            if xc_name == "libSDL2":
                self.process_xc(xc)
        return super().pre_zip_xc_frameworks()

    module_map = """
        module SDL [extern_c] {
            umbrella header "SDL.h"
            export *
            link "SDL"
        }
        """



package = SDL2Core()