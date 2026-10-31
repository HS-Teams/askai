"""AskAI local desktop tools over MCP stdio; stdout belongs to the protocol."""

from dataclasses import asdict
from pathlib import Path
import os
import asyncio
from mcp.server.fastmcp import FastMCP, Context
from mcp.types import ToolAnnotations
from askai.core.capabilities.desktop import DesktopCapabilities
from askai.core.support.app_paths import askai_data_dir
from askai.core.permissions.grants import grants


async def confirm_action(ctx: Context, message: str) -> bool:
    """Use the MCP form schema; model titles/descriptions are not allowed at its root."""
    result = await ctx.session.elicit_form(
        message=message,
        requestedSchema={"type": "object", "properties": {}},
        related_request_id=ctx.request_id,
    )
    return result.action == "accept"


def create_server(capabilities: DesktopCapabilities, policy=grants) -> FastMCP:
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

    async def authorize(ctx, required, message):
        return await policy.authorize_async(required, message, lambda text: confirm_action(ctx, text))

    @server.tool(annotations=annotations)
    async def open_path(path: str, ctx: Context) -> dict:
        """Open an absolute local path. Audio/video plays in ffplay; other paths use the default app."""
        target = DesktopCapabilities._path(path)
        media = target.suffix.lower() in DesktopCapabilities.AUDIO_SUFFIXES | DesktopCapabilities.VIDEO_SUFFIXES
        required = ["media.play.local" if media else "paths.open.local"]
        if target.name.casefold() == "photo booth.app":
            required.append("camera.preview.local")
        if not await authorize(ctx, required, f"Allow AskAI to open `{target}`?"):
            return {"status": "cancelled", "operation": "open_path"}
        return await asyncio.to_thread(lambda: asdict(capabilities.open_path(str(target))))

    @server.tool(annotations=annotations)
    async def open_application(name: str, ctx: Context) -> dict:
        """Launch a named macOS application, such as Safari or Calculator."""
        required = ["applications.open.local"]
        if Path(name).name.casefold().removesuffix(".app") in {"photo booth", "photobooth"}:
            required.append("camera.preview.local")
        if not await authorize(ctx, required, f"Allow AskAI to open application `{name}`?"):
            return {"status": "cancelled", "operation": "open_application"}
        return await asyncio.to_thread(lambda: asdict(capabilities.open_application(name)))

    @server.tool(annotations=annotations)
    async def play_music(path: str, ctx: Context) -> dict:
        """Play a local audio or video file using ffplay (FFmpeg). Resolve the path before calling."""
        target = DesktopCapabilities._path(path)
        if not await authorize(ctx, ["media.play.local"], f"Allow AskAI to play `{target}`?"):
            return {"status": "cancelled", "operation": "play_music"}
        return await asyncio.to_thread(lambda: asdict(capabilities.play_music(str(target))))

    @server.tool(annotations=annotations)
    async def control_music(action: str, ctx: Context) -> dict:
        """Control AskAI ffplay playback: play (resume), pause or stop. No playlist navigation."""
        if action not in {"play", "pause", "stop"}:
            raise ValueError("Playback action must be play, pause or stop")
        if not await authorize(ctx, [f"media.{action}.local"], f"Allow AskAI to {action} local playback?"):
            return {"status": "cancelled", "operation": "control_music"}
        return await asyncio.to_thread(lambda: asdict(capabilities.control_music(action)))

    @server.tool(annotations=annotations)
    async def open_camera(ctx: Context) -> dict:
        """Open the camera preview in Photo Booth, only when the user requests camera access."""
        if not await authorize(ctx, ["camera.preview.local"], "Allow AskAI to open the camera preview?"):
            return {"status": "cancelled", "operation": "open_camera"}
        return await asyncio.to_thread(lambda: asdict(capabilities.open_camera()))

    return server


def main():
    base = Path(
        os.getenv(
            "ASKAI_CAPABILITY_DIR", str(askai_data_dir() / "cache" / "capabilities")
        )
    )
    create_server(DesktopCapabilities(base)).run(transport="stdio")


if __name__ == "__main__":
    main()
