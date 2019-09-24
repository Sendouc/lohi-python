from difflib import get_close_matches

from .lists import weapons, weapons_upper

MAX_LENGTH = 2000

def split_to_shorter_parts(msg: str) -> list:
    if len(msg) <= MAX_LENGTH:
        return [msg]
    to_return = []
    current_msg = ""
    for line in msg.split("\n"):
        if len(current_msg) + len(line) >= MAX_LENGTH:
            to_return.append(current_msg)
            current_msg = ""
        current_msg += f"{line}\n"
    
    to_return.append(current_msg)
    return to_return

def get_close_weapon(weapon: str):
    '''
    Gets the closest weapons with fuzzy matching
    if close enough match isn't found returns None.
    '''
    weapon_list = get_close_matches(weapon.upper(), weapons_upper, n=1)
    if len(weapon_list) == 0:
        return None
    
    weapon = weapon_list[0]
    index_of_weapon = weapons_upper.index(weapon)
    return weapons[index_of_weapon]