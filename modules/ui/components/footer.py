from nicegui import ui

from i18n import t


def build_footer(layout):
    with ui.footer().classes("bg-base-400") as footer:
        layout.footer = footer
        ui.image('assets/wmo-foot.png').props('alt=""').classes("footer-divider")
        ui.label(t('footer.copyright')).classes("footer-copyright")
