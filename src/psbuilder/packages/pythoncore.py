from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import python3, openssl, libffi

from os.path import basename, join, exists
import plistlib
import shutil
import os

PackageDependency = SwiftTarget.PackageDependency

class PythonCoreTarget(SwiftTarget):
    
    name = "PythonCore"
    
    dependencies = ["PythonExtra"]
    
    recipes = [
        python3.recipe,
        openssl.recipe,
        libffi.recipe
    ]
    
    @property
    def linker_settings(self) -> list[SwiftTarget.LinkerSetting]:
        output = [SwiftTarget.LinkerSetting("libz", "library")]
        for recipe in self.recipes:
            if hasattr(recipe, "pbx_frameworks"):
                for pbx in recipe.pbx_frameworks:
                    output.append(SwiftTarget.LinkerSetting(pbx))
            if hasattr(recipe, "pbx_libraries"):
                for lib in recipe.pbx_libraries:
                    output.append(SwiftTarget.LinkerSetting(lib,"library"))
        
        return output

class PythonLibrary(SwiftTarget):
    
    name = "PythonLibrary"
    
    resources = [SwiftTarget.Resource("lib")]
    
class PythonExtra(SwiftTarget):
    
    name = "PythonExtra"
    
    dependencies = ["libpython3.11"]
    
    
########################################################################################

class PythonCore(SwiftPackage):
    
    repo_url = "https://github.com/kivyswiftlink/PythonCore"
    #include_pythonswiftlink = True
    
    products = [
        SwiftPackage.Product("PythonCore", ["PythonCore", "libpython3.11", 
        "libssl", 
        "libcrypto", 
        "libffi"]),
        SwiftPackage.Product("PythonLibrary", ["PythonLibrary"])
    ]
    
    targets = [
        PythonCoreTarget(),
        PythonExtra(),
        PythonLibrary()
    ]
    
    @property
    def xc_platforms(self) -> list[str]:
        return [
            "ios-arm64",
            "ios-arm64_x86_64-simulator"
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
        py_headers_fn = "python3.11"
        py_headers = join(self.ctx.dist_dir, "root", "python3", "include", py_headers_fn)
        
        with open(join(py_headers, "module.modulemap"), "w") as fp:
            fp.write(self.module_map)
            
        for plat in self.xc_platforms:
            xc_plat = join(xc, plat)
            shutil.copytree(
                py_headers,
                join(xc_plat, py_headers_fn)
            )
        
        self.process_plist(
            join(xc,"Info.plist"),
            py_headers_fn
        )
        
    
    def pre_zip_xc_frameworks(self):
        for xc in self.get_all_xcframeworks():
            xc_name = basename(xc)
            if xc_name.startswith("libpython"):
                self.process_xc(xc)
        return super().pre_zip_xc_frameworks()
    
    def post_package(self):
        export_dir = join(self.swift_package_dir, "export")
        package = join(export_dir, "PythonCore")
        sp_sources = join(package, "Sources")
        
        py_lib_folder = join(sp_sources, "PythonLibrary")
        
        sp_lib = join(py_lib_folder, "lib")
        
        if exists(sp_lib):
            shutil.rmtree(sp_lib)
            
        lib_src = join(self.ctx.dist_dir, "root", "python3", "lib")
        shutil.copytree(lib_src, sp_lib)
        

    module_map = """
module Python [extern_c] {
	umbrella header "Python.h"
	export *
	link "Python"
}
"""

package = PythonCore()