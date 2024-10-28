import discord
import csv
import asyncio
from discord.ext import commands

# Replace with your bot token (after regenerating it for security)
TOKEN = 'YOUR_TOKEN_HERE'  # <-- Update this line with your new token

# Intents and command prefix
intents = discord.Intents.default()
intents.bans = True  # Enable bans permission
intents.message_content = True  # Enable message content intent
bot = commands.Bot(command_prefix="!", intents=intents)

# Command to fetch all banned users and save to a CSV file
@bot.command(name='fb')
async def fb(ctx):
    try:
        total_bans = 0  # Counter for scraped users
        rate_limit_wait = 60  # Wait time when hitting rate limits
        unique_users = {}  # Dictionary to store unique users (ID: Username#Discriminator)
        duplicate_ids = []  # List to store duplicate user IDs
        duplicate_count = 0  # Counter for duplicates

        # Create or overwrite a CSV file and save banned users
        with open('banned_users.csv', mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['User ID', 'Username#Discriminator'])  # CSV headers

            # Use async for to iterate over all bans (discord async iterable)
            async for ban_entry in ctx.guild.bans():
                user = ban_entry.user
                
                # Check for duplicates
                if user.id in unique_users:
                    print(f"Duplicate found: {user.name}#{user.discriminator} (ID: {user.id}), skipping...")
                    duplicate_ids.append(user.id)  # Add duplicate user ID to the list
                    duplicate_count += 1  # Increment duplicate counter
                    continue  # Skip if user is already in the unique_users

                # Save unique user
                unique_users[user.id] = f"{user.name}#{user.discriminator}"
                
                # Print each banned user while scraping
                print(f"Scraping banned user: {user.name}#{user.discriminator} (ID: {user.id})")
                writer.writerow([user.id, unique_users[user.id]])
                total_bans += 1  # Increment counter

                # Check if we reached 1000 bans
                if total_bans % 1000 == 0:  # After every 1000 bans
                    print("Hit 1000 bans. Waiting for rate limit...")
                    await asyncio.sleep(rate_limit_wait)  # Wait to avoid hitting rate limits

        await ctx.send(f"Scraped {total_bans} unique banned users and saved them to banned_users.csv.")

        # Print the number of duplicates found and their IDs
        if duplicate_count > 0:
            print(f"Found {duplicate_count} duplicate(s): {duplicate_ids}")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Command to ban users from a CSV file on a new server
@bot.command(name='bans')
@commands.has_permissions(ban_members=True)
async def bans(ctx):
    try:
        with open('banned_users.csv', mode='r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            total_users = sum(1 for _ in csv_reader)  # Count total users to ban
            file.seek(0)  # Reset the file pointer to the start
            next(csv_reader)  # Skip the header row

            # Send the initial message indicating progress
            progress_message = await ctx.send(f"Banning users... (0/{total_users})")
            current_ban_count = 0  # Counter for banned users

            for row in csv_reader:
                user_id = int(row['User ID'])
                user = await bot.fetch_user(user_id)
                await ctx.guild.ban(user, reason="Banned from old server")
                current_ban_count += 1  # Increment counter

                # Update the progress message
                await progress_message.edit(content=f"Banning users... ({current_ban_count}/{total_users})")

        await ctx.send("All users in the CSV have been banned.")

    except Exception as e:
        await ctx.send(f"An error occurred: {e}")

# Run the bot
bot.run(TOKEN)