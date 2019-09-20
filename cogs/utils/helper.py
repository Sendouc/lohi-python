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