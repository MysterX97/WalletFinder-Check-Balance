import os
import requests
import random
import time
from itertools import permutations, islice
import math
import asyncio
from eth_account import Account
from mnemonic import Mnemonic
from termcolor import colored
from functools import lru_cache
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
# BeautifulSoup and re are kept for EVM scraping, but no longer used for Tron
from bs4 import BeautifulSoup
import re

# Optional libraries, check if installed
try:
    from bitcoinlib.keys import Key
except ImportError:
    print(colored("Warning: bitcoinlib is not installed. Bitcoin functionality will be limited. BTC addresses cannot be generated.", "red"))
    Key = None

try:
    from solana.keypair import Keypair
    from solana.publickey import PublicKey
except ImportError:
    print(colored("Warning: solana library is not installed. Solana functionality will be limited.", "yellow"))
    Keypair = None
    PublicKey = None

try:
    from tronpy import Tron
    from tronpy.keys import PrivateKey as TronPrivateKey
except ImportError:
    print(colored("Warning: tronpy is not installed. Tron functionality will be limited.", "yellow"))
    Tron = None
    TronPrivateKey = None

# --- 1. Configuration ---
# !!! ATTENTION !!!
# This word pool and permutation approach does NOT conform to the BIP-39 mnemonic standard.
# It is used solely for demonstration purposes and to show how your desired "permutation" logic works.
# Real BIP-39 uses a fixed 2048-word dictionary and a checksum.
# Finding a wallet with a balance using this method is practically impossible.
WORD_POOL = [
 "abandon", "ability", "able", "about", "above", "absent", "absorb", "abstract", "absurd", "abuse",
    "access", "accident", "account", "accuse", "achieve", "acid", "acoustic", "acquire", "across", "act",
    "action", "actor", "actress", "actual", "adapt", "add", "addict", "address", "adjust", "admit",
    "adult", "advance", "advice", "aerobic", "affair", "afford", "afraid", "again", "age", "agent",
    "agree", "ahead", "aim", "air", "airport", "aisle", "alarm", "album", "alcohol", "alert",
    "alien", "all", "alley", "allow", "almost", "alone", "alpha", "already", "also", "alter",
    "always", "amateur", "amazing", "among", "amount", "amused", "analyst", "anchor", "ancient", "anger",
    "angle", "angry", "animal", "ankle", "announce", "annual", "another", "answer", "antenna", "antique",
    "anxiety", "any", "apart", "apology", "appear", "apple", "approve", "april", "arch", "arctic",
    "area", "arena", "argue", "armed", "armor", "army", "around", "arrange", "arrest", "arrive",
    "arrow", "art", "artefact", "artist", "artwork", "ask", "aspect", "assault", "asset", "assist",
    "assume", "asthma", "athlete", "atom", "attack", "attend", "attitude", "attract", "auction", "audit",
    "august", "aunt", "author", "auto", "autumn", "average", "avocado", "avoid", "awake", "aware",
    "away", "awesome", "awful", "awkward", "axis", "baby", "bachelor", "bacon", "badge", "bag",
    "balance", "balcony", "ball", "bamboo", "banana", "banner", "bar", "barely", "bargain", "barrel",
    "base", "basic", "basket", "battle", "beach", "bean", "beauty", "because", "become", "beef",
    "before", "begin", "behave", "behind", "believe", "below", "belt", "bench", "benefit", "best",
    "betray", "better", "between", "beyond", "bicycle", "bid", "bike", "bind", "biology", "bird",
    "birth", "bitter", "black", "blade", "blame", "blanket", "blast", "bleak", "bless", "blind",
    "blood", "blossom", "blouse", "blue", "blur", "blush", "board", "boat", "body", "boil",
    "bomb", "bone", "bonus", "book", "boost", "border", "boring", "borrow", "boss", "bottom",
    "bounce", "box", "boy", "bracket", "brain", "brand", "brass", "brave", "bread", "breeze",
    "brick", "bridge", "brief", "bright", "bring", "brisk", "broccoli", "broken", "bronze", "broom",
    "brother", "brown", "brush", "bubble", "buddy", "budget", "buffalo", "build", "bulb", "bulk",
    "bullet", "bundle", "bunker", "burden", "burger", "burst", "bus", "business", "busy", "butter",
    "buyer", "buzz", "cabbage", "cabin", "cable", "cactus", "cage", "cake", "call", "calm",
    "camera", "camp", "can", "canal", "cancel", "candy", "cannon", "canoe", "canvas", "canyon",
    "capable", "capital", "captain", "car", "carbon", "card", "cargo", "carpet", "carry", "cart",
    "case", "cash", "casino", "castle", "casual", "cat", "catalog", "catch", "category", "cattle",
    "caught", "cause", "caution", "cave", "ceiling", "celery", "cement", "census", "century", "cereal",
    "certain", "chair", "chalk", "champion", "change", "chaos", "chapter", "charge", "chase", "chat",
    "cheap", "check", "cheese", "chef", "cherry", "chest", "chicken", "chief", "child", "chimney",
    "choice", "choose", "chronic", "chuckle", "chunk", "churn", "cigar", "cinnamon", "circle", "citizen",
    "city", "civil", "claim", "clap", "clarify", "claw", "clay", "clean", "clerk", "clever",
    "click", "client", "cliff", "climb", "clinic", "clip", "clock", "clog", "close", "cloth",
    "cloud", "clown", "club", "clump", "cluster", "clutch", "coach", "coast", "coconut", "code",
    "coffee", "coil", "coin", "collect", "color", "column", "combine", "come", "comfort", "comic",
    "common", "company", "concert", "conduct", "confirm", "congress", "connect", "consider", "control", "convince",
    "cook", "cool", "copper", "copy", "coral", "core", "corn", "correct", "cost", "cotton",
    "couch", "country", "couple", "course", "cousin", "cover", "coyote", "crack", "cradle", "craft",
    "cram", "crane", "crash", "crater", "crawl", "crazy", "cream", "credit", "creek", "crew",
    "cricket", "crime", "crisp", "critic", "crop", "cross", "crouch", "crowd", "crucial", "cruel",
    "cruise", "crumble", "crunch", "crush", "cry", "crystal", "cube", "culture", "cup", "cupboard",
    "curious", "current", "curtain", "curve", "cushion", "custom", "cute", "cycle", "dad", "damage",
    "damp", "dance", "danger", "daring", "dash", "daughter", "dawn", "day", "deal", "debate",
    "debris", "decade", "december", "decide", "decline", "decorate", "decrease", "deer", "defense", "define",
    "defy", "degree", "delay", "deliver", "demand", "demise", "denial", "dentist", "deny", "depart",
    "depend", "deposit", "depth", "deputy", "derive", "describe", "desert", "design", "desk", "despair",
    "destroy", "detail", "detect", "develop", "device", "devote", "diagram", "dial", "diamond", "diary",
    "dice", "diesel", "diet", "differ", "digital", "dignity", "dilemma", "dinner", "dinosaur", "direct",
    "dirt", "disagree", "discover", "disease", "dish", "dismiss", "disorder", "display", "distance", "divert",
    "divide", "divorce", "dizzy", "doctor", "document", "dog", "doll", "dolphin", "domain", "donate",
    "donkey", "donor", "door", "dose", "double", "dove", "draft", "dragon", "drama", "drastic",
    "draw", "dream", "dress", "drift", "drill", "drink", "drip", "drive", "drop", "drum",
    "dry", "duck", "dumb", "dune", "during", "dust", "dutch", "duty", "dwarf", "dynamic",
    "eager", "eagle", "early", "earn", "earth", "easily", "east", "easy", "echo", "ecology",
    "economy", "edge", "edit", "educate", "effort", "egg", "eight", "either", "elbow", "elder",
    "electric", "elegant", "element", "elephant", "elevator", "elite", "else", "embark", "embody", "embrace",
    "emerge", "emotion", "employ", "empower", "empty", "enable", "enact", "end", "endless", "endorse",
    "enemy", "energy", "enforce", "engage", "engine", "enhance", "enjoy", "enlist", "enough", "enrich",
    "enroll", "ensure", "enter", "entire", "entry", "envelope", "episode", "equal", "equip", "era",
    "erase", "erode", "erosion", "error", "erupt", "escape", "essay", "essence", "estate", "eternal",
    "ethics", "evidence", "evil", "evoke", "evolve", "exact", "example", "excess", "exchange", "excite",
    "exclude", "excuse", "execute", "exercise", "exhaust", "exhibit", "exile", "exist", "exit", "exotic",
    "expand", "expect", "expire", "explain", "expose", "express", "extend", "extra", "eye", "eyebrow",
    "fabric", "face", "faculty", "fade", "faint", "faith", "fall", "false", "fame", "family",
    "famous", "fan", "fancy", "fantasy", "farm", "fashion", "fat", "fatal", "father", "fatigue",
    "fault", "favorite", "feature", "february", "federal", "fee", "feed", "feel", "female", "fence",
    "festival", "fetch", "fever", "few", "fiber", "fiction", "field", "figure", "file", "film",
    "filter", "final", "find", "fine", "finger", "finish", "fire", "firm", "first", "fiscal",
    "fish", "fit", "fitness", "fix", "flag", "flame", "flash", "flat", "flavor", "flee",
    "flight", "flip", "float", "flock", "floor", "flower", "fluid", "flush", "fly", "foam",
    "focus", "fog", "foil", "fold", "follow", "food", "foot", "force", "forest", "forget",
    "fork", "fortune", "forum", "forward", "fossil", "foster", "found", "fox", "fragile", "frame",
    "frequent", "fresh", "friend", "fringe", "frog", "front", "frost", "frown", "frozen", "fruit",
    "fuel", "fun", "funny", "furnace", "fury", "future", "gadget", "gain", "galaxy", "gallery",
    "game", "gap", "garage", "garbage", "garden", "garlic", "garment", "gas", "gasp", "gate",
    "gather", "gauge", "gaze", "general", "genius", "genre", "gentle", "genuine", "gesture", "ghost",
    "giant", "gift", "giggle", "ginger", "giraffe", "girl", "give", "glad", "glance", "glare",
    "glass", "glide", "glimpse", "globe", "gloom", "glory", "glove", "glow", "glue", "goat",
    "goddess", "gold", "good", "goose", "gorilla", "gospel", "gossip", "govern", "gown", "grab",
    "grace", "grain", "grant", "grape", "grass", "gravity", "great", "green", "grid", "grief",
    "grit", "grocery", "group", "grow", "grunt", "guard", "guess", "guide", "guilt", "guitar",
    "gun", "gym", "habit", "hair", "half", "hammer", "hamster", "hand", "happy", "harbor",
    "hard", "harsh", "harvest", "hat", "have", "hawk", "hazard", "head", "health", "heart",
    "heavy", "hedgehog", "height", "hello", "helmet", "help", "hen", "hero", "hidden", "high",
    "hill", "hint", "hip", "hire", "history", "hobby", "hockey", "hold", "hole", "holiday",
    "hollow", "home", "honey", "hood", "hope", "horn", "horror", "horse", "hospital", "host",
    "hotel", "hour", "hover", "hub", "huge", "human", "humble", "humor", "hundred", "hungry",
    "hunt", "hurdle", "hurry", "hurt", "husband", "hybrid", "ice", "icon", "idea", "identify",
    "idle", "ignore", "ill", "illegal", "illness", "image", "imitate", "immense", "immune", "impact",
    "impose", "improve", "impulse", "inch", "include", "income", "increase", "index", "indicate", "indoor",
    "industry", "infant", "inflict", "inform", "inhale", "inherit", "initial", "inject", "injury", "inmate",
    "inner", "innocent", "input", "inquiry", "insane", "insect", "inside", "inspire", "install", "intact",
    "interest", "into", "invest", "invite", "involve", "iron", "island", "isolate", "issue", "item",
    "ivory", "jacket", "jaguar", "jar", "jazz", "jealous", "jeans", "jelly", "jewel", "job",
    "join", "joke", "journey", "joy", "judge", "juice", "jump", "jungle", "junior", "junk",
    "just", "kangaroo", "keen", "keep", "ketchup", "key", "kick", "kid", "kidney", "kind",
    "kingdom", "kiss", "kit", "kitchen", "kite", "kitten", "kiwi", "knee", "knife", "knock",
    "know", "lab", "label", "labor", "ladder", "lady", "lake", "lamp", "language", "laptop",
    "large", "later", "latin", "laugh", "laundry", "lava", "law", "lawn", "lawsuit", "layer",
    "lazy", "leader", "leaf", "learn", "leave", "lecture", "left", "leg", "legal", "legend",
    "leisure", "lemon", "lend", "length", "lens", "leopard", "lesson", "letter", "level", "liar",
    "liberty", "library", "license", "life", "lift", "light", "like", "limb", "limit", "link",
    "lion", "liquid", "list", "little", "live", "lizard", "load", "loan", "lobster", "local",
    "lock", "logic", "lonely", "long", "loop", "lottery", "loud", "lounge", "love", "loyal",
    "lucky", "luggage", "lumber", "lunar", "lunch", "luxury", "lyrics", "machine", "mad", "magic",
    "magnet", "maid", "mail", "main", "major", "make", "mammal", "man", "manage", "mandate",
    "mango", "mansion", "manual", "maple", "marble", "march", "margin", "marine", "market", "marriage",
    "mask", "mass", "master", "match", "material", "math", "matrix", "matter", "maximum", "maze",
    "meadow", "mean", "measure", "meat", "mechanic", "medal", "media", "melody", "melt", "member",
    "memory", "mention", "menu", "mercy", "merge", "merit", "merry", "mesh", "message", "metal",
    "method", "middle", "midnight", "milk", "million", "mimic", "mind", "minimum", "minor", "minute",
    "miracle", "mirror", "misery", "miss", "mistake", "mix", "mixed", "mixture", "mobile", "model",
    "modify", "mom", "moment", "monitor", "monkey", "monster", "month", "moon", "moral", "more",
    "morning", "mosquito", "mother", "motion", "motor", "mountain", "mouse", "move", "movie", "much",
    "muffin", "mule", "multiply", "muscle", "museum", "mushroom", "music", "must", "mutual", "myself",
    "mystery", "myth", "naive", "name", "napkin", "narrow", "nasty", "nation", "nature", "near",
    "neck", "need", "negative", "neglect", "neither", "nephew", "nerve", "nest", "net", "network",
    "neutral", "never", "news", "next", "nice", "night", "noble", "noise", "nominee", "noodle",
    "normal", "north", "nose", "notable", "note", "nothing", "notice", "novel", "now", "nuclear",
    "number", "nurse", "nut", "oak", "obey", "object", "oblige", "obscure", "observe", "obtain",
    "obvious", "occur", "ocean", "october", "odor", "off", "offer", "office", "often", "oil",
    "okay", "old", "olive", "olympic", "omit", "once", "one", "onion", "online", "only",
    "open", "opera", "opinion", "oppose", "option", "orange", "orbit", "orchard", "order", "ordinary",
    "organ", "orient", "original", "orphan", "ostrich", "other", "outdoor", "outer", "output", "outside",
    "oval", "oven", "over", "own", "owner", "oxygen", "oyster", "ozone", "pact", "paddle",
    "page", "pair", "palace", "palm", "panda", "panel", "panic", "panther", "paper", "parade",
    "parent", "park", "parrot", "party", "pass", "patch", "path", "patient", "patrol", "pattern",
    "pause", "pave", "payment", "peace", "peanut", "pear", "peasant", "pelican", "pen", "penalty",
    "pencil", "people", "pepper", "perfect", "permit", "person", "pet", "phone", "photo", "phrase",
    "physical", "piano", "picnic", "picture", "piece", "pig", "pigeon", "pill", "pilot", "pink",
    "pioneer", "pipe", "pistol", "pitch", "pizza", "place", "planet", "plastic", "plate", "play",
    "please", "pledge", "pluck", "plug", "plunge", "poem", "poet", "point", "polar", "pole",
    "police", "pond", "pony", "pool", "popular", "portion", "position", "possible", "post", "potato",
    "pottery", "poverty", "powder", "power", "practice", "praise", "predict", "prefer", "prepare", "present",
    "pretty", "prevent", "price", "pride", "primary", "print", "priority", "prison", "private", "prize",
    "problem", "process", "produce", "profit", "program", "project", "promote", "proof", "property", "prosper",
    "protect", "proud", "provide", "public", "pudding", "pull", "pulp", "pulse", "pumpkin", "punch",
    "pupil", "puppy", "purchase", "purity", "purpose", "purse", "push", "put", "puzzle", "pyramid",
    "quality", "quantum", "quarter", "question", "quick", "quit", "quiz", "quote", "rabbit", "raccoon",
    "race", "rack", "radar", "radio", "rail", "rain", "raise", "rally", "ramp", "ranch",
    "random", "range", "rapid", "rare", "rate", "rather", "raven", "raw", "razor", "ready",
    "real", "reason", "rebel", "rebuild", "recall", "receive", "recipe", "record", "recycle", "reduce",
    "reflect", "reform", "refuse", "region", "regret", "regular", "reject", "relax", "release", "relief",
    "rely", "remain", "remember", "remind", "remove", "render", "renew", "rent", "reopen", "repair",
    "repeat", "replace", "report", "require", "rescue", "resemble", "resist", "resource", "response", "result",
    "retire", "retreat", "return", "reunion", "reveal", "review", "reward", "rhythm", "rib", "ribbon",
    "rice", "rich", "ride", "ridge", "rifle", "right", "rigid", "ring", "riot", "ripple",
    "risk", "ritual", "rival", "river", "road", "roast", "robot", "robust", "rocket", "romance",
    "roof", "rookie", "room", "rose", "rotate", "rough", "round", "route", "royal", "rubber",
    "rude", "rug", "rule", "run", "runway", "rural", "sad", "saddle", "sadness", "safe",
    "sail", "salad", "salmon", "salon", "salt", "salute", "same", "sample", "sand", "satisfy",
    "satoshi", "sauce", "sausage", "save", "say", "scale", "scan", "scare", "scatter", "scene",
    "scheme", "school", "science", "scissors", "scorpion", "scout", "scrap", "screen", "script", "scrub",
    "sea", "search", "season", "seat", "second", "secret", "section", "security", "seed", "seek",
    "segment", "select", "sell", "seminar", "senior", "sense", "sentence", "series", "service", "session",
    "settle", "setup", "seven", "shadow", "shaft", "shallow", "share", "shed", "shell", "sheriff",
    "shield", "shift", "shine", "ship", "shiver", "shock", "shoe", "shoot", "shop", "short",
    "shoulder", "shove", "shrimp", "shrug", "shuffle", "shy", "sibling", "sick", "side", "siege",
    "sight", "sign", "silent", "silk", "silly", "silver", "similar", "simple", "since", "sing",
    "siren", "sister", "situate", "six", "size", "skate", "sketch", "ski", "skill", "skin",
    "skirt", "skull", "slab", "slam", "sleep", "slender", "slice", "slide", "slight", "slim",
    "slogan", "slot", "slow", "slush", "small", "smart", "smile", "smoke", "smooth", "snack",
    "snake", "snap", "sniff", "snow", "soap", "soccer", "social", "sock", "soda", "soft",
    "solar", "soldier", "solid", "solution", "solve", "someone", "song", "soon", "sorry", "sort",
    "soul", "sound", "soup", "source", "south", "space", "spare", "spatial", "spawn", "speak",
    "special", "speed", "spell", "spend", "sphere", "spice", "spider", "spike", "spin", "spirit",
    "split", "spoil", "sponsor", "spoon", "sport", "spot", "spray", "spread", "spring", "spy",
    "square", "squeeze", "squirrel", "stable", "stadium", "staff", "stage", "stairs", "stamp", "stand",
    "start", "state", "stay", "steak", "steel", "stem", "step", "stereo", "stick", "still",
    "sting", "stock", "stomach", "stone", "stool", "story", "stove", "strategy", "street", "strike",
    "strong", "struggle", "student", "stuff", "stumble", "style", "subject", "submit", "subway", "success",
    "such", "sudden", "suffer", "sugar", "suggest", "suit", "summer", "sun", "sunny", "sunset",
    "super", "supply", "supreme", "sure", "surface", "surge", "surprise", "surround", "survey", "suspect",
    "sustain", "swallow", "swamp", "swap", "swarm", "swear", "sweet", "swift", "swim", "swing",
    "switch", "sword", "symbol", "symptom", "syrup", "system", "table", "tackle", "tag", "tail",
    "talent", "talk", "tank", "tape", "target", "task", "taste", "tattoo", "taxi", "teach",
    "team", "tell", "ten", "tenant", "tennis", "tent", "term", "test", "text", "thank",
    "that", "theme", "then", "theory", "there", "they", "thing", "this", "thought", "three",
    "thrive", "throw", "thumb", "thunder", "ticket", "tide", "tiger", "tilt", "timber", "time",
    "tiny", "tip", "tired", "tissue", "title", "toast", "tobacco", "today", "toddler", "toe",
    "together", "toilet", "token", "tomato", "tomorrow", "tone", "tongue", "tonight", "tool", "tooth",
    "top", "topic", "topple", "torch", "tornado", "tortoise", "toss", "total", "tourist", "toward",
    "tower", "town", "toy", "track", "trade", "traffic", "tragic", "train", "transfer", "trap",
    "trash", "travel", "tray", "treat", "tree", "trend", "trial", "tribe", "trick", "trigger",
    "trim", "trip", "trophy", "trouble", "truck", "true", "truly", "trumpet", "trust", "truth",
    "try", "tube", "tuition", "tumble", "tuna", "tunnel", "turkey", "turn", "turtle", "twelve",
    "twenty", "twice", "twin", "twist", "two", "type", "typical", "ugly", "umbrella", "unable",
    "unaware", "uncle", "uncover", "under", "undo", "unfair", "unfold", "unhappy", "uniform", "unique",
    "unit", "universe", "unknown", "unlock", "until", "unusual", "unveil", "update", "upgrade", "uphold",
    "upon", "upper", "upset", "urban", "urge", "usage", "use", "used", "useful", "useless",
    "usual", "utility", "vacant", "vacuum", "vague", "valid", "valley", "valve", "van", "vanish",
    "vapor", "various", "vast", "vault", "vehicle", "velvet", "vendor", "venture", "venue", "verb",
    "verify", "version", "very", "vessel", "veteran", "viable", "vibrant", "vicious", "victory", "video",
    "view", "village", "vintage", "violin", "virtual", "virus", "visa", "visit", "visual", "vital",
    "vivid", "vocal", "voice", "void", "volcano", "volume", "vote", "voyage", "wage", "wagon",
    "wait", "walk", "wall", "walnut", "want", "warfare", "warm", "warrior", "wash", "wasp",
    "water", "wave", "way", "wealth", "weapon", "wear", "weasel", "weather", "web", "wedding",
    "weekend", "weird", "welcome", "west", "wet", "whale", "what", "wheat", "wheel", "when",
    "where", "whip", "whisper", "wide", "width", "wild", "will", "win", "window", "wine",
    "wing", "wink", "winner", "winter", "wire", "wisdom", "wise", "wish", "witness", "wolf",
    "woman", "wonder", "wood", "wool", "word", "work", "world", "worry", "worth", "wrap",
    "wreck", "wrist", "write", "wrong", "yard", "year", "yellow", "you", "young", "youth",
    "zebra", "zero", "zone", "zoo",



    # Specify your 12 (or more) desired words here.
]
MNEMONIC_LENGTH = 12

# Infura Project ID - No longer used for EVM balance checks, but remains in RPC URLs
INFURA_PROJECT_ID = "e4390055418a474a88ea23824351018c"

COINGECKO_API_BASE = "https://api.coingecko.com/api/v3"

MAX_ATTEMPTS_PER_RUN = 30000
MIN_BALANCE_USD_THRESHOLD = 0.0001

# Network Configurations - API Keys removed from EVM scanners
NETWORK_CONFIGS = {
    "Ethereum": {
        "rpc_url": f"https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}",
        "chain_id": 1,
        "is_poa": False,
        "native_symbol": "ETH",
        "coingecko_id": "ethereum",
        "explorer_url": "https://etherscan.io/address/", # Base URL for scraping
        "bip44_coin": Bip44Coins.ETHEREUM,
        "erc20_tokens": {
            "USDT (ERC-20)": {"address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6, "coingecko_id": "tether"},
            "USDC (ERC-20)": {"address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "decimals": 6, "coingecko_id": "usd-coin"},
        }
    },
    "Bitcoin": {
        "native_symbol": "BTC",
        "coingecko_id": "bitcoin",
        # Corrected Blockstream.info API base URL
        "explorer_api": "https://blockstream.info/api/address/",
        "bip44_coin": Bip44Coins.BITCOIN,
    },
    "Solana": {
        "native_symbol": "SOL",
        "coingecko_id": "solana",
        "explorer_api": "https://api.mainnet-beta.solana.com",
        "derivation_path_sol": "m/44'/501'/0'/0'",
        "bip44_coin": Bip44Coins.SOLANA,
    },
    "Tron": {
        "native_symbol": "TRX",
        "coingecko_id": "tron",
        "explorer_api": "https://apilist.tronscan.org/api/account", # Correct API for balance and transactions (uses query param ?address=)
        "explorer_url": "https://tronscan.org/#/address/", # Base URL for direct linking (not used for scraping anymore in this code)
        "transactions_api": "https://apilist.tronscan.org/api/transaction", # Still here for completeness, though account API gives total txs
        "bip44_coin": Bip44Coins.TRON,
        "trc20_tokens": {
            "USDT (TRC-20)": {"address": "TR7NHqjeKQxGTCi8qT8fcTfEPYptx2gCz", "decimals": 6, "coingecko_id": "tether"}
        }
    }
}

# --- 2. Helper Functions ---

def derive_addresses(mnemonic_phrase: str, passphrase: str = "") -> dict:
    """
    Derives addresses for various cryptocurrencies from a single mnemonic phrase using bip_utils.
    Returns a dictionary of addresses or an "Error" key with a description if seed derivation fails.
    This function acts as the BIP-39 validation point.
    """
    addresses = {}
    try:
        seed_generator = Bip39SeedGenerator(mnemonic_phrase)
        seed_bytes = seed_generator.Generate(passphrase)
    except Exception as e:
        return {"Error": f"Mnemonic seed generation failed (BIP-39 validation error): {e}"}

    try:
        # EVM (Ethereum, Polygon, BNB Smart Chain use the same derivation path)
        bip44_eth = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        eth_account = bip44_eth.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        addresses["EVM"] = eth_account.PublicKey().ToAddress()
    except Exception as e:
        addresses["EVM"] = f"Error deriving EVM address: {e}"

    if Key: # Bitcoinlib dependency check - BTC address generation
        try:
            bip44_btc = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
            btc_account = bip44_btc.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
            addresses["Bitcoin"] = btc_account.PublicKey().ToAddress()
        except Exception as e:
            addresses["Bitcoin"] = f"Error deriving Bitcoin address: {e}"
    else:
        addresses["Bitcoin"] = colored("bitcoinlib is not installed, Bitcoin address could not be generated.", "red")


    if PublicKey: # Solana dependency check
        try:
            bip44_sol = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)
            sol_account = bip44_sol.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
            addresses["Solana"] = str(PublicKey(sol_account.PublicKey().RawCompressed().ToBytes()))
        except Exception as e:
            addresses["Solana"] = f"Error deriving Solana address: {e}"
    
    if TronPrivateKey: # Tronpy dependency check
        try:
            bip44_tron = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
            tron_account_obj = bip44_tron.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
            
            evm_private_key_bytes = tron_account_obj.PrivateKey().Raw().ToBytes()
            
            tron_private_key_obj = TronPrivateKey(evm_private_key_bytes)
            addresses["Tron"] = tron_private_key_obj.public_key.to_base58check_address() # Tron's base58 address
        except Exception as e:
            addresses["Tron"] = f"Error deriving Tron address: {e}"

    return addresses

# --- Web Scraping Function for EVM Chains ---
@lru_cache(maxsize=128)
async def get_evm_balance_and_transactions_from_scrape(address, explorer_url, native_symbol):
    """
    Gets native coin balance and checks for transactions by scraping Etherscan-like sites.
    """
    url = f"{explorer_url}{address}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}

    try:
        response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        native_balance = 0.0
        usd_balance_from_scrape = 0.0
        has_transactions = False

        eth_value_header = soup.find("h4", string=lambda text: text and f"{native_symbol} Value" in text.strip())
        if not eth_value_header:
            eth_value_header = soup.find("h4", string=lambda text: text and "Eth Value" in text.strip())

        if eth_value_header:
            value_div = eth_value_header.find_parent("div")
            if value_div:
                eth_value_text = value_div.text.strip()
                match_usd = re.search(r"\$\d+(\.\d+)?", eth_value_text)
                if match_usd:
                    try:
                        usd_balance_from_scrape = float(match_usd.group().replace('$', ''))
                    except ValueError:
                        pass
                
                native_balance_span = value_div.find("span", class_="text-dark", string=lambda text: text and native_symbol in text)
                if not native_balance_span:
                    native_balance_span = soup.find("div", class_="row", string=lambda text: text and "Ether Balance" in text.strip())
                    if native_balance_span:
                        native_balance_span = native_balance_span.find("span", class_="text-dark")

                if native_balance_span:
                    balance_text_native = native_balance_span.text.strip().replace(native_symbol, '').replace(',', '')
                    match_native = re.search(r"(\d+(\.\d+)?)", balance_text_native)
                    if match_native:
                        try:
                            native_balance = float(match_native.group(1))
                        except ValueError:
                            pass
        
        tx_count_span = soup.find("span", class_="d-block d-md-inline-block text-dark fw-medium",
                                   string=lambda text: text and "Transaction Count" in text)
        if tx_count_span:
            tx_count_text = tx_count_span.text.strip().replace(" Transaction Count", "").replace(",", "")
            try:
                tx_count = int(tx_count_text)
                if tx_count > 0:
                    has_transactions = True
            except ValueError:
                pass

        return native_balance, usd_balance_from_scrape, has_transactions, None
    except requests.exceptions.RequestException as e:
        return 0.0, 0.0, False, f"HTTP request error: {e}"
    except Exception as e:
        return 0.0, 0.0, False, f"Scraping error: {e}"

# --- API Based Functions (for non-EVM chains and Coingecko) ---
@lru_cache(maxsize=1)
async def get_crypto_prices_async(coin_ids_list):
    """
    Asynchronously fetches cryptocurrency prices from CoinGecko.
    """
    try:
        ids_str = ",".join(coin_ids_list)
        response = await asyncio.to_thread(requests.get, f"{COINGECKO_API_BASE}/simple/price?ids={ids_str}&vs_currencies=usd", timeout=10)
        response.raise_for_status()
        data = response.json()
        prices = {coin_id: data[coin_id]['usd'] for coin_id in data if 'usd' in data[coin_id]}
        return prices, None
    except requests.exceptions.RequestException as e:
        return None, f"Error getting prices from CoinGecko: {e}"
    except Exception as e:
        return None, f"Unexpected error getting prices: {e}"

@lru_cache(maxsize=128)
async def get_btc_balance_and_transactions(btc_address):
    """
    Asynchronously fetches Bitcoin balance and transaction status from Blockstream.info API.
    Parses JSON response for `chain_stats.funded_txo_sum`, `chain_stats.spent_txo_sum`, and `chain_stats.tx_count`.
    """
    explorer_url = f"{NETWORK_CONFIGS['Bitcoin']['explorer_api']}{btc_address}"

    try:
        response = await asyncio.to_thread(requests.get, explorer_url, timeout=10)
        response.raise_for_status() # Raise for HTTP errors
        data = response.json()

        balance_satoshi = 0
        has_transactions = False

        if 'chain_stats' in data:
            funded_sum = data['chain_stats'].get('funded_txo_sum', 0)
            spent_sum = data['chain_stats'].get('spent_txo_sum', 0)
            balance_satoshi = funded_sum - spent_sum
            
            tx_count = data['chain_stats'].get('tx_count', 0)
            if tx_count > 0:
                has_transactions = True
        
        balance_btc = balance_satoshi / (10**8) # Convert satoshi to BTC

        return balance_btc, has_transactions, None
    except requests.exceptions.RequestException as e:
        return None, None, f"HTTP request error for Blockstream.info: {e}"
    except (ValueError, KeyError) as e:
        return None, None, f"Error parsing data from Blockstream.info: {e}"
    except Exception as e:
        return None, None, f"Unexpected error getting BTC balance/transactions: {e}"

@lru_cache(maxsize=128)
async def get_sol_balance_and_transactions(sol_address):
    """
    Asynchronously fetches Solana balance and transaction status from Solana RPC.
    """
    try:
        headers = {"Content-Type": "application/json"}
        payload_balance = {
            "jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [sol_address]
        }
        payload_tx = {
            "jsonrpc": "2.0", "id": 1, "method": "getConfirmedSignaturesForAddress2",
            "params": [sol_address, {"limit": 1}]
        }

        balance_response = await asyncio.to_thread(requests.post, NETWORK_CONFIGS['Solana']['explorer_api'], headers=headers, json=payload_balance, timeout=10)
        balance_response.raise_for_status()
        balance_data = balance_response.json()

        tx_response = await asyncio.to_thread(requests.post, NETWORK_CONFIGS['Solana']['explorer_api'], headers=headers, json=payload_tx, timeout=10)
        tx_response.raise_for_status()
        tx_data = tx_response.json()

        balance_sol = 0
        if 'result' in balance_data and 'value' in balance_data['result']:
            balance_lamports = balance_data['result']['value']
            balance_sol = balance_lamports / (10**9)

        has_transactions = False
        if 'result' in tx_data and tx_data['result']:
            has_transactions = len(tx_data['result']) > 0

        return balance_sol, has_transactions, None
    except requests.exceptions.RequestException as e:
        return None, None, f"Error getting SOL balance/transactions from Solana RPC: {e}"
    except Exception as e:
        return None, None, f"Unexpected error getting SOL balance/transactions: {e}"


# --- Updated TRX Balance and Transaction check function ---
@lru_cache(maxsize=128)
async def get_trx_balance_and_tokens_and_transactions(trx_address):
    """
    Asynchronously fetches Tron balance and TRC-20 token balances from Tronscan API (public endpoint).
    It does NOT perform web scraping for TRX or USD values from tronscan.org/#/address/.
    USD value for TRX is calculated using CoinGecko price.
    """
    # Corrected API URL as per user's confirmation: https://apilist.tronscan.org/api/account?address={address}
    api_url = f"{NETWORK_CONFIGS['Tron']['explorer_api']}?address={trx_address}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    }

    balance_trx_api = 0.0 # TRX balance from API
    has_transactions = False
    token_balances = {} # TRC-20 token balances from API
    error_message = None

    try:
        # --- API based data retrieval for TRX and TRC-20 balances and transaction count ---
        api_response = await asyncio.to_thread(requests.get, api_url, headers=headers, timeout=10)
        api_response.raise_for_status() # Raise for HTTP errors
        api_data = api_response.json()

        if 'balance' in api_data:
            balance_sun = api_data['balance']
            balance_trx_api = balance_sun / (10**6) # Convert SUN to TRX

        if 'totalTransactionCount' in api_data and api_data['totalTransactionCount'] > 0:
            has_transactions = True

        if 'tokenBalances' in api_data:
            for token_info in api_data['tokenBalances']:
                for token_symbol, config in NETWORK_CONFIGS['Tron']['trc20_tokens'].items():
                    if (token_info.get('tokenId') and token_info['tokenId'].upper() == config['address'].upper()) or \
                       (token_info.get('tokenAbbr') and token_info['tokenAbbr'].upper() == token_symbol.split(' ')[0].upper()):
                        try:
                            raw_balance = int(token_info['balance'])
                            token_balances[token_symbol] = raw_balance / (10 ** config['decimals'])
                        except (ValueError, KeyError):
                            pass

    except requests.exceptions.RequestException as e:
        error_message = f"HTTP request error for Tron API: {e}"
    except Exception as e:
        error_message = f"Tron API data retrieval error: {e}"

    # We now only return data from the API, no scraped values
    return balance_trx_api, token_balances, has_transactions, error_message

# --- 3. Main Logic ---
async def main():
    print(colored("--- Multi-Chain Wallet Balance Scanner (Custom Word Permutations) ---", "cyan"))
    print(colored("!!! This script uses web scraping for EVM networks. !!!", "red"))
    print(colored("!!! Tron (TRX) balances and transactions are checked via Tronscan API (public endpoint). !!!", "yellow"))
    print(colored("!!! Bitcoin (BTC) balances and transactions are checked via Blockstream.info API. !!!", "yellow"))
    print(colored("!!! Web scraping is highly unreliable for EVM networks and may lead to your IP address being blocked by Explorers. !!!", "red"))
    print(colored("!!! HTML structure changes will invalidate the scraping code. Use at your own risk. !!!", "red"))
    print(colored("-" * 60, "white"))

    if len(WORD_POOL) < MNEMONIC_LENGTH:
        print(colored(f"[-] Error: WORD_POOL must contain at least {MNEMONIC_LENGTH} unique words to generate a {MNEMONIC_LENGTH}-word mnemonic.", "red"))
        return

    coin_ids_for_prices = set()
    for net_config in NETWORK_CONFIGS.values():
        if "coingecko_id" in net_config:
            coin_ids_for_prices.add(net_config["coingecko_id"])
        if "erc20_tokens" in net_config:
            for token_info in net_config["erc20_tokens"].values():
                coin_ids_for_prices.add(token_info["coingecko_id"])
        if "trc20_tokens" in net_config:
            for token_info in net_config["trc20_tokens"].values():
                coin_ids_for_prices.add(token_info["coingecko_id"])

    prices, price_error = await get_crypto_prices_async(tuple(coin_ids_for_prices))
    if price_error:
        print(colored(f"[!] Price retrieval error: {price_error}. USD balance will not be shown.", "red"))
        prices = {}
    else:
        print(colored("\n[+] Current Cryptocurrency Prices (USD):", "green"))
        for coin_id, price in prices.items():
            print(f"  - {coin_id.ljust(15)}: ${price:.4f}")
        print(colored("-" * 60, "white"))

    valid_mnemonics_count = 0
    invalid_mnemonics_count = 0
    attempts_made = 0
    wallets_with_balance_count = 0

    print(colored(f"\n[+] Starting permutation generation and checking your words (with a limit of {MAX_ATTEMPTS_PER_RUN} attempts)...", "cyan"))
    print(colored("-" * 60, "white"))

    total_permutations = math.perm(len(WORD_POOL), MNEMONIC_LENGTH)
    print(colored(f"[INFO] Total possible combinations ({MNEMONIC_LENGTH} words from {len(WORD_POOL)}): {total_permutations:,}", "blue"))

    for i, perm_words in enumerate(islice(permutations(WORD_POOL, MNEMONIC_LENGTH), MAX_ATTEMPTS_PER_RUN)):
        attempts_made += 1
        current_secret_phrase = " ".join(perm_words)

        derived_addresses = derive_addresses(current_secret_phrase)

        if "Error" in derived_addresses:
            invalid_mnemonics_count += 1
            print(colored(f"[-] Invalid mnemonic (BIP-39 check failed) {attempts_made}/{MAX_ATTEMPTS_PER_RUN}: {current_secret_phrase}", "blue"))
            continue

        valid_mnemonics_count += 1
        print(colored(f"\n[+] Valid mnemonic (BIP-39 compliant) {attempts_made}/{MAX_ATTEMPTS_PER_RUN}: {current_secret_phrase}", "light_yellow"))
        for chain, addr in derived_addresses.items():
            # Special handling for error message from derive_addresses for Bitcoin
            if "Error" in str(addr) or "is not installed" in str(addr):
                print(colored(f"    {chain} Address: {addr}", "red"))
            else:
                print(colored(f"    {chain} Address: {addr}", "light_yellow"))


        all_found_balances_usd = []
        has_any_transactions = False

        # --- Checking balances and transaction history on EVM-compatible networks (using WEB SCRAPING) ---
        for network_name in ["Ethereum"]: # Only for Ethereum
            config = NETWORK_CONFIGS[network_name]
            # Ensure BTC address was successfully derived before checking balance
            if network_name == "Bitcoin" and ("Error" in derived_addresses.get("Bitcoin", "") or "is not installed" in derived_addresses.get("Bitcoin", "")):
                # Skip checking if bitcoinlib is not installed or derivation failed
                continue

            if "EVM" in derived_addresses and "Error" not in derived_addresses["EVM"]:
                evm_address = derived_addresses["EVM"]
                print(colored(f"  [+] Checking {network_name} (web scraping)...", "cyan"))

                native_balance, usd_balance_from_scrape, has_tx, scrape_error = await get_evm_balance_and_transactions_from_scrape(
                    evm_address, config["explorer_url"], config["native_symbol"]
                )

                if scrape_error:
                    print(colored(f"    [!] Error checking {network_name}: {scrape_error}", "red"))
                else:
                    if usd_balance_from_scrape > 0:
                        print(colored(f"    ✅ Wallet has balance: ${usd_balance_from_scrape:.2f} (scraped value)", "green"))
                        all_found_balances_usd.append(usd_balance_from_scrape)
                    elif native_balance > 0:
                        print(colored(f"    [+] {config['native_symbol']} Balance: {native_balance:.6f}", "white"))
                        if config["coingecko_id"] in prices and float(native_balance) > 0:
                            usd_value = float(native_balance) * prices[config["coingecko_id"]]
                            all_found_balances_usd.append(usd_value)
                            print(colored(f"      ~ Approximately ${usd_value:.2f} (calculated with CoinGecko price)", "yellow"))
                    else:
                        print(colored(f"    ❌ Balance is 0 ({config['native_symbol']})", "red"))

                    if has_tx:
                        print(colored(f"    [+] Transactions found on {network_name}!", "green"))
                        has_any_transactions = True
                    else:
                        print(colored(f"    [-] No transactions found on {network_name}.", "red"))

        # --- Checking balances and transaction history on non-EVM networks (using APIs) ---
        # Changed to use Blockstream.info API which handles both balance and transaction count from one endpoint
        if "Bitcoin" in derived_addresses and "Error" not in derived_addresses["Bitcoin"] and "is not installed" not in derived_addresses["Bitcoin"]:
            btc_address = derived_addresses["Bitcoin"]
            print(colored(f"  [+] Checking Bitcoin (BTC)... (using Blockstream.info API)", "cyan"))
            btc_balance, has_btc_transactions, btc_error = await get_btc_balance_and_transactions(btc_address)
            if btc_balance is not None:
                print(colored(f"    [+] BTC Balance: {btc_balance:.8f}", "white"))
                if NETWORK_CONFIGS["Bitcoin"]["coingecko_id"] in prices and float(btc_balance) > 0:
                    usd_value = float(btc_balance) * prices[NETWORK_CONFIGS["Bitcoin"]["coingecko_id"]]
                    all_found_balances_usd.append(usd_value)
                    print(colored(f"      ~ Approximately ${usd_value:.2f}", "yellow"))
                if has_btc_transactions:
                    print(colored(f"    [+] Transactions found on Bitcoin!", "green"))
                    has_any_transactions = True
                else:
                    print(colored(f"    [-] No transactions found on Bitcoin.", "red"))
            elif btc_error:
                print(colored(f"    [!] BTC balance/transaction check error: {btc_error}", "red"))

        if "Solana" in derived_addresses and "Error" not in derived_addresses["Solana"]:
            sol_address = derived_addresses["Solana"]
            print(colored(f"  [+] Checking Solana (SOL)...", "cyan"))
            sol_balance, has_sol_transactions, sol_error = await get_sol_balance_and_transactions(sol_address)
            if sol_balance is not None:
                print(colored(f"    [+] SOL Balance: {sol_balance:.8f}", "white"))
                if NETWORK_CONFIGS["Solana"]["coingecko_id"] in prices and float(sol_balance) > 0:
                    usd_value = float(sol_balance) * prices[NETWORK_CONFIGS["Solana"]["coingecko_id"]]
                    all_found_balances_usd.append(usd_value)
                    print(colored(f"      ~ Approximately ${usd_value:.2f}", "yellow"))
                if has_sol_transactions:
                    print(colored(f"    [+] Transactions found on Solana!", "green"))
                    has_any_transactions = True
                else:
                    print(colored(f"    [-] No transactions found on Solana.", "red"))
            elif sol_error:
                print(colored(f"    [!] SOL balance/transaction check error: {sol_error}", "red"))
        
        if "Tron" in derived_addresses and "Error" not in derived_addresses["Tron"]:
            trx_address = derived_addresses["Tron"]
            # Call the updated get_trx_balance_and_tokens_and_transactions using only API
            print(colored(f"  [+] Checking Tron (TRX)... (using Tronscan API)", "cyan"))
            trx_balance_api, trc20_balances_api, has_trx_transactions, trx_error = await get_trx_balance_and_tokens_and_transactions(trx_address)
            
            if trx_error:
                print(colored(f"    [!] TRX balance/token/transaction check error: {trx_error}", "red"))
            elif trx_balance_api is not None: # Check if API call was successful
                if trx_balance_api > 0: # If API TRX balance is found
                    print(colored(f"    [+] TRX Balance (API): {trx_balance_api:.6f}", "white"))
                    if NETWORK_CONFIGS["Tron"]["coingecko_id"] in prices and float(trx_balance_api) > 0:
                        usd_value = float(trx_balance_api) * prices[NETWORK_CONFIGS["Tron"]["coingecko_id"]]
                        all_found_balances_usd.append(usd_value)
                        print(colored(f"      ~ Approximately ${usd_value:.2f} (calculated with CoinGecko price)", "yellow"))
                else:
                    print(colored(f"    ❌ Balance is 0 (TRX)", "red"))

                # Report TRC-20 balances from API
                for token_symbol, balance in trc20_balances_api.items():
                    if balance > 0: # Only print if token balance is greater than 0
                        print(colored(f"    [+] {token_symbol} Balance (Tron API): {balance:.6f}", "white"))
                        token_config = NETWORK_CONFIGS["Tron"]["trc20_tokens"].get(token_symbol)
                        if token_config and token_config["coingecko_id"] in prices and float(balance) > 0:
                            usd_value = float(balance) * prices[token_config["coingecko_id"]]
                            all_found_balances_usd.append(usd_value)
                            print(colored(f"      ~ Approximately ${usd_value:.2f}", "yellow"))

                if has_trx_transactions:
                    print(colored(f"    [+] Transactions found on Tron!", "green"))
                    has_any_transactions = True
                else:
                    print(colored(f"    [-] No transactions found on Tron.", "red"))

        # --- Summarizing results and saving to file ---
        total_sum_usd = sum(all_found_balances_usd)
        print(colored(f"    [=] Estimated Total Value (USD): ${total_sum_usd:.2f}", "light_green"))

        if total_sum_usd >= MIN_BALANCE_USD_THRESHOLD or has_any_transactions:
            wallets_with_balance_count += 1
            status_message = ""
            if total_sum_usd >= MIN_BALANCE_USD_THRESHOLD:
                status_message += f"with balance (> ${MIN_BALANCE_USD_THRESHOLD:.2f})"
            if has_any_transactions:
                if status_message:
                    status_message += " and "
                status_message += "with transactions"
            print(colored(f"    [+] Wallet found {status_message}!", "green"))

            output_path = os.path.join(os.getcwd(), "found_wallets.txt")
            with open(output_path, "a", encoding='utf-8') as f:
                f.write(f"Mnemonic: {current_secret_phrase}\n")
                for chain, addr in derived_addresses.items():
                    # Write only if it's a valid address or explicitly not an error message
                    if "Error" not in str(addr) and "is not installed" not in str(addr):
                        f.write(f"{chain} Address: {addr}\n")
                    elif chain == "Bitcoin" and "is not installed" in str(addr):
                        f.write(f"{chain} Address: {addr}\n") # Still write the warning to file if it occurs
                f.write(f"Estimated Total Value (USD): ${total_sum_usd:.2f}\n")
                f.write(f"Transactions Found: {'Yes' if has_any_transactions else 'No'}\n")
                f.write("-" * 50 + "\n\n")
            print(colored(f"    [+] Information saved to {output_path}", "light_yellow"))
        else:
            print(colored("    ❌ Wallet has no balance and no transactions found.", "red"))

        # Displaying progress
        if attempts_made % 10 == 0 or attempts_made == MAX_ATTEMPTS_PER_RUN:
            print(colored(f"\n[INFO] Checked {attempts_made:,} mnemonics. Valid: {valid_mnemonics_count}, Wallets with balance/transactions: {wallets_with_balance_count}, Invalid (BIP-39 check failed): {invalid_mnemonics_count}", "cyan"))

        if attempts_made >= MAX_ATTEMPTS_PER_RUN:
            print(colored(f"\n[INFO] Maximum attempts limit reached ({MAX_ATTEMPTS_PER_RUN}). Program stopping.", "yellow"))
            break

        # Delay for web scraping/API calls to avoid rate limits
        time.sleep(0) # 1 second delay for each valid mnemonic check

    print(colored("\n--- Check completed ---", "cyan"))
    print(colored(f"Total mnemonics checked: {attempts_made}", "light_green"))
    print(colored(f"Valid mnemonics found (i.e., whose BIP-39 derivation was successful): {valid_mnemonics_count}", "green"))
    print(colored(f"Wallets found with balance/transactions: {wallets_with_balance_count}", "green"))
    print(colored(f"Invalid mnemonics (BIP-39 check failed): {invalid_mnemonics_count}", "red"))

if __name__ == "__main__":
    asyncio.run(main())
