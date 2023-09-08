import json


class Bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def read_minifig_ids_from_file(category: str) -> list:
    with open(f"BL_list/{category}_minifigs_ids.json", "r") as file:
        ids = file.read()
    ids = json.loads(ids)
    return ids


def get_proxies():
    with open(f"http.txt", "r") as file:
        for line in file:
            yield line.strip()
