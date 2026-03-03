from nicegui import ui

from i18n import LANGUAGES, current_lang, t


def build_header(layout, toggle_mini, on_language_change):
    with ui.header(elevated=True).classes("header-bg") as header:
        layout.header = header
        ui.image('assets/wmo-banner.png').props('fit=cover alt=""').classes("header-banner")
        ui.image('assets/wmo-foot.png').props('alt=""').classes("header-divider")
        ui.image('assets/logo.png').props('alt="WIS2 Downloader"').classes("header-logo")
        with ui.row().classes("header-toolbar"):
            ui.button(icon='menu').props(
                f'flat round color=white aria-label="{t("aria.toggle_nav")}"'
            ).on('click', toggle_mini)
            ui.space()
            ui.select(
                options=LANGUAGES,
                value=current_lang(),
            ).props('dense borderless dark').classes('lang-select').on(
                'update:model-value',
                lambda e: on_language_change(e.sender.value),
            )
