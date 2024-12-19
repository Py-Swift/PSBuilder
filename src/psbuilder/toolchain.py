#!/usr/bin/env python3
import argparse
import platform
import sys
from sys import stdout
from os.path import join, dirname, realpath, exists, isdir, basename, splitext
from os import listdir, unlink, makedirs, environ, chdir, getcwd, walk
import sh
import zipfile
import tarfile
import importlib
import io
import json
import shutil
import fnmatch
import tempfile
import time
from contextlib import suppress
from datetime import datetime
from pprint import pformat
import logging
import urllib.request
import hashlib


from kivy_ios.toolchain import Context, ToolchainCL, GenericPlatform, logger, JsonStore

from kivy_ios.toolchain import Recipe, Graph, JsonStore
from kivy_ios.toolchain import CythonRecipe as _CythonRecipe
from kivy_ios.toolchain import build_recipes


from .targets import SwiftTarget
from .context import PackageContext
from .package import SwiftPackage




def generate_packages(packages: list[str], ctx: PackageContext, **kw):
    version: str | None = kw.pop("version", None)
    logger.info(f"generate_packages: {packages}")
    #ctx.wanted_recipes = names[:]
    packages_to_load = packages
    packages_loaded = []
    to_run: list[SwiftPackage] = []
    while packages:
        name = packages_to_load.pop(0)
        if name in packages_loaded:
            continue
        try:
            package = SwiftPackage.get_package(name, ctx)
            packages_loaded.append(name)
        except KeyError:
            logger.error("No recipe named {}".format(name))
            sys.exit(1)
        
        to_run.append(package)
    
    recipes_to_build = []
    for package in to_run:
        package.init_with_ctx(ctx)
        
        for t in package.targets:
            for recipe in t.recipes:
                recipes_to_build.append(recipe.name)
    
    build_recipes(recipes_to_build, ctx)
        
    for package in to_run:
        if version:
            package.version = version
        package.execute()
        
    

def build_recipes(names, ctx):
    # gather all the dependencies
    logger.info("Want to build {}".format(names))
    graph = Graph()
    ctx.wanted_recipes = names[:]
    recipe_to_load = names
    recipe_loaded = []
    while names:
        name = recipe_to_load.pop(0)
        if name in recipe_loaded:
            continue
        try:
            recipe = Recipe.get_recipe(name, ctx)
        except KeyError:
            logger.error("No recipe named {}".format(name))
            sys.exit(1)
        graph.add(name, name)
        logger.info("Loaded recipe {} (depends of {}, optional are {})".format(
            name, recipe.depends, recipe.optional_depends))
        for depend in recipe.depends:
            graph.add(name, depend)
            recipe_to_load += recipe.depends
        for depend in recipe.optional_depends:
            # in case of compilation after the initial one, take in account
            # of the already compiled recipes
            key = "{}.build_all".format(depend)
            if key in ctx.state:
                recipe_to_load.append(name)
                graph.add(name, depend)
            else:
                graph.add_optional(name, depend)
        recipe_loaded.append(name)

    build_order = list(graph.find_order())
    logger.info("Build order is {}".format(build_order))
    recipes = [Recipe.get_recipe(name, ctx) for name in build_order]
    recipes = [recipe for recipe in recipes if not recipe.is_alias]
    recipes_order = [recipe.name for recipe in recipes]
    logger.info("Recipe order is {}".format(recipes_order))
    for recipe in recipes:
        recipe.init_with_ctx(ctx)
    for recipe in recipes:
        recipe.execute()


class PSLToolchainCL(ToolchainCL):
    
    def __init__(self):
        super().__init__()
    
    def build(self):
        ctx = PackageContext()
        parser = argparse.ArgumentParser(
                description="Build the toolchain")
        parser.add_argument("recipe", nargs="+", help="Recipe to compile")
        parser.add_argument("--platform", action="append",
                            help="Restrict compilation specific platform (multiple allowed)")
        parser.add_argument("--concurrency", type=int, default=ctx.num_cores,
                            help="number of concurrent build processes (where supported)")
        parser.add_argument("--no-pigz", action="store_true", default=not bool(ctx.use_pigz),
                            help="do not use pigz for gzip decompression")
        parser.add_argument("--no-pbzip2", action="store_true", default=not bool(ctx.use_pbzip2),
                            help="do not use pbzip2 for bzip2 decompression")
        parser.add_argument("--add-custom-recipe", action="append", default=[],
                            help="Path to custom recipe")
        args = parser.parse_args(sys.argv[2:])

        if args.platform:

            # User requested a specific set of platforms, so we need to reset
            # the list of the selected platforms.
            ctx.selected_platforms = []

            for req_platform in args.platform:

                # if req_platform in [plat.name for plat in ctx.selected_platforms]:
                #     logger.error(f"Platform {req_platform} has been specified multiple times")
                #     sys.exit(1)

                # if req_platform not in [plat.name for plat in ctx.supported_platforms]:
                #     logger.error(f"Platform {req_platform} is not supported")
                #     sys.exit(1)

                ctx.selected_platforms.extend([plat for plat in ctx.supported_platforms if plat.name == req_platform])

            logger.info(f"The following platforms has been requested to build: {ctx.selected_platforms}")

        ctx.num_cores = args.concurrency
        if args.no_pigz:
            ctx.use_pigz = False
        if args.no_pbzip2:
            ctx.use_pbzip2 = False

        self.validate_custom_recipe_paths(ctx, args.add_custom_recipe)

        ctx.use_pigz = ctx.use_pbzip2
        logger.info("Building with {} processes, where supported".format(ctx.num_cores))
        if ctx.use_pigz:
            logger.info("Using pigz to decompress gzip data")
        if ctx.use_pbzip2:
            logger.info("Using pbzip2 to decompress bzip2 data")

        build_recipes(args.recipe, ctx)

    
    
    def swiftpackage(self):
        ctx = PackageContext()
        parser = argparse.ArgumentParser(
                description="Build the toolchain")
        parser.add_argument("package", nargs="+", help="Package to generate")
        parser.add_argument("--export", action="append",
                            help="export destination")
        parser.add_argument("--version", default=None,
                            help="set global version if package accepts its")
        args = parser.parse_args(sys.argv[2:])
        kw = {
            "version": args.version
        }
        if args.package == ["all"]:
            generate_packages(
                [
                   "pythoncore" ,"kivycore", "sdl2core", "imagecore",
                   "kivynumpy", "freetype"
                ],
                ctx,
                **kw
            )
        else:
            generate_packages(args.package, ctx, **kw)
        

def main():
    PSLToolchainCL()


if __name__ == "__main__":
    main()
