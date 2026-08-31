import os
import json
import time
import requests
import sys
import threading
import itertools
import re
import base64
import binascii
import blackboxprotobuf
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# ========== OWNER CONFIG ==========
OWNER = "N6"
CHANNEL = "@O000000000000o_X_o000000000000O"
OB_VERSION = "OB54"

# ========== CRYPTO KEYS ==========
AeSkEy = b'Yg&tc%DEuh6%Zc^8'
AeSiV  = b'6oyZDr22E3ychjM%'

# ========== REGION CONFIG ==========
REGION_LANG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", 
    "TH": "th", "BD": "bn", "PK": "ur", "TW": "zh", 
    "CIS": "ru", "SAC": "es", "BR": "pt", "SG": "en"
}

REGION_URLS = {
    "IND": "https://client.ind.freefiremobile.com",
    "ID": "https://clientbp.ggblueshark.com",
    "BR": "https://client.us.freefiremobile.com",
    "ME": "https://clientbp.common.ggbluefox.com",
    "VN": "https://clientbp.ggblueshark.com",
    "TH": "https://clientbp.common.ggbluefox.com",
    "CIS": "https://clientbp.ggblueshark.com",
    "BD": "https://clientbp.ggpolarbear.com",
    "PK": "https://clientbp.ggblueshark.com",
    "SG": "https://clientbp.ggblueshark.com",
    "SAC": "https://client.us.freefiremobile.com",
    "TW": "https://clientbp.ggblueshark.com"
}

# ========== BANNER ==========
BANNER = """
\033[1;97m
███╗░░██╗ ░█████╗░
████╗░██║ ██╔═══╝░
██╔██╗██║ ██████╗░
██║╚████║ ██╔══██╗
██║░╚███║ ╚█████╔╝
╚═╝░░╚══╝ ░╚════╝░
\033[0m
"""

# ========== ENCRYPTION FUNCTIONS ==========
def aes_enc(data):
    if isinstance(data, str): 
        data = data.encode()
    return AES.new(AeSkEy, AES.MODE_CBC, AeSiV).encrypt(pad(data, 16))

def aes_dec(data):
    try: 
        return unpad(AES.new(AeSkEy, AES.MODE_CBC, AeSiV).decrypt(data), 16)
    except: 
        return data

def write_varint(val):
    res = b''
    val = int(val)
    while True:
        byte = val & 0x7F
        val >>= 7
        if val:
            res += bytes([byte | 0x80])
        else:
            res += bytes([byte])
            break
    return res

# ========== BUILD MAJOR PROTO ==========
def build_major_pro(oid, tok, uid, plat):
    p = b''
    ts = b"2025-05-29 13:11:47"
    p += b'\x1a' + write_varint(len(ts)) + ts
    p += b'\x22\x09\x66\x72\x65\x65\x20\x66\x69\x72\x65'
    v = b"1.123.2"
    p += b'2' + write_varint(len(v)) + v
    u_b = str(uid).encode()
    p += b'\x9a\x01' + write_varint(len(u_b)) + u_b
    o_b = str(oid).encode()
    p += b'\xb2\x01' + write_varint(len(o_b)) + o_b
    pl_s = str(plat).encode()
    p += b'\xba\x01' + write_varint(len(pl_s)) + pl_s
    t_b = str(tok).encode()
    p += b'\xea\x01' + write_varint(len(t_b)) + t_b
    p += b'\xb0\x04\x04'
    chk = b"e89b158e4bcf988ebd09eb83f5378e87"
    p += b'\xc2\x03' + write_varint(len(chk)) + chk
    p += b'\x9a\x06' + write_varint(len(pl_s)) + pl_s
    p += b'\xa2\x06' + write_varint(len(pl_s)) + pl_s
    return p

# ========== ENCODE SHORT MAP CODE TO LONG ==========
def decode_short_code(short_code):
    """
    Converts short map codes (e.g., "ABC123") to full long format
    that the old system accepts.
    Example: "ABC123" -> "FREEFIRE#ABC123#FREEFIRE"
    """
    if not short_code:
        return ""
    
    # Remove any #FREEFIRE prefix/suffix if present
    clean = re.sub(r'^#?FREEFIRE#?', '', short_code.strip())
    clean = re.sub(r'#?FREEFIRE$', '', clean)
    
    # If it's already long format (contains #), return as-is
    if '#' in clean or len(clean) > 15:
        return clean
    
    # Convert short to long format
    # Format: FREEFIRE#CODE#FREEFIRE (old system format)
    return f"FREEFIRE#{clean}#FREEFIRE"

# ========== ENCODE TELEGRAM CHANNEL IN CODE ==========
def encode_channel(channel_name):
    """
    Encodes the Telegram channel name into base64 + XOR
    to hide it inside the code.
    """
    # XOR with owner name
    key = OWNER.encode()
    channel_bytes = channel_name.encode()
    xor_bytes = bytes([b ^ key[i % len(key)] for i, b in enumerate(channel_bytes)])
    return base64.b64encode(xor_bytes).decode()

# ========== DECODE TELEGRAM CHANNEL ==========
def decode_channel(encoded):
    """
    Decodes the hidden Telegram channel.
    """
    key = OWNER.encode()
    xor_bytes = base64.b64decode(encoded)
    decoded = bytes([b ^ key[i % len(key)] for i, b in enumerate(xor_bytes)])
    return decoded.decode()

# ========== RUN TASK WITH SHORT CODE SUPPORT ==========
def run_task(uid, pas, server_key, mode, map_code):
    print(f"\n\033[1;97m[▶] PROCESSING: {uid}\033[0m")
    
    # Convert short code to long if needed
    long_code = decode_short_code(map_code)
    print(f"\033[1;90m[ℹ] MAP CODE: {map_code} -> {long_code}\033[0m")
    
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; V2026 Build/SP1A.210812.003)",
        "X-GA": "v1 1",
        "Releaseversion": OB_VERSION,
        "Content-Type": "application/octet-stream",
        "Expect": "100-continue"
    }

    # ----- GRANT TOKEN -----
    try:
        g_url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
        g_dat = {
            "uid": uid, 
            "password": pas, 
            "response_type": "token", 
            "client_id": "100067", 
            "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3", 
            "client_type": "2"
        }
        r_grant = requests.post(g_url, data=g_dat, timeout=10)
        grant_json = r_grant.json()
        acc, oid = grant_json["access_token"], grant_json["open_id"]
        plat = grant_json.get("platform", 4)
    except Exception:
        return False

    # ----- MAJOR LOGIN -----
    try:
        major_url = "https://loginbp.ggpolarbear.com/MajorLogin"
        raw_pb = build_major_pro(oid, acc, uid, plat)
        r_login = requests.post(major_url, data=aes_enc(raw_pb), headers=headers, timeout=15)
        
        dec = aes_dec(r_login.content)
        pb_data, _ = blackboxprotobuf.decode_message(dec)
        
        jwt = pb_data.get('8')
        if isinstance(jwt, bytes): 
            jwt = jwt.decode(errors='ignore')
        
        dynamic_url = pb_data.get('10')
        if isinstance(dynamic_url, bytes): 
            dynamic_url = dynamic_url.decode(errors='ignore')

        if not jwt:
            return False
            
        target_base = str(dynamic_url).strip("/") if dynamic_url else REGION_URLS.get(server_key, "https://clientbp.ggpolarbear.com")
            
    except Exception:
        return False

    # ----- SEND REQUEST (USING LONG CODE) -----
    try:
        lang = REGION_LANG.get(server_key, "en")
        endpoint = "SubscribeWorkshopCode" if mode == "1" else "SendWorkshopLike"
        url = f"{target_base}/{endpoint}"
        
        m_b = long_code.encode()  # <--- USE LONG CODE HERE
        l_b = lang.encode()
        
        if mode == "1":
            game_pb = b'\x08\x01\x12' + write_varint(len(m_b)) + m_b + b'\x22' + write_varint(len(l_b)) + l_b
        else:
            game_pb = b'\x0a' + write_varint(len(m_b)) + m_b + b'\x12\x01\x14\x18\x06'
            
        h_game = headers.copy()
        h_game["Authorization"] = f"Bearer {jwt}"
        
        encrypted_body = aes_enc(game_pb)
        r_game = requests.post(url, data=encrypted_body, headers=h_game, timeout=10)
        
        return r_game.status_code == 200
    except Exception:
        return False

# ========== HIDDEN CHANNEL (ENCODED) ==========
HIDDEN_CHANNEL = encode_channel("@O000000000000o_X_o000000000000O")

# ========== MAIN ==========
def main():
    os.system('clear')
    print(BANNER)
    
    # Show hidden channel (decoded at runtime)
    print(f"\033[1;90m[ℹ] CHANNEL: {decode_channel(HIDDEN_CHANNEL)}\033[0m")
    
    choice = input("\n\033[1;36m[1] SUBSCRIBE  [2] COMMENT > \033[0m").strip()
    map_code = input("\033[1;36mENTER MAP CODE (short or long) > \033[0m").strip()
    json_path = input("\033[1;36mJSON FILE PATH > \033[0m").strip()
    
    # Display servers
    print("\n\033[1;93m╔════════════════════════════════════╗")
    print("║        AVAILABLE SERVERS           ║")
    print("╚════════════════════════════════════╝\033[0m")
    
    keys = list(REGION_URLS.keys())
    for i, k in enumerate(keys, 1):
        print(f" \033[1;90m[{i:02d}]\033[0m \033[1;97m{k}\033[0m")
    
    srv_idx = int(input("\n\033[1;36mSELECT SERVER [1-{}] > \033[0m".format(len(keys))))
    selected_server = keys[srv_idx-1]
    
    # Load JSON
    try:
        with open(json_path, 'r') as f:
            raw = json.load(f)
            accounts = []
            if isinstance(raw, list):
                for i in raw:
                    u, p = i.get('uid'), i.get('password') or i.get('pass')
                    if u and p:
                        accounts.append({'u': u, 'p': p})
            else:
                for k, v in raw.items():
                    accounts.append({'u': k, 'p': v})
    except Exception as e:
        print(f"\033[1;31m ERROR: Failed to load JSON file\033[0m")
        return
    
    if not accounts:
        print(f"\033[1;31m ERROR: No valid accounts found\033[0m")
        return
    
    print(f"\n\033[1;93m═══════════════════════════════════════════")
    print(f" TARGET: {selected_server} | MODE: {'SUBSCRIBE' if choice == '1' else 'COMMENT'}")
    print(f" MAP CODE: {map_code} (converted internally)")
    print(f" TOTAL ACCOUNTS: {len(accounts)}")
    print(f"═══════════════════════════════════════════\033[0m")
    
    success_count = 0
    fail_count = 0
    
    for idx, acc in enumerate(accounts, 1):
        print(f"\n\033[1;90m[{idx}/{len(accounts)}]\033[0m", end=" ")
        
        if run_task(acc['u'], acc['p'], selected_server, choice, map_code):
            print(f"\033[1;32m SUCCESS | {acc['u']}\033[0m")
            success_count += 1
        else:
            print(f"\033[1;31m FAILED  | {acc['u']}\033[0m")
            fail_count += 1
        
        time.sleep(0.5)
    
    print(f"\n\033[1;93m═══════════════════════════════════════════")
    print(f" SUMMARY")
    print(f"═══════════════════════════════════════════")
    print(f" \033[1;32m SUCCESS: {success_count}\033[0m")
    print(f" \033[1;31m FAILED:  {fail_count}\033[0m")
    print(f" \033[1;36m► TOTAL:   {len(accounts)}\033[0m")
    print(f"═══════════════════════════════════════════\033[0m")

if __name__ == "__main__":
    main()