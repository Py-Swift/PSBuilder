from psbuilder.targets import SwiftTarget
from psbuilder.package import CythonSwiftPackage, SwiftPackage


from kivy_ios.toolchain import Recipe
from kivy_ios.recipes.kivy import KivyRecipe

PackageDependency = SwiftTarget.PackageDependency

class KivyTarget(SwiftTarget):
    
    name = "KivyCore"
    
    swiftonize_plugin = False
    
    recipes = [
        KivyRecipe()
    ]

    dependencies = [
        PackageDependency("SDL2Core", "SDL2Core"),
        # PackageDependency("SwiftonizeModules", "PythonSwiftLink"),
        PackageDependency("SwiftonizeModules", "PySwiftKit"),
        PackageDependency("PythonCore", "PythonCore")
    ]

class KivyCore(CythonSwiftPackage):
    
    include_pythoncore = True
    include_pythonswiftlink = True
    
    repo_url = "https://github.com/kivyswiftlink/KivyCore"
    
    products = [
        SwiftPackage.Product("KivyCore", ["KivyCore"])
    ]
    
    targets = [
        KivyTarget(),
    ]
    
    dependencies = [
        SwiftPackage.Dependency("https://github.com/KivySwiftLink/SDL2Core", next_major="311.0.0")
    ]

    site_package_targets = [
        "kivy", f"Kivy-{KivyRecipe.version}-py3.11.egg-info"
    ]

package = KivyCore()