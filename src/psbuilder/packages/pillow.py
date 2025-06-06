from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import pillow

PackageDependency = SwiftTarget.PackageDependency

class PillowTarget(SwiftTarget):
    
    name = "Pillow"
    
    dependencies = [
        PackageDependency("libjpeg", "ImageCore"),
        PackageDependency("freetype", "FreeType"),
    ]
    
    recipes = [
        pillow.recipe
    ]


class Pillow(CythonSwiftPackage):
    
    include_pythoncore = True
    include_pythonswiftlink = True
    
    products = [
            SwiftPackage.Product("Pillow", ["Pillow"]),
        ]

    targets = [
        PillowTarget()
    ]
    
    @property
    def dependencies(self) -> list[SwiftPackage.Dependency]:
        return [
            SwiftPackage.Dependency("https://github.com/kv-swift/ImageCore", version=self.version),
            SwiftPackage.Dependency("https://github.com/kv-swift/FreeType", version=self.version)
        ]
    
    site_package_targets = [
        "PIL", f"pillow-{pillow.recipe.version}-py3.11.egg-info"
    ]


package = Pillow()