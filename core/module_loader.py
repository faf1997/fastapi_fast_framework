import os
import ast
import importlib.util
import logging
import sys
from .orm.registry import Registry

logger = logging.getLogger(__name__)

class ModuleLoader:
    def __init__(self, modules_path):
        self.modules_path = modules_path
        self.modules = {}
        self.loaded_modules = {}

    def get_routers(self):
        routers = []
        for name, module in self.loaded_modules.items():
            # Check if module has controllers submodule
            if hasattr(module, 'controllers'):
                controllers = module.controllers
                if hasattr(controllers, 'router'):
                     routers.append(controllers.router)
        return routers


    def load_modules(self, env):
        self._discover_modules()
        sorted_modules = self._sort_modules()
        
        for module_name in sorted_modules:
            logger.info(f"Loading module: {module_name}")
            self._import_module(module_name)
        
        # After loading all processing models, run auto_init
        self._init_models(env)

    def _discover_modules(self):
        if not os.path.exists(self.modules_path):
            return
            
        for item in os.listdir(self.modules_path):
            module_path = os.path.join(self.modules_path, item)
            manifest_path = os.path.join(module_path, '__manifest__.py')
            if os.path.isdir(module_path) and os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    try:
                        manifest = ast.literal_eval(f.read())
                        self.modules[item] = manifest
                    except Exception as e:
                        logger.error(f"Failed to load manifest for {item}: {e}")

    def _sort_modules(self):
        # Topological sort for dependencies
        # This is a naive implementation
        loaded = []
        to_load = list(self.modules.keys())
        
        # Simple loop to resolve dependencies
        # In a real scenario, we need cycle detection and proper graph sort
        changed = True
        while to_load and changed:
            changed = False
            for module in list(to_load):
                depends = self.modules[module].get('depends', [])
                if all(dep in loaded for dep in depends):
                    loaded.append(module)
                    to_load.remove(module)
                    changed = True
        
        # If any left, just load them (circular deps or missing deps handling needed)
        if to_load:
            logger.warning(f"Modules with unresolved dependencies: {to_load}")
            loaded.extend(to_load)
            
        return loaded

    def _import_module(self, module_name):
        module_path = os.path.join(self.modules_path, module_name)
        
        # Recursively import all .py files in the module directory to ensure models are registered
        # Standard Odoo structure usually has an __init__.py that imports models
        # We will rely on __init__.py chains
        spec = importlib.util.spec_from_file_location(module_name, os.path.join(module_path, '__init__.py'))
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            self.loaded_modules[module_name] = module

    def _init_models(self, env):
        # Initialize tables
        for name, cls in Registry.models().items():
            if hasattr(cls, '_auto_init'):
                logger.info(f"Initializing model schema: {name}")
                cls._auto_init(env)

        # Bootstrap Admin
        # logger.info(f"Registry models: {list(Registry.models().keys())}")
        ResUsers = Registry.get('res.users')
        if ResUsers:
             # logger.info(f"ResUsers found: {ResUsers}")
             if hasattr(ResUsers, '_bootstrap_admin'):
                 logger.info("Bootstrapping Admin User")
                 ResUsers._bootstrap_admin(env)
             else:
                 logger.error("ResUsers has no _bootstrap_admin")
        else:
             logger.error("ResUsers NOT found in Registry")


