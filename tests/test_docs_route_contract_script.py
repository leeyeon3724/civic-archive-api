import importlib.util
from pathlib import Path


def _load_docs_contract_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "check_docs_routes.py"
    spec = importlib.util.spec_from_file_location("check_docs_routes", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discover_route_files_finds_app_routes():
    module = _load_docs_contract_module()
    route_files = module.discover_route_files(module.APP_ROOT)
    relative_paths = {path.relative_to(module.PROJECT_ROOT).as_posix() for path in route_files}
    assert "app/routes/news.py" in relative_paths
    assert "app/bootstrap/system_routes.py" in relative_paths
    assert "app/observability.py" in relative_paths


def test_extract_code_routes_contains_core_endpoints():
    module = _load_docs_contract_module()
    route_files = module.discover_route_files(module.APP_ROOT)
    code_routes = module.extract_code_routes(route_files)
    assert ("GET", "/api/news") in code_routes
    assert ("POST", "/api/news") in code_routes
    assert ("GET", "/health/ready") in code_routes
    assert ("GET", "/metrics") in code_routes
