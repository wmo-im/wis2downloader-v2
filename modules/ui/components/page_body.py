from nicegui import ui

from components.right_sidebar import build_right_sidebar


def build_page_body(layout):
    with ui.element("div").classes("flex flex-row h-full w-full"):
        with ui.element("div").classes("flex-grow min-w-0 bg-base-100 h-full p-4 overflow-y-auto") as content:
            layout.content = content
        build_right_sidebar(layout)
