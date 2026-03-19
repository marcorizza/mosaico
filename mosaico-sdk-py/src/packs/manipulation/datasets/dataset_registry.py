from pathlib import Path

from packs.manipulation.contracts import DatasetPlugin
from packs.manipulation.datasets.reassemble import ReassemblePlugin


class DatasetRegistry:
    def __init__(self) -> None:
        self._plugins: list[DatasetPlugin] = []

    def register(self, plugin: DatasetPlugin) -> None:
        self._plugins.append(plugin)

    def resolve(self, root: Path) -> DatasetPlugin:
        for plugin in self._plugins:
            if plugin.supports(root):
                return plugin
        raise ValueError(f"No dataset plugin found for {root}")


def build_default_dataset_registry() -> DatasetRegistry:
    registry = DatasetRegistry()
    registry.register(ReassemblePlugin())
    return registry
