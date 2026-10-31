"""AskAI local desktop tools over MCP stdio; stdout belongs to the protocol."""

from dataclasses import asdict
from pathlib import Path
import os
import asyncio
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from askai.core.capabilities.desktop import DesktopCapabilities


class CameraConsent(BaseModel):
    """An empty form uses the host confirmation buttons, with no extra text field."""


def create_server(capabilities: DesktopCapabilities) -> FastMCP:
    server = FastMCP(
        "AskAI desktop",
        instructions=(
            "Use these desktop capabilities only for actions requested by the user. "
            "Do not activate a camera unless explicitly requested. "
            "Dispatched means the OS accepted the request, not that the user saw or heard it. "
            "Never claim to see image contents based only on a saved image path."
        ),
    )
    annotations = ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, openWorldHint=True
    )

    @server.tool(annotations=annotations)
    def open_path(path: str) -> dict:
        """Open an absolute local path. Audio/video plays in ffplay; other paths use the default app."""
        return asdict(capabilities.open_path(path))

    @server.tool(annotations=annotations)
    def open_application(name: str) -> dict:
        """Launch a named macOS application, such as Safari or Calculator."""
        return asdict(capabilities.open_application(name))

    @server.tool(annotations=annotations)
    def play_music(path: str) -> dict:
        """Play a local audio or video file using ffplay (FFmpeg). Resolve the path before calling."""
        return asdict(capabilities.play_music(path))

    @server.tool(annotations=annotations)
    def control_music(action: str) -> dict:
        """Control AskAI ffplay playback: play (resume), pause or stop. No playlist navigation."""
        return asdict(capabilities.control_music(action))

    @server.tool(annotations=annotations)
    async def open_camera(ctx: Context) -> dict:
        """Open the camera preview in Photo Booth, only when the user requests camera access."""
        consent = await ctx.elicit("Allow AskAI to open the camera preview?", CameraConsent)
        if consent.action != "accept":
            return {"status": "cancelled", "operation": "open_camera"}
        return await asyncio.to_thread(lambda: asdict(capabilities.open_camera()))

    @server.tool(annotations=annotations)
    async def capture_camera(ctx: Context, device: int = 0) -> dict:
        """Confirm, count down and capture one photo. Open the returned path with your image-viewing tool before analyzing it."""
        consent = await ctx.elicit(
            "Allow AskAI to take one camera photo and share it with the current agent for visual analysis?",
            CameraConsent,
        )
        if consent.action != "accept":
            return {"status": "cancelled", "operation": "capture_camera"}
        for remaining in (3, 2, 1):
            await ctx.report_progress(3 - remaining, 3, f"Camera: {remaining}")
            await asyncio.sleep(1)
        result = await asyncio.to_thread(capabilities.capture_camera, device)
        await ctx.report_progress(3, 3, "Camera: SHOT")
        return asdict(result)

    return server


def main():
    base = Path(
        os.getenv(
            "ASKAI_CAPABILITY_DIR", str(Path.home() / ".local/share/askai/capabilities")
        )
    )
    create_server(DesktopCapabilities(base)).run(transport="stdio")


if __name__ == "__main__":
    main()
