# test_radmin_ip.py
import subprocess
import re
import sys

def get_radmin_ip():
    """Kiểm tra xem ipconfig có tìm thấy Radmin IP không."""
    try:
        # Chạy lệnh ipconfig
        output = subprocess.check_output("ipconfig", shell=True, encoding="utf8")
        
        # Logic tìm kiếm
        sections = output.split("\n\n")

        for sec in sections:
            if "Radmin" in sec or "Radmin VPN" in sec:
                match = re.search(r"IPv4 Address[^\:]*: ([0-9\.]+)", sec)
                if match:
                    return match.group(1).strip()
    except Exception as e:
        return f"ERROR: {e}"
    return "IP NOT FOUND IN IPCONFIG" # Nếu không tìm thấy trong log

if __name__ == "__main__":
    print("--- Radmin IP Test ---")
    print("STATUS: ")
    print(get_radmin_ip())
    print("----------------------")