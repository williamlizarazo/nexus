import shiny
import server as app_server


def test_server_uses_top_level_shiny_req():
    assert app_server.req is shiny.req
