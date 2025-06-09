from .recipe import _Recipe
import hashlib
from os.path import join, dirname, realpath, exists, isdir, basename, splitext
from typing import TypeAlias

class SwiftTarget:
    
    class PackageDependency:
        name: str
        package: str
        condition: dict | None = None
        type: str
        
        def __init__(self, name: str, package: str, _type: str = "target", condition: dict | None = None):
            self.name = name
            self.package = package
            self.condition = condition
            self.type = _type
            
        @staticmethod
        def product(name: str, package: str, condition: dict | None = None) -> "SwiftTarget.PackageDependency":
            SwiftTarget.PackageDependency(name, package, "product", condition)
        
        @staticmethod
        def target(name: str, package: str, condition: dict | None = None) -> "SwiftTarget.PackageDependency":
            SwiftTarget.PackageDependency(name, package, "target", condition)
        
            
        @property
        def dump(self) -> dict:
            data = {
                "name": self.name,
                "package": self.package,
                "type": self.type
            }
            if self.condition:
                data["condition"] = self.condition
            return data
            
    class LinkerSetting:
        kind: str
        name: str
        condition: dict | None = None
        
        def __init__(self, name: str, kind: str = "framework", condition: dict | None = None):
            self.condition = condition
            self.kind = kind
            self.name = name
            
        @property
        def dump(self) -> dict:
            data = {
                "kind": self.kind,
                "name": self.name
            }
            if self.condition:
                data["condition"] = self.condition
            return data
    class Resource:
        kind: str
        path: str
        
        def __init__(self, path: str, kind: str = "copy"):
            self.kind = kind
            self.path = path
            
        @property
        def dump(self) -> dict:
            return {
                "kind": self.kind,
                "path": self.path
            }
            
            
    name: str
    recipes: list[_Recipe] = []
    dependencies: list[PackageDependency | str ] = []
    resources: list[Resource] = []
    #swiftonize_plugin: bool = False
    pyswiftwrapper: bool = False
    
    ios_only: list[str] = []
    macos_only: list[str] = []
    
    linker_libraries: list[LinkerSetting] = []
    
    @property
    def linker_settings(self) -> list[LinkerSetting]:
        output = []
        for recipe in self.recipes:
            if hasattr(recipe, "pbx_frameworks"):
                for pbx in recipe.pbx_frameworks:
                    condition = None
                    if pbx in self.ios_only:
                        condition = {"platform": "ios"}
                    elif pbx in self.macos_only:
                        condition = {"platform": "macos"}
                    output.append(SwiftTarget.LinkerSetting(pbx, condition=condition))
            if hasattr(recipe, "pbx_libraries"):
                for lib in recipe.pbx_libraries:
                    lib: str = lib
                    condition = None
                    if lib in self.ios_only:
                        condition = {"platform": "ios"}
                    elif lib in self.macos_only:
                        condition = {"platform": "macos"}
                    if lib.startswith("lib"):
                        output.append(SwiftTarget.LinkerSetting(lib.removeprefix("lib"),"library", condition=condition))
                    else:
                         output.append(SwiftTarget.LinkerSetting(lib,"library", condition=condition))
        
        return output + self.linker_libraries
    
    @property
    def xcframeworks(self) -> list[str]:
        xcs: list[str] = []
        for recipe in self.recipes:
            xcs.extend(recipe.dist_xcframeworks)
        return xcs
    
    def dump_dep(self) -> list[dict | str]:
        deps = []
        for dep in self.dependencies:
            match dep:
                case str():
                    deps.append({
                        "type": "string",
                        "data": dep,
                        "condition": {"platform": "ios"} if dep in self.ios_only else {"platform": "macos"} if dep in self.macos_only else None
                    })
                case _:
                    deps.append({
                        "type": "dependency",
                        "data": dep.dump
                    })
        for xc in self.xcframeworks:
            fn, ext = splitext(basename(xc))
            deps.append({
                        "type": "string",
                        "data": fn,
                        "condition": {"platform": "ios"} if fn in self.ios_only else {"platform": "macos"} if fn in self.macos_only else None
                    })
        return deps
                    
        
    
    @property
    def dump(self) -> dict:
        plugins = []
        
        # if self.pyswiftwrapper:
            # plugins.append(
            #     {
            #         "name": "PySwiftWrapper",
            #         "package": "PySwiftWrapper"
            #     }
            # )
            # self.dependencies.append(
            #     SwiftTarget.PackageDependency("PySwiftWrapper", "PySwiftWrapper")
            # )
        # if self.swiftonize_plugin:
        #     plugins.append(
        #         {
        #             "name": "Swiftonize",
        #             "package": "SwiftonizePlugin"
        #         }
        #     )
        return {
            "type": "target",
            "data": {
                "name": self.name,
                "dependencies": self.dump_dep(),
                "resources": [res.dump for res in self.resources],
                "linker_settings": [linker.dump for linker in self.linker_settings],
                "plugins": plugins
            }
        }

TargetDependency: TypeAlias = SwiftTarget.PackageDependency    

class BinaryTarget:
    name: str
    file: str
    github: str
    repo: str
    version: str
    
    _sha256: str
        
    def __init__(self,name: str, file: str, github: str, repo: str, version: str):
        self.name = name
        self.file = file
        self.github = github
        self.repo = repo
        self.version = version
        self._sha256 = None
    
    @property
    def url(self) -> str:
        return f"https://github.com/{self.github}/{self.repo}/releases/download/{self.version}/{basename(self.file)}"
    
    def calculate_checksum(self):
        BUF_SIZE = 65536
        sha256 = hashlib.sha256()
        with open(self.file, "rb") as fp:
            while True:
                data = fp.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)
        self._sha256 = sha256.hexdigest()
                
    @property
    def checksum(self) -> str:
        sha = self._sha256
        if sha: return sha
        self.calculate_checksum()
        return self._sha256
    
    @property
    def dump(self) -> dict:
        return {
            "type": "binary",
            "data": {
                "name": self.name,
                "url": self.url,
                "checksum": self.checksum
            }
        }