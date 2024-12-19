from os.path import join, dirname, realpath, exists, isdir, basename, splitext
import json
import importlib

from kivy_ios.toolchain import logger
from kivy_ios.toolchain import Recipe as _Recipe



class Recipe(_Recipe):
    
    pbx_frameworks: list[str]
    
    def execute(self):
        super().execute()
        
    def add_headers_to_xcframework(self):
        self.get_include_dir
    
    @classmethod
    def get_recipe(cls, name, ctx):
        if not hasattr(cls, "recipes"):
            cls.recipes = {}

        if '==' in name:
            name, version = name.split('==')
        else:
            version = None

        if name in cls.recipes:
            recipe = cls.recipes[name]
        else:
            for custom_recipe_path in ctx.custom_recipes_paths:
                if custom_recipe_path.split("/")[-1] == name:
                    spec = importlib.util.spec_from_file_location(
                        name, join(custom_recipe_path, "__init__.py")
                    )
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    recipe = mod.recipe
                    recipe.recipe_dir = custom_recipe_path
                    logger.info(f"A custom version for recipe '{name}' found in folder {custom_recipe_path}")
                    break
            else:
                logger.info(f"Using the bundled version for recipe '{name}'")
                mod = importlib.import_module(f"kivy_ios.recipes.{name}")
                recipe = mod.recipe
                recipe.recipe_dir = join(ctx.root_dir, "recipes", name)

            recipe.init_after_import(ctx)

        if version:
            recipe.version = version

        return recipe


