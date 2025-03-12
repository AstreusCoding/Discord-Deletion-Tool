import discord # type: ignore
from discord.ext import commands # type: ignore
from utils import setup_logging, get_authorization_token
import random

# Setup logging
logger = setup_logging()

# Import pandas with error handling
try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None
    logger.error("pandas not installed, Excel export disabled.")

# Load environment variables
authorization_token = get_authorization_token('DISCORD_TOKEN')

DISCORD_DM_URL = "[Go to message](https://discord.com/channels/@me/"
ALLOWED_USERS = [
    194969326275657738,
    1327158107645808661,  # Add your user ID here
]


class MyClient(discord.Client):
    async def on_ready(self):
        logger.info(f'Logged on as {self.user}')

    async def get_user_messages(self, user_id):
        """
        Retrieve all messages in the DM conversation with a specific user
        and save them into an excel spreadsheet.

        Args:
            user_id: The Discord user ID to get the DM conversation for

        Returns:
            A list of message objects in the DM conversation
        """
    # Get the user and ensure a DM channel exists
    user = self.get_user(user_id)
    if not user:
        logger.error(f"User with id {user_id} not found.")
        return []
    dm_channel = user.dm_channel
    if dm_channel is None:
        dm_channel = await user.create_dm()

    all_messages = []
    last_message = None

    # Use pagination to retrieve messages in batches of 100
    while True:
        kwargs = {'limit': 100}
        if last_message:
            kwargs['before'] = last_message  # pass the message object

        messages = [msg async for msg in dm_channel.history(**kwargs)]
        if not messages:
            break
        all_messages.extend(messages)
        last_message = messages[-1]

        logger.info(
            f'Total messages from user {user_id} found: {len(all_messages)}'
        )

        # Save messages to an Excel spreadsheet using pandas
        if pd is None:
            logger.error("pandas not installed, Excel export disabled.")
        else:
            try:
                rows = []
                rows.extend(
                    {
                        'id': msg.id,
                        'author': msg.author.name,
                        'content': msg.content,
                        'timestamp': msg.created_at,
                    }
                    for msg in all_messages
                )
                df = pd.DataFrame(rows)
                excel_filename = f"dm_messages_{user_id}.xlsx"
                df.to_excel(excel_filename, index=False)
                logger.info(f"Saved messages to {excel_filename}")
            except Exception as e:
                logger.error(f"Error saving messages to Excel: {str(e)}")

        return all_messages

    async def on_message(self, message):  # sourcery skip: assign-if-exp
        # only respond to allowed users
        if message.author.id not in ALLOWED_USERS:
            return

        # check if it was sent in a DM channel
        if not isinstance(message.channel, discord.DMChannel):
            return

        # check if the message is a command we're expecting
        if message.content != 'purge':
            return

        await message.channel.send('Please provide a mention or a user ID')

        # Wait for a response
        def check(m):
            return m.author == message.author and m.channel == message.channel

        response = await self.wait_for('message', check=check)

        # Check if the response is a mention
        if response.mentions:
            user_id = response.mentions[0].id
        else:
            # Try to convert the content to a user ID
            try:
                user_id = int(response.content.strip())
            except ValueError:
                await message.channel.send(
                    "That doesn't appear to be a valid user ID. "
                    "Please try again."
                )
                return

        # Send a confirmation message
        await message.channel.send(
            f"You provided the following user ID: {user_id},\n"
            f"Does this mention look correct? <@{user_id}>"
        )

        # wait for confirmation
        response = await self.wait_for('message', check=check)
        if response.content.lower() not in ['yes', 'y']:
            await message.channel.send("Please provide the correct user ID.")
            return

        # Get confirmation
        await message.channel.send(
            "Retrieving messages from this user. This may take some time..."
        )

        # Get all messages from the user
        user_messages = await self.get_user_messages(user_id)

        # Report the results
        if user_messages:
            await message.channel.send(
                f"Found {len(user_messages)} messages from user <@{user_id}>"
            )
            await message.channel.send(
                "Here's a sample of the most recent messages:"
            )

            # Randomly show a sample of messages (25 messages)
            sample_size = min(25, len(user_messages))
            sample_messages = random.sample(user_messages, sample_size)
            for msg in sample_messages:
                content = msg.content or (
                    "[No text content - may contain attachments or embeds]"
                )
                if len(content) > 1000:
                    truncated_content = f"{content[:1000]}..."
                else:
                    truncated_content = content

                message_resp: str = ""
                message_resp = f"**Message from <#{msg.channel.id}>:** "
                message_resp += f"{truncated_content}\n"
                message_resp += f"{DISCORD_DM_URL}{msg.channel.id}/{msg.id})\n"
                message_resp += (
                    f"Sent by: {msg.author.name} at "
                    f"{msg.created_at}\n"
                )
                await message.channel.send(
                    message
                )
        else:
            await message.channel.send(
                f"No messages found from user <@{user_id}>"
            )


client = MyClient()
logger.info(f'Starting bot{str(client)}')
client.run(authorization_token)
