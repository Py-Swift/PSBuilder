from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import python3, openssl, libffi

from os.path import basename, join
import plistlib
import shutil
import os

PackageDependency = SwiftTarget.PackageDependency

class PythonCoreTarget(SwiftTarget):
    
    name = "PythonCore"
    
    dependencies = ["PythonLibrary"]
    
    recipes = [
        python3.recipe,
        openssl.recipe,
        libffi.recipe
    ]

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
        SwiftPackage.Product("PythonCore", ["PythonCore"]),
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

    module_map = """
module Python [extern_c] {
	umbrella header "Python.h"
	export *
	link "Python"
}
"""

package = PythonCore()