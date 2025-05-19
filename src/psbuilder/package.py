from os.path import join, dirname, realpath, exists, isdir, basename, splitext
from os import listdir, unlink, makedirs, environ, chdir, getcwd, walk
import sh
import shutil
import json
import importlib
import sys
from .context import PackageContext
from .targets import BinaryTarget, SwiftTarget
from .utils import ChangeDir, ensure_dir, cache_execution, zip_to_path
from sh import Command
from typing import Generator
import subprocess
from datetime import datetime


def copy_package_content(cls: "SwiftPackage"):
    print(cls.get_binary_targets)




class SwiftPackage:
    
    class Product:
        name: str
        targets: list[str]
        
        def __init__(self, name: str, targets: list[str]):
            self.name = name
            self.targets = targets
        
        @property
        def dump(self) -> dict:
            return {
                "name": self.name,
                "targets": self.targets
            }
    
    class Dependency:
        url: str
        version: str | None
        next_major: str | None
        next_minor: str | None
        
        
        def __init__(self, url: str, version: str | None = None, next_major: str | None = None, next_minor: str | None = None):
            self.url = url
            self.version = version
            self.next_major = next_major
            self.next_minor = next_minor
            
        @property
        def dump(self) -> dict:
            version = self.version
            major = self.next_major
            minor = self.next_minor
            _type = "extact"
            if major:
                _type = "upToNextMajor"
                version = major
            elif minor:
                _type = "upToNextMinor"
                version = minor
            elif not version:
                version = "0.0.0"
            
            return {
                "type": _type,
                #"data": {
                    "url": self.url,
                    "version": version
                #}
            }
            
            
    ctx: PackageContext | None
    products: list[Product] = []
    dependencies: list[Dependency] = []
    targets: list[SwiftTarget]
    version: str = "311.0.0"
    
    include_pythoncore: bool = False
    include_pythonswiftlink: bool = False
    
    only_include_binary_targets: bool = False
    
    repo_url: str | None = None
    
    @property
    def name(self):
        return self.__class__.__name__
    
    def init_with_ctx(self, ctx: PackageContext):
        self.ctx = ctx
        for target in self.targets:
            for recipe in target.recipes:
                recipe.init_with_ctx(ctx)
    
    @cache_execution
    def execute(self):
        print(self.get_binary_targets)
        ensure_dir(self.swift_package_dir)
        self.pre_package()
        self.copy_files_to_package()
        self.export_package()
        self.post_package()
    
    def pre_zip_dists(self):
        pass
    
    def pre_zip_xc_frameworks(self):
        pass
    
    def pre_package(self):
        pass
    
    def post_package(self):
        pass
        
    def generate_package_swift(self) -> str:
        return str(sh.SwiftPackageWriter("create", join(self.swift_package_dir, "package.json")))
    
    def write_package_swift(self, dir: str):
        with open(join(dir, "Package.swift"), "w") as fp:
            fp.write(self.generate_package_swift())
    
    def copy_files_to_package(self):
        self.zip_xc_frameworks_to_export()
        self.zip_dist_files_to_export()
        with open(join(self.swift_package_dir, "package.json"), "w") as fp:
            json.dump(self.dump, fp)
        
    
    def export_package(self):
        export_dir = join(self.swift_package_dir, "export")
        ensure_dir(export_dir)
        repo_url = self.repo_url
        if repo_url:
            self.create_from_repo(repo_url, export_dir)
        else:
            self.create_new(export_dir)
        
    
    def create_new(self, working_dir: str):
        root = join(working_dir, self.__class__.__name__)
        targets = list(self.targets)
        targets_count = len(targets)
        if targets_count > 0:
            sources = join(root, "Sources")
            for target in targets:
                targ_folder = join(sources, target.name)
                ensure_dir(targ_folder)
                with open(join(targ_folder, f"{target.name}.swift"), "w") as fp:
                    fp.write("")
            
        self.write_package_swift(root)        
        
        
    def create_from_repo(self, url: str, working_dir: str):
        with ChangeDir(working_dir):
            self.clone_url(url)
            self.write_package_swift(basename(url))
    
    @cache_execution
    def clone_url(self, url: str, **kwargs):
        sh.git("clone", url)
    
    @property
    def all_targets(self) -> list[SwiftTarget | BinaryTarget]:
        output: list[SwiftTarget | BinaryTarget] = []
        if not self.only_include_binary_targets:
            output.extend(self.targets)
        for src in self.get_binary_targets:
            output.append(
                BinaryTarget(
                    splitext(basename(src))[0],
                    src,
                    "kivyswiftlink",
                    self.__class__.__name__,
                    self.version
                )
            )
        return output
    
    def get_all_xcframeworks(self):
        for target in self.targets:
            for xc in target.xcframeworks:
                yield xc
    
    @property
    def get_binary_targets(self) -> list[str]:
        bin_targets: list[str] = []
        root = self.swift_package_xcframeworks
        for xc in self.get_all_xcframeworks():
            fn, ext = splitext(basename(xc))
            bin_targets.append(join(root, f"{fn}.zip"))
        
        return bin_targets
    
    @property
    def get_dependencies(self) -> list[Dependency]:
        deps = list(self.dependencies)
        if self.include_pythonswiftlink:
            deps.append(
                # SwiftPackage.Dependency("https://github.com/KivySwiftLink/PythonSwiftLink", next_major="311.1.0")
                SwiftPackage.Dependency("https://github.com/KivySwiftLink/PySwiftKit", next_major="311.0.0")
            )
        if self.include_pythoncore:
            deps.append( 
                SwiftPackage.Dependency("https://github.com/KivySwiftLink/PythonCore", next_major="311.0.0")
            )
        if any([target.pyswiftwrapper for target in self.targets]):
            deps.append(
                # SwiftPackage.Dependency("https://github.com/PythonSwiftLink/SwiftonizePlugin", next_major="0.0.0")
                SwiftPackage.Dependency("https://github.com/PythonSwiftLink/PySwiftWrapper", next_major="0.0.0")
            )
        return deps
    
    @property
    def swift_package_dir(self) -> str:
        return join(self.ctx.swift_packages, self.__class__.__name__)
    
    @property
    def swift_package_xcframeworks(self) -> str:
        return join(self.swift_package_dir, "xcframeworks")
    
    @property
    def swift_package_site(self) -> str:
        return join(self.swift_package_dir, "site-packages")
    
    @property
    def dump(self) -> dict:
        return {
            "name": self.__class__.__name__,
            "products": [p.dump for p in self.products],
            "dependencies": [dep.dump for dep in self.get_dependencies],
            "targets": [target.dump for target in self.all_targets],
            "version": self.version
        }
    
    def get_all_targets_recipes(self):
        for target in self.targets:
            for recipe in target.recipes:
                yield recipe
    
    @cache_execution
    def zip_dist_files_to_export(self):
        root = join(self.swift_package_dir, "dist_files")
        has_dist_files = False
        platforms_to_build = dict()
        for plat in self.ctx.supported_platforms:
            if plat.sdk in platforms_to_build:
                continue
            platforms_to_build[plat.sdk] = plat
        
        for plat in platforms_to_build.values():
            plat_root = join(root, plat.sdk)
            for recipe in self.get_all_targets_recipes():
                recipe_root = join(plat_root, recipe.name)
                ensure_dir(plat_root)
                #with ChangeDir(plat_root):
                for lib in recipe._get_all_libraries():
                    has_dist_files = True
                    library_fn = basename(lib)
                    library_name = library_fn.split(".a")[0]
                    static_fn = join(self.ctx.dist_dir, "lib", plat.sdk, library_fn)
                    try:
                        shutil.copy(static_fn, join(plat_root))
                    except: pass
        if has_dist_files:
            with ChangeDir(self.swift_package_dir):
                zip_to_path("dist_files", "./")
        
        
    @cache_execution
    def zip_xc_frameworks_to_export(self):
        last_path = getcwd()
        xc_export_root = self.swift_package_xcframeworks
        ensure_dir(xc_export_root)
        self.pre_zip_xc_frameworks()
        for xc in self.get_all_xcframeworks():
            chdir(dirname(xc))
            xc_basename = basename(xc)
            fn = splitext(xc_basename)[0]
            zip_name = f"{fn}.zip"
            zipfile = join(xc_export_root, f"{fn}.zip")
            sh.zip("-r", zipfile, xc_basename)
        chdir(last_path)
        
    
            
        
    @classmethod
    def get_package(cls, name, ctx) -> "SwiftPackage":
        # if not hasattr(cls, "recipes"):
        #     cls.recipes = {}

        if '==' in name:
            name, version = name.split('==')
        else:
            version = None

        mod = importlib.import_module(f"psbuilder.packages.{name}")
        package: SwiftPackage = mod.package
        #recipe.recipe_dir = join(ctx.root_dir, "packages", name)

        #recipe.init_after_import(ctx)

        if version:
            package.version = version

        return package
    
    def update_state(self, key, value):
        """
        Update entry in state database. This is usually done in the
        @cache_execution decorator to log an action and its time of occurrence,
        but it needs to be done manually in recipes.
        """
        key_time = "{}.at".format(key)
        self.ctx.state[key] = value
        now_str = str(datetime.utcnow())
        self.ctx.state[key_time] = now_str
        print("New State: {} at {}".format(key, now_str))

PackageDependency = SwiftPackage.Dependency
PackageProduct = SwiftPackage.Product
    
class PythonSwiftPackage(SwiftPackage):
    site_package_targets: list[str]
    
    def copy_files_to_package(self):
        super().copy_files_to_package()
        self.copy_site_package_folder()
        self.zip_site_packages()

    def copy_site_package_folder(self):
        site_packages_dir = self.ctx.site_packages_root
        target_root = self.swift_package_site
        ensure_dir(site_packages_dir)
        
        for target in self.site_package_targets:
            src = join(site_packages_dir, target)
            if exists(src):
                if isdir(src):
                    shutil.copytree(src, join(target_root, target))
                else:
                    shutil.copy(src, target_root)
                    
    def zip_site_packages(self):
        with ChangeDir(self.swift_package_dir):
            #sh.zip("-r", "site-packages", "site-packages.zip")
            zip_to_path("site-packages", "./")
            
    
    
    @property
    def dump(self) -> dict:
        data = super().dump
        data["site_package_targets"] = self.site_package_targets
        return data

class CythonSwiftPackage(PythonSwiftPackage):
    
    ...
    
    
    

    

        
        
                