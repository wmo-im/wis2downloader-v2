from nicegui import ui

from data import gdc_records, topic_hierarchy
from i18n import t
from views.shared import on_topics_picked, clean_page


# ---------------------------------------------------------------------------
# Topic hierarchy → ui.tree conversion
# ---------------------------------------------------------------------------

def _to_tree_nodes(topic_dict: dict, path: str = '') -> list[dict]:
    """Convert the topic hierarchy dict into the node list format expected by ui.tree."""
    nodes = []
    for label, value in sorted(topic_dict.items()):
        node_path = f"{path}/{label}" if path else label
        if "children" in value:
            nodes.append({
                "id": node_path + "/#",
                "label": label,
                "children": _to_tree_nodes(value["children"], node_path),
            })
        else:
            nodes.append({
                "id": node_path,
                "label": label,
            })
    return nodes


# ---------------------------------------------------------------------------
# GDC scraper — builds state.features + tree widget
# ---------------------------------------------------------------------------

async def scrape_topics_tree(state, layout, tree_area):
    clean_page(state, layout)
    tree_area.clear()
    with tree_area:
        filter_input = ui.input(label=t('tree.filter_label'))
        tree_widget = ui.tree(
            _to_tree_nodes(topic_hierarchy()), label_key='label',
            on_select=lambda e: on_topics_picked(e, state, layout),
        )
        filter_input.bind_value_to(tree_widget, 'filter')


# ---------------------------------------------------------------------------
# View entry point
# ---------------------------------------------------------------------------

def render(container, state, layout):
    clean_page(state, layout)
    with container:
        ui.label(t('tree.title')).classes("page-title")

        if not any(gdc_records.values()):
            with ui.card().classes("info-card"):
                ui.icon('info').classes("info-card-icon")
                ui.label(t('catalogue.not_loaded')).classes("text-h6")
                ui.label(t('catalogue.not_loaded_msg')).classes("text-body2 text-grey-7")
            return

        with ui.scroll_area().classes("tree-scroll") as tree_area:
            ui.label(t('tree.loading')).classes("text-body2 text-grey-7")

        ui.timer(0.1, lambda: scrape_topics_tree(state, layout, tree_area), once=True)
