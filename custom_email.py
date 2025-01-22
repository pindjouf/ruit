from ghunt import globals as gb
from ghunt.helpers.utils import get_httpx_client
from ghunt.objects.base import GHuntCreds
from ghunt.apis.peoplepa import PeoplePaHttp
from ghunt.apis.vision import VisionHttp
from ghunt.helpers import gmaps, playgames, auth, calendar as gcalendar, ia
from ghunt.helpers.knowledge import get_user_type_definition

import httpx
from typing import *
from pathlib import Path

COLORS = {
    'red': '#FB4934',
    'orange': '#FE8019',
    'yellow': '#FABD2F',
    'green': '#B8BB26',
    'aqua': '#8EC07C',
    'blue': '#83A598',
    'purple': '#D3869B',
    'gray': '#928374',
    'fg': '#EBDBB2',
    'bg': '#282828'     
}

class TargetNotFoundError(Exception):
    pass

class NoPublicProfileError(Exception):
    pass

async def hunt(as_client: httpx.AsyncClient, email_address: str, json_file: Path=None):
    if not as_client:
        as_client = get_httpx_client()
 
    ghunt_creds = await auth.load_and_auth(as_client)

    people_pa = PeoplePaHttp(ghunt_creds)
    is_found, target = await people_pa.people_lookup(as_client, email_address, params_template="max_details")
    
    if not is_found:
        raise TargetNotFoundError("[-] The target wasn't found.")

    if json_file:
        json_results = {}

    containers = target.sourceIds

    if len(containers) > 1 or not "PROFILE" in containers:
        gb.rc.print("[!] You have this person in these containers:", style=COLORS['yellow'])
        for container in containers:
            gb.rc.print(f"- {container.title()}", style=COLORS['blue'])

    if not "PROFILE" in containers:
        raise NoPublicProfileError("[-] Given information does not match a public Google Account.")

    container = "PROFILE"
    
    gb.rc.print("\n🙋 Google Account Data", style=COLORS['purple'])

    if container in target.profilePhotos:
        if target.profilePhotos[container].isDefault:
            gb.rc.print("[-] Default profile picture", style=COLORS['gray'])
        else:
            gb.rc.print("[+] Custom profile picture!", style=COLORS['green'])
            gb.rc.print(f"=> {target.profilePhotos[container].url}", style=COLORS['blue'])

    if container in target.coverPhotos:
        if target.coverPhotos[container].isDefault:
            gb.rc.print("[-] Default cover picture", style=COLORS['gray'])
        else:
            gb.rc.print("[+] Custom cover picture!", style=COLORS['green'])
            gb.rc.print(f"=> {target.coverPhotos[container].url}", style=COLORS['blue'])

    gb.rc.print(f"\nLast profile edit: {target.sourceIds[container].lastUpdated.strftime('%Y/%m/%d %H:%M:%S (UTC)')}", style=COLORS['fg'])
    
    if container in target.emails:
        gb.rc.print(f"Email: {target.emails[container].value}", style=COLORS['blue'])
    else:
        gb.rc.print(f"Email: {email_address}", style=COLORS['blue'])

    gb.rc.print(f"Gaia ID: {target.personId}", style=COLORS['blue'])

    if container in target.profileInfos:
        gb.rc.print("\nUser types:", style=COLORS['purple'])
        for user_type in target.profileInfos[container].userTypes:
            definition = get_user_type_definition(user_type)
            gb.rc.print(f"- {user_type} [italic]({definition})[/italic]", style=COLORS['fg'])

    gb.rc.print("\n📞 Google Chat Data", style=COLORS['purple'])
    gb.rc.print(f"Entity Type: {target.extendedData.dynamiteData.entityType}", style=COLORS['fg'])
    customer_id = target.extendedData.dynamiteData.customerId
    gb.rc.print(f"Customer ID: {customer_id if customer_id else 'Not found'}", style=COLORS['fg'])

    gb.rc.print("\n🌐 Google Plus Data", style=COLORS['purple'])
    gb.rc.print(f"Enterprise User: {target.extendedData.gplusData.isEntrepriseUser}", style=COLORS['fg'])
    
    if container in target.inAppReachability:
        gb.rc.print("\n[+] Activated Google services:", style=COLORS['green'])
        for app in target.inAppReachability[container].apps:
            gb.rc.print(f"- {app}", style=COLORS['blue'])

    gb.rc.print("\n🎮 Play Games Data", style=COLORS['purple'])

    player_results = await playgames.search_player(ghunt_creds, as_client, email_address)
    if player_results:
        player_candidate = player_results[0]
        gb.rc.print("\n[+] Found player profile!", style=COLORS['green'])
        gb.rc.print(f"Username: {player_candidate.name}", style=COLORS['blue'])
        gb.rc.print(f"Player ID: {player_candidate.id}", style=COLORS['blue'])
        gb.rc.print(f"Avatar: {player_candidate.avatar_url}", style=COLORS['blue'])
        _, player = await playgames.get_player(ghunt_creds, as_client, player_candidate.id)
        playgames.output(player)
    else:
        gb.rc.print("\n[-] No player profile found.", style=COLORS['gray'])

    gb.rc.print("\n🗺️ Maps Data", style=COLORS['purple'])
    err, stats, reviews, photos = await gmaps.get_reviews(as_client, target.personId)
    gmaps.output(err, stats, reviews, photos, target.personId)

    gb.rc.print("\n🗓️ Calendar Data", style=COLORS['purple'])
    cal_found, calendar, calendar_events = await gcalendar.fetch_all(ghunt_creds, as_client, email_address)

    if cal_found:
        gb.rc.print("\n[+] Public Google Calendar found!", style=COLORS['green'])
        if calendar_events.items:
            if "PROFILE" in target.names:
                gcalendar.out(calendar, calendar_events, email_address, target.names[container].fullname)
            else:
                gcalendar.out(calendar, calendar_events, email_address)
        else:
            gb.rc.print("=> No recent events found.", style=COLORS['gray'])
    else:
        gb.rc.print("[-] No public Google Calendar.", style=COLORS['gray'])

    if json_file:
        if container == "PROFILE":
            json_results[f"{container}_CONTAINER"] = {
                "profile": target,
                "play_games": player if player_results else None,
                "maps": {
                    "photos": photos,
                    "reviews": reviews,
                    "stats": stats
                },
                "calendar": {
                    "details": calendar,
                    "events": calendar_events
                } if cal_found else None
            }
        else:
            json_results[f"{container}_CONTAINER"] = {
                "profile": target
            }

        import json
        from ghunt.objects.encoders import GHuntEncoder
        with open(json_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(json_results, cls=GHuntEncoder, indent=4))
        gb.rc.print(f"\n[+] JSON output wrote to {json_file}!", style=COLORS['green'])

    return target
