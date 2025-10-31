import sys
import time
import os
import concurrent.futures
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    print("Error: The 'requests' library is not installed.", file=sys.stderr)
    print("Please install it by running: pip install requests", file=sys.stderr)
    sys.exit(1)

# ANSI escape codes for colors
GREEN = '\033[1;32m'
BLUE = '\033[1;34m'
BOLD_WHITE = '\033[1;37m'
CYAN = '\033[1;36m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
RESET = '\033[0m'

# A curated list of websites and their user profile URL formats.
DEFAULT_SITES_TO_CHECK = [
    # Social Media & Networking
    "https://www.facebook.com/{}",
    "https://x.com/{}", # Formerly Twitter
    "https://www.instagram.com/{}",
    "https://www.linkedin.com/in/{}",
    "https://www.pinterest.com/{}/",
    "https://www.reddit.com/user/{}",
    "https://vk.com/{}",
    "https://t.me/{}", # Telegram
    "https://www.tumblr.com/blog/{}",
    "https://myspace.com/{}",
    "https://ello.co/{}",
    "https://ask.fm/{}",

    # Video & Streaming
    "https://www.tiktok.com/@{}",
    "https://www.youtube.com/@{}",
    "https://vimeo.com/{}",
    "https://www.twitch.tv/{}",
    "https://www.dailymotion.com/{}",
    "https://streamable.com/{}",

    # Music
    "https://soundcloud.com/{}",
    "https://open.spotify.com/user/{}",
    "https://www.last.fm/user/{}",
    "https://www.mixcloud.com/{}/",
    "https://www.bandcamp.com/{}",
    "https://genius.com/artists/{}",

    # Creative & Portfolio
    "https://www.behance.net/{}",
    "https://dribbble.com/{}",
    "https://www.deviantart.com/{}",
    "https://500px.com/p/{}",
    "https://www.artstation.com/{}",
    "https://carbonmade.com/{}",
    "https://www.flickr.com/people/{}",
    "https://gifer.com/{}",
    "https://imgflip.com/user/{}",

    # Gaming
    "https://www.roblox.com/user.aspx?username={}",
    "https://steamcommunity.com/id/{}",
    "https://www.chess.com/member/{}",
    "https://www.nexusmods.com/users/{}",
    "https://www.kongregate.com/accounts/{}",
    "https://www.newgrounds.com/{}.newgrounds.com",
    "https://{}.itch.io/",
    "https://www.speedrun.com/user/{}",
    "https://www.gamespot.com/profile/{}/",

    # Blogging & Publishing
    "https://medium.com/@{}",
    "https://www.wattpad.com/user/{}",
    "https://www.blogger.com/profile/{}",
    "https://disqus.com/by/{}/",
    "https://wordpress.com/author/{}",
    "https://en.gravatar.com/{}",
    "https://{}.blogspot.com/",
    "https://{}.wordpress.com/",

    # Coding & Development
    "https://github.com/{}",
    "https://gitlab.com/{}",
    "https://bitbucket.org/{}/",
    "https://hub.docker.com/u/{}",
    "https://stackoverflow.com/users/{}",
    "https://www.codewars.com/users/{}",
    "https://www.freecodecamp.org/{}",
    "https://jsfiddle.net/user/{}/",
    "https://replit.com/@{}",
    "https://codepen.io/{}",
    "https://codesandbox.io/u/{}",

    # Knowledge & Community
    "https://en.wikipedia.org/wiki/User:{}",
    "https://fandom.com/u/{}",
    "https://www.quora.com/profile/{}",
    "https://www.instructables.com/member/{}",
    "https://www.producthunt.com/@{}",
    "https://news.ycombinator.com/user?id={}",
    "https://www.goodreads.com/{}",
    "https://letterboxd.com/{}/",
    "https://www.tripadvisor.com/Profile/{}",
    "https://www.cracked.com/members/{}",

    # Crowdfunding & Support
    "https://www.patreon.com/{}",
    "https://www.kickstarter.com/profile/{}",
    "https://ko-fi.com/{}",
    "https://buymeacoffee.com/{}",
    "https://www.gofundme.com/profile/{}",

    # Marketplaces & E-commerce
    "https://www.etsy.com/people/{}",
    "https://www.ebay.com/usr/{}",
    "https://www.fiverr.com/{}",
    "https://www.gumroad.com/{}",
    "https://themeforest.net/user/{}",
    "https://www.redbubble.com/people/{}/",
    "https://teespring.com/stores/{}",
    "https://www.amazon.com/gp/profile/amzn1.account.{}",
    "https://www.aliexpress.com/store/{}",

    # Payment & Finance
    "https://cash.app/${}",
    "https://www.paypal.com/paypalme/{}",
    "https://venmo.com/u/{}",

    # Miscellaneous
    "https://www.buzzfeed.com/{}",
    "https://slides.com/{}",
    "https://keybase.io/{}",
    "https://imgur.com/user/{}",
    "https://pastebin.com/u/{}",
    "https://www.scribd.com/{}",
    "https://www.slideshare.net/{}",
    "https://{}.slack.com/",
    "https://{}.wixsite.com/",
    "https://ifunny.co/user/{}",
    "https://www.khanacademy.org/profile/{}/",
    "https://www.duolingo.com/profile/{}/",
    "https://www.sporcle.com/user/{}/",
    "https://www.memrise.com/user/{}/",
    "https://www.ultimate-guitar.com/u/{}",
    "https://allrecipes.com/cook/{}"
]

def check_username(url_format, username, session):
    """
    Checks for a username on a site. Returns a status and the final URL.
    """
    if "{}" not in url_format:
        # This case should ideally be caught by load_sites_from_file for user-provided sites
        # For hardcoded sites, this indicates a bug in the default list.
        return ('error', url_format) # Treat as an error for consistency

    url = url_format.format(username)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        with session.get(url, headers=headers, timeout=10) as response:
            if response.status_code == 200:
                if "ProfilePage" not in response.text and "Page Not Found" not in response.text:
                    return ('found', url)
    except requests.RequestException:
        return ('error', url)
    return ('not_found', url)

def load_sites_from_file(filepath, extensions=None):
    """
    Loads sites from a given file path, returning a list of valid URL formats,
    a list of malformed ones, and the count of original valid lines.
    """
    valid_sites = []
    malformed_sites = []
    original_valid_lines_count = 0

    if extensions is None:
        extensions = [""] # Default to no extension if none provided

    try:
        with open(filepath, 'r') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    original_valid_lines_count += 1

                    # Ensure scheme is present
                    if not stripped_line.startswith('http://') and not stripped_line.startswith('https://'):
                        stripped_line = 'https://' + stripped_line

                    # If {} is missing, add /{} automatically
                    if "{}" not in stripped_line:
                        stripped_line += "/{}"

                    # Apply extensions
                    for ext in extensions:
                        # Ensure extension has a trailing slash if it's a path segment
                        formatted_ext = ext.strip().rstrip('/') + '/' if ext.strip() else ''

                        # Insert extension before the placeholder
                        modified_line = stripped_line.replace('{}', formatted_ext + '{}')
                        valid_sites.append(modified_line)

    except Exception as e:
        print(f"\n{RED}[!] Error reading file {filepath}: {e}{RESET}")
    return valid_sites, malformed_sites, original_valid_lines_count

def main():
    """
    Main function to run the username scanner.
    """
    print() # Add a blank line for spacing before the prompt
    try:
        username = input(f" {BOLD_WHITE}search username > {RESET}")
    except KeyboardInterrupt:
        print()
        print(f"\n{RED}Exiting...{RESET}")
        return

    if not username:
        print()
        print(f"\n{RED}Username cannot be empty.{RESET}")
        return

    found_urls = []
    error_urls = []

    # Initialize the list of sites to check with default sites
    sites_to_scan = list(DEFAULT_SITES_TO_CHECK) # Create a mutable copy

    print() # spacing
    try:
        while True:
            scan_file_choice = input(f"{BOLD_WHITE}Do you want to add websites to the scan? [N/y] > {RESET}").lower()
            if scan_file_choice in ['y', 'n', '']:
                break
            else:
                print()
                print(f"\n{RED}Invalid input. Please enter y, n, or press Enter to automatically scan a pre-configured list...{RESET}")
                print()

        extensions_to_add = [""] # Default to no extensions
        if scan_file_choice == 'y':
            print()
            while True:
                file_path = input(f"{YELLOW}Enter the path to your file or use {CYAN}sites.txt{YELLOW} for a more comprehensive scan > {RESET}")
                if os.path.exists(file_path):
                    print()
                    # Ask about extensions
                    while True:
                        add_ext_choice = input(f"{BOLD_WHITE}Add path extensions (e.g., 'blog/', 'users/') to each site? (N/y) > {RESET}").lower()
                        if add_ext_choice in ['y', 'n', '']:
                            break
                        else:
                            print(f"\n{RED}Invalid input. Please enter y, n, or press Enter.{RESET}")
                            print()
                    if add_ext_choice == 'y':
                        print()
                        while True:
                            ext_input = input(f"{YELLOW}Enter comma-separated extensions (e.g., blog/, users/) > {RESET}")

                            raw_extensions = [e.strip() for e in ext_input.split(',') if e.strip()]

                            has_invalid_ext = False
                            for ext in raw_extensions:
                                if not ext.endswith('/'):
                                    print(f"\n{RED}Warning: Extension '{ext}' does not end with a '/'. Please ensure all path extensions end with a slash.{RESET}")
                                    has_invalid_ext = True
                                    break

                            if has_invalid_ext:
                                print()
                                continue

                            if raw_extensions:
                                extensions_to_add = raw_extensions
                                break
                            else:
                                print(f"\n{RED}No valid extensions entered. Please provide at least one, or press N to skip.{RESET}")
                                print()

                    user_added_valid_sites, malformed_user_sites, original_valid_lines_count = load_sites_from_file(file_path, extensions=extensions_to_add) # Pass extensions
                    print()
                    if user_added_valid_sites:
                        sites_to_scan.extend(user_added_valid_sites)
                        print(f"{GREEN}[*] Loaded {CYAN}{original_valid_lines_count}{GREEN} site(s) from {CYAN}{file_path}{GREEN}{RESET}")
                    if malformed_user_sites:
                        # Add malformed sites to error_urls for final reporting
                        error_urls.extend(malformed_user_sites)
                        print(f"{YELLOW}[!] Found {len(malformed_user_sites)} malformed site(s) in {file_path}. See errors below.{RESET}")
                    break
                else:
                    print()
                    print(f"{RED}[!] File not found: {file_path}.{RESET}")
                    while True:
                        print()
                        try_again = input(f"{BOLD_WHITE}Try again? [Y/n] > {RESET}").lower()
                        if try_again in ['y', '']:
                            print()
                            break
                        elif try_again == 'n':
                            print(f"\n{RED}Exiting...{RESET}")
                            return
                        else:
                            print(f"\n{RED}Invalid input. Please enter y, n, or press Enter.{RESET}")
    except KeyboardInterrupt:
        print()
        print(f"\n{RED}Exiting...{RESET}")
        return

    # Deduplicate sites while preserving order
    final_sites_to_check = []
    seen_sites = set()
    for site in sites_to_scan:
        if site not in seen_sites:
            final_sites_to_check.append(site)
            seen_sites.add(site)

    sites_to_scan = final_sites_to_check

    print()

    found_urls = []
    # error_urls is already initialized at the top of main
    total_sites = len(sites_to_scan)
    completed_count = 0
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    start_time = time.time()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            with requests.Session() as session:
                future_to_url = {executor.submit(check_username, site, username, session): site for site in sites_to_scan}

                for future in concurrent.futures.as_completed(future_to_url):
                    completed_count += 1

                    spinner_char = spinner[completed_count % len(spinner)]
                    percent = (completed_count / float(total_sites)) * 100
                    sys.stdout.write(f'\r{GREEN}[*] Searching > {CYAN}{username}{GREEN} {spinner_char} {percent:.1f}%{RESET}')
                    sys.stdout.flush()

                    result = future.result()
                    if result:
                        status, url = result
                        if status == 'found':
                            found_urls.append(url)
                        elif status == 'error':
                            error_urls.append(url)
    except KeyboardInterrupt:
        sys.stdout.write('\r' + ' ' * 50 + '\r') # Clear the spinner line
        print(f"\n{RED}[*] Search Aborted...{RESET}")
        return

    end_time = time.time()
    duration = end_time - start_time

    sys.stdout.write('\r' + ' ' * 40 + '\r') # Clear the spinner line

    if error_urls:
        #print(f"{YELLOW}[*] {len(error_urls)} Site(s) Timed Out or Errored{RESET}")
        print()
        for url in sorted(error_urls):
            print(f"{RED}{url}{RESET}")
        print(f"\n{YELLOW}[*] {len(error_urls)} Site(s) Timed Out or Errored{RESET}")
        print() # Blank line after list of errors

    if found_urls:
       # print(f"\n{CYAN}[*] Found {GREEN}{len(found_urls)}{CYAN} Possible Profile(s) out of {GREEN}{total_sites}{CYAN} websites.{RESET}")
        print() # Skip a line before listing URLs
        for url in sorted(found_urls):
            print(f"{GREEN}{url}{RESET}")
    else:
        print("No profiles found for this username.")

    print(f"\n{BOLD_WHITE}[*] Search Completed in {GREEN}{duration:.2f}{BOLD_WHITE} Seconds.{RESET}")
    print()
    if found_urls:
        print(f"{CYAN}[*] Found {GREEN}{len(found_urls)}{CYAN} Possible Profile(s) out of {GREEN}{total_sites}{CYAN} Websites.{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print(f"\n{RED}Exiting...{RESET}")
