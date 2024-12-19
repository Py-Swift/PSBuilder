from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import numpy

PackageDependency = SwiftTarget.PackageDependency

class KivyNumpyTarget(SwiftTarget):
    
    name = "KivyNumpy"
    
    recipes = [
        numpy.recipe
    ]


class KivyNumpy(CythonSwiftPackage):
    
    include_pythoncore = True
    #include_pythonswiftlink = True
    
    repo_url = "https://github.com/kivyswiftlink/KivyNumpy"
    
    products = [
        SwiftPackage.Product("KivyNumpy", ["KivyNumpy"])
    ]
    
    targets = [
        KivyNumpyTarget()
    ]
    
    
    site_package_targets = [
        "numpy", f"numpy-{numpy.recipe.version}-py3.11.egg-info"
    ]


package = KivyNumpy()