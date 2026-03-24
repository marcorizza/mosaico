import logging

from rich.console import Console
from rich.panel import Panel

from mosaicolabs import MosaicoClient
from packs.manipulation.contracts import SequenceDescriptor

LOGGER = logging.getLogger(__name__)


class UploadReporter:
    def __init__(self, console: Console) -> None:
        self.console = console

    def print_summary(self, original_size: int, remote_size: int) -> None:
        if original_size <= 0:
            LOGGER.warning("Original size is zero; cannot calculate upload summary.")
            return

        ratio = original_size / remote_size if remote_size > 0 else 0.0
        savings = (
            max(0.0, (1 - (remote_size / original_size)) * 100)
            if remote_size > 0
            else 0.0
        )

        summary_text = (
            f"Original Size:  [bold]{self._format_size_mb(original_size):.2f}[/bold]\n"
            f"Remote Size:    [bold]{self._format_size_mb(remote_size):.2f}[/bold]\n"
            f"Ratio:          [bold cyan]{ratio:.2f}x[/bold cyan]\n"
            f"Space Saved:    [bold green]{savings:.1f}%[/bold green]"
        )
        self.console.print(
            Panel(
                summary_text,
                title="[bold]Injection Summary[/bold]",
                expand=False,
                border_style="green",
                padding=1,
                highlight=True,
            )
        )

    def print_verification(
        self, client: MosaicoClient, plans: list[SequenceDescriptor]
    ) -> None:
        self.console.print(
            Panel("[bold green]Verifying Data on Server[/bold green]")
        )
        for plan in plans:
            self._verify_single_sequence(client, plan)

    def _verify_single_sequence(
        self, client: MosaicoClient, plan: SequenceDescriptor
    ) -> None:
        shandler = client.sequence_handler(plan.sequence_name)
        if shandler is None:
            LOGGER.error(
                "Could not retrieve sequence handler for '%s'", plan.sequence_name
            )
            return

        self.console.print(f"• [bold]Sequence Name:[/bold] {shandler.name}")
        self.console.print(
            f"• [bold]Remote Size:[/bold]   {self._format_size_mb(shandler.total_size_bytes):.2f} MB"
        )
        self.console.print(f"• [bold]Created At:[/bold]    {shandler.created_datetime}")
        self.console.print(f"• [bold]Topics Found:[/bold]  {len(shandler.topics)}")
        for topic_name in shandler.topics:
            self.console.print(f"  - {topic_name}")
        shandler.close()

    def get_remote_sequence_size(self, client: MosaicoClient, sequence_name: str) -> int:
        shandler = client.sequence_handler(sequence_name)
        if shandler is None:
            raise RuntimeError(
                f"Could not retrieve sequence handler for '{sequence_name}'"
            )
        return shandler.total_size_bytes

    @staticmethod
    def _format_size_mb(size_bytes: int) -> float:
        return size_bytes / (1024 * 1024)
