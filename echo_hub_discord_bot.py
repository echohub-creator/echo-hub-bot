import os
import json
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", 0))
ADMIN_CHANNEL_ID = int(os.getenv("ADMIN_CHANNEL_ID", 0))
APPROVAL_CHANNEL_ID = int(os.getenv("APPROVAL_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Load vendor directory mapping
VENDOR_FILE = "vendor_directory.json"

def load_vendor_directory():
      if os.path.exists(VENDOR_FILE):
                with open(VENDOR_FILE, "r") as f:
                              return json.load(f)
    return {}
  @bot.event
async def on_ready():
      print(f"Echo Hub Bot logged in as {bot.user} (ID: {bot.user.id})")
      print("Cloud bot monitoring active.")

def validate_inquiry_form(content: str) -> tuple[bool, str]:
      """
          Validates all form submissions to block contact information:
              Emails, phone numbers, Telegram handles, Discord tags,
                  social handles, URLs, and crypto addresses.
                      """
      if not content:
                return True, ""

      # Patterns for prohibited contact details
      patterns = {
          "Email Address": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
          "Phone Number": r"\b(?:\+\d{1,3}\s?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}\b",
          "URL / Website": r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)",
          "Discord Tag / Mention": r"<@!?\d+>|@everyone|@here",
          "Telegram / Social Handle": r"(?:t\.me|telegram|whatsapp|signal|instagram|twitter|x)\s*[:/@]\s*[\w\._-]+",
          "Crypto Address": r"\b(0x[a-fA-F0-9]{40}|[13][a-km-zA-HJ-NP-Z1-9]{25,34}|bc1[q|p][a-z0-9]{39,59})\b"
      }

    for label, pattern in patterns.items():
              if re.search(pattern, content, re.IGNORECASE):
                            return False, f"Prohibited content detected ({label}). Anonymity protection enforced."

          return True, ""

async def set_ticket_permissions(channel: discord.TextChannel, user: discord.Member, vendor_role_id: int = None):
      """
          Automatically configures privacy settings on ticket channels,
              denying @everyone access while granting permissions to admins and assigned vendors.
                  """
      guild = channel.guild

    # Deny @everyone view access
      await channel.set_permissions(guild.default_role, read_messages=False)

    # Allow ticket creator view access
      await channel.set_permissions(user, read_messages=True, send_messages=True, read_message_history=True)

    # Allow admin role access if configured
      for role in guild.roles:
                if role.permissions.administrator:
                              await channel.set_permissions(role, read_messages=True, send_messages=True)

            # Allow assigned vendor role if provided
            if vendor_role_id:
                      vendor_role = guild.get_role(vendor_role_id)
                      if vendor_role:
                                    await channel.set_permissions(vendor_role, read_messages=True, send_messages=True)

              @bot.event
async def on_message(message: discord.Message):
      if message.author.bot:
                return

    # Check ticket channel submissions or interactions
    valid, reason = validate_inquiry_form(message.content)
    if not valid:
              try:
                            await message.delete()
                            warning_msg = await message.channel.send(
                                f"⚠️ **Security Notice ({message.author.mention}):** Your message was removed because it contained restricted personal or contact info. {reason}"
                            )

                  # Log violation to approval/admin channel
                            if APPROVAL_CHANNEL_ID:
                                              approval_channel = bot.get_channel(APPROVAL_CHANNEL_ID)
                                              if approval_channel:
                                                                    await approval_channel.send(
                                                                                              f"🚨 **Blocked Content Violation**\n"
                                                                                              f"**User:** {message.author} (`{message.author.id}`)\n"
                                                                                              f"**Channel:** {message.channel.mention}\n"
                                                                                              f"**Reason:** {reason}"
                                                                    )
except Exception as e:
            print(f"Error handling message validation violation: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
      if not TOKEN:
                print("ERROR: DISCORD_TOKEN is missing in environment variables.")
else:
        bot.run(TOKEN)
