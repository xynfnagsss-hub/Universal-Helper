# 🛡️ Discord Moderation Bot

A professional Discord moderation bot with beautifully designed embeds and comprehensive moderation features.

## ✨ Features

### 🔨 Moderation Commands
- **Kick** - Remove members from the server
- **Ban** - Permanently ban members
- **Warn** - Issue warnings (3 strikes auto-timeout system)
- **Mute** - Temporarily silence members
- **Unmute** - Remove mute from members
- **Clear** - Bulk delete messages
- **Purge** - Advanced message deletion with user/content filtering
- **Warnings** - Check member warnings
- **Clear Warnings** - Reset warnings for a member or all members

### 🎨 Beautiful Embeds
- Color-coded embeds for different actions
- Professional formatting with emojis
- Timestamp and user information
- Moderation logs channel support
- Error handling with clear messages

### ⚙️ Features
- **Dual Command Support** - Use prefix (!) or slash (/) commands
- Automatic timeout after 3 warnings
- Permission checks for safety
- Configurable mute durations (seconds, minutes, hours, days)
- Comprehensive logging to moderation-logs channel
- Clean error messages with helpful guidance

## 📋 Installation

### 1. Clone/Download
Download the bot files to your system.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Create a bot under the application
4. Copy the bot token
5. Enable these **Intents**:
   - Message Content Intent
   - Server Members Intent
   - Guild Moderation
6. Under OAuth2 → URL Generator, select these scopes:
   - `bot`
7. Select these permissions:
   - Kick Members
   - Ban Members
   - Manage Messages
   - Timeout Members
   - Manage Roles
8. Copy the generated URL and invite the bot to your server

### 4. Configure Environment
Create a `.env` file in the bot directory:
```
DISCORD_TOKEN=your_bot_token_here
```

### 5. Set Up Logging Channel
Create a channel named `moderation-logs` in your server for automatic logging.

### 6. Run the Bot
```bash
python bot.py
```

## 🎮 Command Usage

### Kick a Member
```
!kick @member reason for kicking
```

### Ban a Member
```
!ban @member reason for banning
```

### Warn a Member
```
!warn @member spam in general chat
```
*After 3 warnings, the member will be automatically timed out for 1 hour.*

### Mute a Member
```
!mute @member 1h excessive caps
```

Duration formats:
- `1s` - 1 second
- `30m` - 30 minutes
- `2h` - 2 hours
- `7d` - 7 days

### Unmute a Member
```
!unmute @member reason for unmuting
```

### Clear Messages
```
!clear 50
```
*Clears the last 50 messages (max 100)*

### Purge Messages (Advanced)
```
!purge 100
```
*Purge last 100 messages*

```
!purge 50 @member
```
*Purge last 50 messages from a specific member*

```
!purge 30 --content spam
```
*Purge last 30 messages containing the word "spam"*

Purge supports up to 500 messages at once and can filter by user or message content.

### Check Warnings
```
!warnings @member
```
*Check the warning count for a member*

### Clear Warnings
```
!clearwarnings @member
```
*Clear warnings for a specific member*

```
!clearwarnings
```
*Clear all warnings for all members server-wide*

### Get Help
```
!help
```

## ⚡ Slash Commands

You can also use slash commands (/) for a more modern interface:

- `/kick` - Kick a member
- `/ban` - Ban a member
- `/warn` - Warn a member
- `/mute` - Timeout a member
- `/unmute` - Remove timeout
- `/clear` - Clear messages
- `/purge` - Advanced message purge
- `/warnings` - Check member warnings

**Slash Command Benefits:**
- Autocomplete for parameters
- Ephemeral responses (only you see them initially)
- No prefix needed
- Same permissions as prefix commands

## 🎨 Embed Types

The bot features multiple professional embed styles:

- **Action Embeds** - Used for kick, ban, mute, etc.
- **Warning Embeds** - Show warning count and auto-timeout info
- **Confirmation Embeds** - Confirm successful actions
- **Error Embeds** - Display errors with clear messages
- **Log Embeds** - Comprehensive moderation logs

## 📁 File Structure

```
Discord Universal Bot/
├── bot.py                 # Main bot file
├── config.py              # Configuration and colors
├── utils.py               # Embed utility functions
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .env                   # Your Discord token (create this)
├── README.md              # This file
└── cogs/
    └── moderation.py      # Moderation commands cog
```

## 🔒 Permissions

The bot requires these permissions in your server:
- Kick Members
- Ban Members
- Manage Messages
- Timeout Members
- Manage Roles

Users must have appropriate permissions to use moderation commands:
- `Kick Members` - for kick command
- `Ban Members` - for ban command
- `Manage Messages` - for warn command
- `Manage Roles` - for mute/unmute commands

## 🎨 Customization

### Change Colors
Edit `config.py` and modify the `Colors` class:
```python
class Colors:
    PRIMARY = discord.Color.from_rgb(88, 101, 242)
    SUCCESS = discord.Color.from_rgb(87, 171, 90)
    # ... etc
```

### Change Emojis
Edit the `Emojis` class in `config.py` to use different emojis.

### Change Prefix
In `bot.py`, change:
```python
bot = commands.Bot(command_prefix="!", ...)
```

## 🚀 Deployment

### Using a VPS/Server
1. Install Python 3.8+
2. Upload files to server
3. Install requirements
4. Set up `.env` file
5. Use a process manager like `pm2` or `systemd` to keep it running

### Using Hosting Services
- Replit
- Railway
- Heroku (now paid)
- Digital Ocean

## 🛠️ Troubleshooting

**Bot won't start:**
- Check if DISCORD_TOKEN is set in `.env`
- Ensure the token is valid and hasn't expired
- Check Python version (requires 3.8+)

**Commands not working:**
- Verify bot has permissions in the server
- Check role hierarchy (bot role must be above target member)
- Ensure moderation-logs channel exists

**Embeds not showing:**
- Check bot permissions to send embeds
- Ensure channel allows bot messages

## 📞 Support

For issues or questions, check:
- Discord.py Documentation: https://discordpy.readthedocs.io/
- Discord Developer Docs: https://discord.com/developers/docs

## 📄 License

This project is open source and available for personal use.

---

Made with ❤️ for Discord moderation
