from nicegui import ui


def build_right_sidebar(layout):
    is_mini = False
    props = f"{'mini ' if is_mini else ''}width=250 behavior=desktop"


    with ui.element("div").classes("bg-base-100 p-4 right-sidebar") as right_sidebar:
        layout.right_sidebar = right_sidebar
    right_sidebar.set_visibility(False)
