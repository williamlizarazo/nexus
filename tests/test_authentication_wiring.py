from modules.authentication import (
    authentication_actor_ui,
    authentication_login_ui,
    authentication_server,
)


def test_authentication_module_exports():
    assert callable(authentication_login_ui)
    assert callable(authentication_actor_ui)
    assert callable(authentication_server)


def test_login_ui_can_be_built():
    component = authentication_login_ui()

    assert component is not None


def test_actor_ui_can_be_built():
    component = authentication_actor_ui()

    assert component is not None
