#!/usr/bin/env python3
import os
import csv
import hmac
import hashlib
import argparse
from urllib.parse import urlencode

def sign_pid(secret: bytes, pid: str) -> str:
    return hmac.new(secret, pid.encode("utf-8"), hashlib.sha256).hexdigest()

def main():
    p = argparse.ArgumentParser(description="Generate signed participant links (CSV output).")
    p.add_argument("--n", type=int, default=100, help="Number of participants (default: 100)")
    p.add_argument("--prefix", type=str, default="P", help="ID prefix (default: P)")
    p.add_argument("--digits", type=int, default=3, help="Zero-padding digits (default: 3 -> P001)")
    p.add_argument("--base", type=str, default="http://localhost:1337/", help="Base URL (default: http://localhost:1337/)")
    p.add_argument("--out", type=str, default="", help="Output CSV file (default: stdout)")
    args = p.parse_args()

    secret_str = os.environ.get("LAB_SECRET", "SUPER_SECRET")
    if not secret_str:
        raise SystemExit("ERROR: LAB_SECRET env var is not set. Example: export LAB_SECRET='long-random-secret'")

    secret = secret_str.encode("utf-8")
    base = args.base.rstrip("/") + "/"

    rows = []
    for i in range(1, args.n + 1):
        pid = f"{args.prefix}{i:0{args.digits}d}"
        sig = sign_pid(secret, pid)
        qs = urlencode({"pid": pid, "sig": sig})
        link = f"{base}?{qs}"
        rows.append([pid, sig, link])

    # Write CSV
    if args.out:
        f = open(args.out, "w", newline="", encoding="utf-8")
    else:
        f = None

    out_fh = f if f else os.sys.stdout
    writer = csv.writer(out_fh)
    writer.writerow(["pid", "sig", "link"])
    writer.writerows(rows)

    if f:
        f.close()
        print(f"Wrote {args.n} rows to {args.out}")

if __name__ == "__main__":
    main()
