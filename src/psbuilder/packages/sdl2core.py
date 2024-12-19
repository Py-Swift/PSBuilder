from psbuilder.targets import SwiftTarget
from psbuilder.package import SwiftPackage

from kivy_ios.toolchain import Recipe
from kivy_ios.recipes import sdl2, sdl2_image, sdl2_mixer, sdl2_ttf

PackageDependency = SwiftTarget.PackageDependency

class SDL2CoreTarget(SwiftTarget):
    
    name = "SDL2Core"
    
    recipes = [
        sdl2.recipe,
        sdl2_image.recipe,
        sdl2_mixer.recipe,
        sdl2_ttf.recipe
    ]
    
    dependencies = [
        PackageDependency("libpng", "ImageCore"),
    ]


class SDL2Core(SwiftPackage):
    
    repo_url = "https://github.com/kivyswiftlink/SDL2Core"
    
    include_pythoncore = True
    include_pythonswiftlink = True
    
    products = [
        SwiftPackage.Product("SDL2Core", ["SDL2Core"])
    ]
    
    targets = [
        SDL2CoreTarget()
    ]
    
    @property
    def dependencies(self) -> list[SwiftPackage.Dependency]:
        return [
            #SwiftPackage.Dependency("https://github.com/KivySwiftLink/SDL2Core", version=self.version)
        ]



package = SDL2Core()