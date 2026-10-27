import sys
if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
else:
    from importlib_metadata import entry_points

def load_plugins(group_name: str) -> dict:
    """Descubre y carga dinamicamente plugins registrados en pyproject.toml / setup.py."""
    discovered = {}
    try:
        eps = entry_points()
        group_eps = eps.select(group=group_name) if hasattr(eps, "select") else eps.get(group_name, [])
        for ep in group_eps:
            try:
                discovered[ep.name] = ep.load()
            except Exception as e:
                print(f"Advertencia: No se pudo cargar el plugin '{ep.name}': {e}")
    except Exception as e:
        print(f"Advertencia: Error al escanear el grupo '{group_name}': {e}")
    return discovered
