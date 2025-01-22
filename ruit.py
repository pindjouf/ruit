#!/usr/bin/env python3

import csv
import sys
import asyncio
import os
from unidecode import unidecode
from custom_email import hunt, TargetNotFoundError, NoPublicProfileError
from ghunt.helpers import auth
from ghunt.helpers.utils import get_httpx_client
from ghunt.errors import GHuntInvalidSession
import argparse
from rich.console import Console
from rich.theme import Theme
from rich.progress import SpinnerColumn, TextColumn, Progress
from rich import print as rprint

custom_theme = Theme({
    "info": "#8EC07C",
    "warning": "#FE8019",
    "error": "#FB4934",
    "title": "#83A598",
    "accent": "#FABD2F"
})

console = Console(theme=custom_theme)

RUIT_ASCII = """
[title]██████╗ ██╗   ██╗██╗████████╗[/title]
[title]██╔══██╗██║   ██║██║╚══██╔══╝[/title]
[title]██████╔╝██║   ██║██║   ██║   [/title]
[title]██╔══██╗██║   ██║██║   ██║   [/title]
[title]██║  ██║╚██████╔╝██║   ██║   [/title]
[title]╚═╝  ╚═╝ ╚═════╝ ╚═╝   ╚═╝   [/title]
[accent]CSV integration for Ghunt[/accent]
"""

async def process_emails(email_guesses, as_client, ghunt_creds, full_name):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        found_emails = []
        
        for email_addr in email_guesses:
            try:
                if as_client.is_closed:
                    as_client = get_httpx_client()
                    try:
                        ghunt_creds = await auth.load_and_auth(as_client)
                    except Exception as e:
                        console.print(f"[error]❌ Error re-authenticating: {str(e)}[/error]")
                        continue

                task = progress.add_task(f"[info]Checking {email_addr}...[/info]")
                
                try:
                    result = await hunt(as_client=as_client, email_address=email_addr)
                    found_emails.append(email_addr)
                    console.print(f"[info]✅ Found valid email: {email_addr}[/info]")
                except TargetNotFoundError:
                    console.print(f"[warning]⚠️  No account found for {email_addr}[/warning]")
                    continue
                except NoPublicProfileError:
                    console.print(f"[warning]⚠️  No public profile found for {email_addr}[/warning]")
                    continue
                
                progress.remove_task(task)
                await asyncio.sleep(120)
                
            except Exception as e:
                console.print(f"[error]❌ Failed to check {email_addr}: {str(e)}[/error]")
                await asyncio.sleep(120)
        
        if found_emails:
            output_dir = 'found_emails'
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{full_name}.txt")
            with open(output_file, 'w') as f:
                for email in found_emails:
                    f.write(f"{email}\n")

async def main():
    parser = argparse.ArgumentParser(
        description="RUIT - CSV integration for Ghunt",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "input_file",
        help="CSV file containing names to process (must have a 'Name' column)"
    )
    
    if len(sys.argv) == 1:
        console.print(RUIT_ASCII)
        parser.print_help()
        return

    args = parser.parse_args()
    
    console.print(RUIT_ASCII)
    
    as_client = None
    try:
        as_client = get_httpx_client()            

        try:
            ghunt_creds = await auth.load_and_auth(as_client)
        except GHuntInvalidSession:
            console.print("[error]❌ Error: GHunt session not found. Please run 'ghunt login' first to authenticate.[/error]")
            if as_client:
                await as_client.aclose()
            return
        except Exception as e:
            console.print(f"[error]❌ Error during authentication: {str(e)}[/error]")
            if as_client:
                await as_client.aclose()
            return

        with open(args.input_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    full_name = unidecode(row['Name'].lower())
                    entry_list = full_name.split(' ')
                    console.print(f"\n[info]🔍 Processing: {full_name}[/info]")
                    
                    match len(entry_list):
                        case 2:
                            email_guesses = [
                                f"{entry_list[0]}.{entry_list[1]}@gmail.com",
                                f"{entry_list[1]}.{entry_list[0]}@gmail.com",
                                f"{entry_list[0][0]}.{entry_list[1]}@gmail.com",
                                f"{entry_list[1][0]}.{entry_list[0]}@gmail.com"
                            ]
                            await process_emails(email_guesses, as_client, ghunt_creds, full_name)
                            
                        case 3:
                            email_guesses = [
                                f"{entry_list[0]}.{entry_list[1]}{entry_list[2]}@gmail.com",
                                f"{entry_list[1]}{entry_list[2]}.{entry_list[0]}@gmail.com",
                                f"{entry_list[0][0]}.{entry_list[1]}{entry_list[2]}@gmail.com",
                                f"{entry_list[1][0]}{entry_list[2][0]}.{entry_list[0]}@gmail.com"
                            ]
                            await process_emails(email_guesses, as_client, ghunt_creds, full_name)
                            
                        case 4:
                            email_guesses = [
                                f"{entry_list[0]}.{entry_list[1]}{entry_list[2]}{entry_list[3]}@gmail.com",
                                f"{entry_list[1]}{entry_list[2]}{entry_list[3]}.{entry_list[0]}@gmail.com",
                                f"{entry_list[0][0]}.{entry_list[1]}{entry_list[2]}{entry_list[3]}@gmail.com",
                                f"{entry_list[1][0]}{entry_list[2][0]}{entry_list[3][0]}.{entry_list[0]}@gmail.com"
                            ]
                            await process_emails(email_guesses, as_client, ghunt_creds, full_name)
                            
                        case 1:
                            console.print(f"[warning]⚠️  Warning: Single name entry '{full_name}' - skipping[/warning]")
                        case _:
                            console.print(f"[warning]⚠️  Warning: Name '{full_name}' has {len(entry_list)} parts - skipping[/warning]")
                            
                except KeyError:
                    console.print("[error]❌ Error: CSV file must contain a 'Name' column[/error]")
                    if as_client:
                        await as_client.aclose()
                    return
                except Exception as e:
                    console.print(f"[error]❌ Error processing name '{full_name}': {str(e)}[/error]")
                    continue
        
    except FileNotFoundError:
        console.print(f"[error]❌ Error: File '{args.input_file}' not found[/error]")
    except csv.Error as e:
        console.print(f"[error]❌ Error reading CSV file: {str(e)}[/error]")
    except Exception as e:
        console.print(f"[error]❌ An unexpected error occurred: {str(e)}[/error]")
    finally:
        if as_client:
            await as_client.aclose()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[warning]⚠️  Operation cancelled by user[/warning]")
    except Exception as e:
        console.print(f"[error]❌ Fatal error: {str(e)}[/error]")
