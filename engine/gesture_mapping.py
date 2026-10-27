import json
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "gesture_config.json"

BUILT_IN_GESTURES = {
    "None",
    "Closed_Fist",
    "Open_Palm",
    "Pointing_Up",
    "Thumb_Down",
    "Thumb_Up",
    "Victory",
    "ILoveYou"
}

VALID_KINDS = {
    "continuous", # Happens while held
    "discrete", # Fires once
    "toggle", # Flips a state once entered
    "none" # Does nothing
}


def load_config(path = CONFIG_PATH):
    # Reads json file and checks it incase of typos.
    with open(path) as f:
        config = json.load(f)


    for role, gestures in config["gestures"].items():
        for name, entry in gestures.items():
            if name not in BUILT_IN_GESTURES:
                raise ValueError(f"Unknown gesture '{name}' under '{role}'")
            if entry["kind"] not in VALID_KINDS:
                raise ValueError(f"Invalid kind '{entry['kind']}' for gesture '{name}'")
    return config


def role_for_hand(config, handSide):
    # handSide is "left" or "right" in any capitalisation
    for role, side in config["roles"].items():
        if side.lower() == handSide.lower():
            return role
    return None

def lookup_action(config, handSide, gestureName, score):
    if score < config["confidence_threshold"]:
        return None
    role = role_for_hand(config, handSide)
    if role is None:
        return None
    entry = config["gestures"].get(role, {}).get(gestureName)
    if entry is None:
        return None
    return entry["action"], entry["kind"]
