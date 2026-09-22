import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


MODULES = (
    (
        "modules/research_dashboard/server.py",
        "research_dashboard_server",
    ),
    (
        "modules/episodic/server.py",
        "episodic_server",
    ),
    (
        "modules/diagnostics/server.py",
        "diagnostics_server",
    ),
)


def _tree(relative_path: str):
    path = ROOT / relative_path
    return ast.parse(
        path.read_text(encoding="utf-8-sig")
    )


def _function_parameters(
    relative_path: str,
    function_name: str,
):
    tree = _tree(relative_path)

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == function_name
        ):
            return {
                arg.arg
                for arg in (
                    list(node.args.args)
                    + list(node.args.kwonlyargs)
                )
            }

    raise AssertionError(
        f"No se encontró {function_name}"
    )


def _server_passes_auth_callback(
    called_function: str,
) -> bool:
    tree = _tree("server.py")

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        if not isinstance(node.func, ast.Name):
            continue

        if node.func.id != called_function:
            continue

        if any(
            keyword.arg == "is_authenticated"
            for keyword in node.keywords
        ):
            return True

    return False


def test_data_modules_require_authentication_callback():
    for path, function_name in MODULES:
        parameters = _function_parameters(
            path,
            function_name,
        )

        assert "is_authenticated" in parameters


def test_data_modules_contain_server_side_auth_guard():
    for path, _ in MODULES:
        source = (
            ROOT
            .joinpath(path)
            .read_text(encoding="utf-8-sig")
        )

        assert "if not is_authenticated()" in source


def test_root_server_passes_authentication_callback():
    for function_name in (
        "research_dashboard_server",
        "episodic_server",
        "diagnostics_server",
    ):
        assert _server_passes_auth_callback(
            function_name
        )
