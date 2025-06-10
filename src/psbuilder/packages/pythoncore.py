from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import python3, openssl, libffi

from os.path import basename, join, exists
import plistlib
import shutil
import os

from urllib.request import urlretrieve

PackageDependency = SwiftTarget.PackageDependency

class PythonCoreTarget(SwiftTarget):
    
    name = "PythonCore"
    
    
    
    dependencies = [
        
    ]
    
    linker_libraries = [
        SwiftTarget.LinkerSetting("ncurses", "library", {"platform": "macos"}),
    ]
    
    recipes = [
        python3.recipe,
        openssl.recipe,
        libffi.recipe
    ]
    
    ios_only = [
        "libssl",
        "libcrypto",
        "libffi"
    ]
    
    macos_only = [
        "ncurses"
    ]
    

class PythonLibrary(SwiftTarget):
    
    name = "PythonLibrary"
    
    resources = [SwiftTarget.Resource("lib")]
    
    

########################################################################################

class PythonCore(SwiftPackage):
    
    repo_url = "https://github.com/kv-swift/PythonCore"
    #include_pythonswiftlink = True
    py_swift_version = "311.0.3"
    
    products = [
        SwiftPackage.Product("PythonCore", [
            "PythonCore", "libpython3.11", 
            # "libssl", 
            # "libcrypto", 
            # "libffi"
        ]),
        SwiftPackage.Product("PythonLibrary", ["PythonLibrary"])
    ]
    
    targets = [
        PythonCoreTarget(),
        #PythonExtra(),
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
            plist_data: dict = plistlib.load(rp)
        
        available_libraries: list = plist_data.get("AvailableLibraries", [])
        available_libraries.append(
            {
                "HeadersPath": header_fn,
                "LibraryIdentifier": "macos-arm64_x86_64",
                "LibraryPath": "libPython3.11.a",
                "BinaryPath": "libPython3.11.a",
                "SupportedArchitectures": ["arm64", "x86_64"],
                "SupportedPlatform": "macos"
            }
        )
        for lib in available_libraries:
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
            xc_target = join(xc_plat, py_headers_fn)
            if os.path.exists(xc_target): continue
            shutil.copytree(
                py_headers,
                xc_target
            )
        
        self.process_plist(
            join(xc,"Info.plist"),
            py_headers_fn
        )
        python_zip = join(xc, "Python.zip")
        python_zip = urlretrieve(f"https://github.com/Py-Swift/PythonCore/releases/download/{self.py_swift_version}/Python.zip", python_zip)[0]
        print(f"Downloaded Python.zip to {python_zip}")
        unpack_dir = join(xc, "Python.xcframework")
        shutil.unpack_archive(python_zip, xc)
        shutil.copytree(
            join(unpack_dir, "macos-arm64_x86_64"),
            join(xc, "macos-arm64_x86_64"),
        )
        shutil.move(
            join(xc, "macos-arm64_x86_64", "Headers"),
            join(xc, "macos-arm64_x86_64", "python3.11")
        )
        
        os.remove(python_zip)
    
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
        to_remove = join(sp_lib, "python3.11")
        if exists(to_remove):
            shutil.rmtree(to_remove)
            
        python_zip = join(export_dir, "macos-python-stdlib.zip")
        python_zip = urlretrieve(f"https://github.com/Py-Swift/PythonCore/releases/download/{self.py_swift_version}/macos-python-stdlib.zip", python_zip)[0]

    module_map = """
module Python [extern_c] {
	umbrella header "Python.h"
	export *
	link "Python"
}
"""

package = PythonCore()