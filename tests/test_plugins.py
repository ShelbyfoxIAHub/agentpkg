from unittest.mock import patch, MagicMock
from pathlib import Path
from agentpkg.plugins import load_plugins

def test_load_plugins_mock():
    # Simular un plugin externo registrado para la extension .custom
    mock_ep = MagicMock()
    mock_ep.name = ".custom"
    mock_ep.load.return_value = lambda path: "Texto extraido por plugin personalizado"
    
    with patch("agentpkg.plugins.entry_points") as mock_entry_points:
        mock_eps = MagicMock()
        mock_eps.select.return_value = [mock_ep]
        mock_entry_points.return_value = mock_eps
        
        plugins = load_plugins("agentpkg.parsers")
        assert ".custom" in plugins
        assert plugins[".custom"](Path("archivo.custom")) == "Texto extraido por plugin personalizado"
