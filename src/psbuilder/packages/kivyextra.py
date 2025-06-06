from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage, CythonSwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import (
    ffmpeg,
    ffpyplayer,
    matplotlib,
    kiwisolver
)

PackageDependency = SwiftTarget.PackageDependency

class KE_Target(SwiftTarget):
    
    @property
    def name(self):
        return self.__class__.__name__

class KiwiSolver(KE_Target):

    recipes = [
        kiwisolver.recipe
    ]
    
class FFMpeg(KE_Target):

    recipes = [
        ffmpeg.recipe
    ]
    
class FFPyplayer(KE_Target):

    recipes = [
        ffpyplayer.recipe
    ]
    
class MatPlotLib(KE_Target):

    recipes = [
        matplotlib.recipe
    ]

all_targets= [
    KiwiSolver(),
    FFMpeg(),
    FFPyplayer(),
    MatPlotLib()
]

def create_products():
    for target in all_targets:
        yield SwiftPackage.Product(target.name, [target.name])

class KivyExtra(CythonSwiftPackage):
    
    include_pythoncore = True
    #include_pythonswiftlink = True
    
    repo_url = "https://github.com/kv-swift/KivyExtra"
    
    products = list(create_products())
    
    targets = all_targets
    
    
    site_package_targets = [
        "kiwisolver.cpython-311-darwin.so", "kiwisolver.cpython-311-darwin.so.libs",
        "ffpyplayer", "matplotlib"
    ]


package = KivyExtra()