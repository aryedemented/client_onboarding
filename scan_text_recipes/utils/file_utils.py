import inspect
import pkgutil
from pydoc import locate
from typing import Dict, Callable, List, Type, Any


def dynamic_import_from_packages(
        packages_path: List[str], predicate: Callable[[type], bool] = None) -> Dict[str, Type[Any]]:
    """
    This function imports dynamically all concrete classes that are located in a list of packages (only one level is
    currently supported for each package)
    :param packages_path: list of packages path that contains all the classes that should be imported
    :param predicate: predicate that returns True for all classes that should be imported
    :return: Dictionary with classes' names as keys and actual classes as values
    """

    classes = {}
    for package_path in packages_path:
        classes.update(dynamic_import_from_package(package_path, predicate))

    return classes


def dynamic_import_from_package(
        package_path: str, predicate: Callable[[type], bool] = None, suppress_errors=False) -> Dict[str, type]:
    """
    This function dynamically imports all concrete classes from a specific package, including sub-packages.
    :param package_path: Package path containing the classes to be imported.
    :param predicate: Function that filters classes to be imported.
    :param suppress_errors: If True, modules that fail to import will be skipped.
    :return: Dictionary with class names as keys and class objects as values.
    """

    # Locate package module
    package = locate(package_path)
    if package is None:
        raise ImportError(f"Package {package_path} not found.")

    # List all modules, including submodules
    modules = []
    for module_info in pkgutil.walk_packages(package.__path__, package_path + "."):
        modules.append(module_info.name)

    if predicate is None:
        predicate = lambda x: True

    classes = {}
    for module in modules:
        try:
            mod = locate(module)
            if mod is None:
                continue
            members = inspect.getmembers(mod)
        except Exception as e:
            if suppress_errors:
                continue
            else:
                raise

        # Iterate through module members to find relevant classes
        for name, cls in members:
            if inspect.isclass(cls) and not inspect.isabstract(cls) and predicate(cls) and name not in classes:
                classes[name] = cls

    return classes
