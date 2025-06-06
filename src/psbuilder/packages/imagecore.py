from psbuilder.targets import SwiftTarget, TargetDependency
from psbuilder.package import SwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import libjpeg, libpng

PackageDependency = SwiftTarget.PackageDependency

class LibJpeg(SwiftTarget):
    
    name = "libjpeg"
    
    recipes = [libjpeg.recipe]

class LibPng(SwiftTarget):
    
    name = "libpng"
    
    recipes = [libpng.recipe]


class ImageCore(SwiftPackage):
    
    only_include_binary_targets = True
    
    repo_url = "https://github.com/kv-swift/ImageCore"
    
    products = [
        SwiftPackage.Product("libpng", ["libpng16"]),
        SwiftPackage.Product("libjpeg", ["libjpeg"])
    ]
    
    targets = [
        LibJpeg(),
        LibPng()
    ]
    



package = ImageCore()