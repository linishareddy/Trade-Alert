"""
discord_agent.py
Self-bot for private Discord channels.
WARNING: Self-bots violate Discord ToS. Use at your own risk.
"""

import asyncio
import random
import discord

from config.settings import settings
from agents.discord.harness.client import post_alert


class TradingBot(discord.Client):
    def __init__(self) -> None:
        # DO NOT USE INTENTS for self-bots. Discord will reject the token as invalid!
        super().__init__(
            chunk_guilds_at_startup=False,
        )
        self.target_channel_ids: list[int] = settings.discord_channel_ids

    async def on_ready(self) -> None:
        print(f"[DiscordAgent] ✅ Logged in as {self.user} (ID: {self.user.id})")
        print(f"[DiscordAgent] Watching channels: {self.target_channel_ids}")

        # In order to receive live MESSAGE_CREATE events as a user account
        # without "Read Message History" permission, we MUST subscribe to the guild.
        for channel_id in self.target_channel_ids:
            channel = self.get_channel(channel_id)
            if channel:
                print(f"[DiscordAgent] Sending Lazy Request to subscribe to #{channel.name}...")
                try:
                    payload = {
                        "op": 14,
                        "d": {
                            "guild_id": str(channel.guild.id),
                            "typing": True,
                            "threads": True,
                            "activities": True,
                            "channels": {
                                str(channel.id): [[0, 99]]
                            }
                        }
                    }
                    await self.ws.send_as_json(payload)
                    print(f"[DiscordAgent] ✓ Subscribed successfully to #{channel.name} in {channel.guild.name}")
                except Exception as e:
                    print(f"[DiscordAgent] ⚠ Failed to subscribe to {channel.name}: {e}")
            else:
                print(f"[DiscordAgent] ⚠ Channel {channel_id} not found in cache.")

        print("[DiscordAgent] ✅ Ready and listening for live messages...")

    async def on_message(self, message: discord.Message) -> None:
        if message.channel.id not in self.target_channel_ids:
            return
        if message.author.id == self.user.id:
            return

        await self._process(message, is_edit=False)

    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if after.channel.id not in self.target_channel_ids:
            return
        print(f"[DiscordAgent] Message edited: {after.id}")
        await self._process(after, is_edit=True)

    async def _process(self, message: discord.Message, *, is_edit: bool) -> None:
        await asyncio.sleep(random.uniform(0.8, 2.3))

        payload = {
            "message_id": str(message.id),
            "channel_id": str(message.channel.id),
            "author": str(message.author),
            "content": message.content or "",
            "embeds": [e.to_dict() for e in message.embeds],
            "timestamp": message.created_at.isoformat(),
            "is_edit": is_edit,
        }

        ok = await post_alert(payload)
        status = "✅" if ok else "❌"
        preview = (message.content[:75] + "...") if message.content else "[Embeds only]"
        print(f"[DiscordAgent] {status} | {message.id[-6:]} | {message.author} | {preview}")


async def run_discord_agent() -> None:
    if not getattr(settings, "DISCORD_USER_TOKEN", None):
        print("[DiscordAgent] ❌ DISCORD_USER_TOKEN not set")
        return

    bot = TradingBot()

    try:
        print("[DiscordAgent] Starting self-bot...")
        await bot.start(settings.DISCORD_USER_TOKEN)
    except discord.LoginFailure:
        print("[DiscordAgent] ❌ Invalid or expired token. Get a fresh one.")
    except Exception as e:
        print(f"[DiscordAgent] Crash: {e}")