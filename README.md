# Codenames Discord Bot

A Discord bot that allows you to play the game **Codenames** directly within your Discord server.

## Features

- Play Codenames using slash commands.
- Automatically manages game state, teams, and roles.
- Generates visual game boards for an immersive experience.

## Prerequisites

- **Python 3.8** or higher.
- A Discord account and a Discord server where you have permission to add bots.
- A Discord application with a bot token. You can create one at the [Discord Developer Portal](https://discord.com/developers/applications).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Tamur11/Codenames-Discord.git
   cd Codenames-Discord
   ```

2. **Install Dependencies**

   Ensure you have `pip` installed. Then, install the required packages using the provided `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

   **`requirements.txt` Content:**

   ```txt
   discord.py>=2.0.0
   Pillow
   python-dotenv
   ```

3. **Set Up Environment Variables**

   Create a `.env` file in the project root directory and add your Discord bot token:

   ```env
   DISCORD_TOKEN=your_bot_token_here
   ```

## Usage

1. **Run the Bot**

   Start the bot by running:

   ```bash
   python bot.py
   ```

   The bot will connect to Discord and synchronize the slash commands with your server. This process may take a few minutes initially.

2. **Invite the Bot to Your Server**

   If you haven't already, invite the bot to your Discord server using an OAuth2 URL with the appropriate permissions. In the Discord Developer Portal:

   - Go to your application.
   - Navigate to the **OAuth2** section and select **URL Generator**.
   - Under **Scopes**, select `bot` and `applications.commands`.
   - Under **Bot Permissions**, select the permissions the bot requires (e.g., Send Messages, Manage Messages, Manage Roles).
   - Copy the generated URL and paste it into your browser to invite the bot to your server.

3. **Interact with the Bot Using Slash Commands**

   ### Starting a New Game

   - **Command:**

     `/codenames`

   - **Description:**

     Starts a new game of Codenames. The bot will initialize the game state and prompt you to add Spymasters.

   ### Joining a Team

   - **Command:**

     `/join color (Red/Blue) role (Player/Spymaster)`

   - **Examples:**

     `/join Red Player`

     `/join Blue Spymaster`

   - **Description:**

     Join the specified team as either a Player or a Spymaster. Only one Spymaster is allowed per team.

   ### Starting the Game

   - **Command:**

     `/start`

   - **Description:**

     Begins the game once both Red and Blue Spymasters have joined. The bot will set up the game board and notify players.

   ### Giving a Clue (Spymasters Only)

   - **Command:**

     `/clue clue (Your Clue) number (Number of Words, or "infinity")`

   - **Example:**

     `/clue Animal 2`

   - **Description:**

     Allows the Spymaster to provide a one-word clue and the number of related words on the board. The clue will be shared with your team.

   ### Making a Guess (Players Only)

   - **Command:**

     `/guess word (Word)`

   - **Example:**

     `/guess LION`

   - **Description:**

     Players use this command to guess a word on the board based on the Spymaster's clue.

   ### Passing Your Turn

   - **Command:**

     `/pass`

   - **Description:**

     Ends your team's turn and passes control to the other team.

   ### Checking Whose Turn It Is

   - **Command:**

     `/turn`

   - **Description:**

     Displays which team's turn it is or which Spymaster should provide a clue.

   ### Viewing Teams and Spymasters

   - **Command:**

     `/teams`

   - **Description:**

     Shows the current team members and identifies the Spymasters.

## Notes

- **Slash Commands Synchronization:**

  - When you first run the bot, it may take a few minutes to register the slash commands with Discord. This is normal.
  - If commands aren't appearing, ensure the bot has the necessary permissions and that you're running the latest version of `discord.py`.

- **Permissions:**

  - The bot requires certain permissions to function properly, such as:
    - Read and Send Messages
    - Manage Messages (for pinning game boards)
    - Manage Roles (for assigning team roles)
  - Ensure the bot's role is high enough in the role hierarchy to manage roles.
