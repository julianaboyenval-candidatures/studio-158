#!/usr/bin/env python3
"""Accès du robot au planning Studio 158 (Supabase). Bibliothèque standard uniquement.

Identifiants lus dans l'environnement : STUDIO_BOT_EMAIL, STUDIO_BOT_PASSWORD (jamais affichés).

Commandes :
  studio.py dump                       → JSON {posts:{id:data}, ideas:{...}, meta:{...}} sur la sortie
  studio.py get <col> <id>             → le document
  studio.py put <col> <id> <fichier.json>   → crée ou remplace le document
  studio.py upload <photo.jpg> <nom.jpg>    → dépose dans le bucket public, affiche l'URL publique
  studio.py check                      → vérifie la connexion (affiche « ok »)
"""
import json, os, sys, urllib.error, urllib.request

URL = "https://vtusvowmjfkpveizkwzs.supabase.co"
# Clé publique (la même que dans config.js du site) : elle ne donne accès à rien sans connexion.
BUCKET = "studio158"
SITE = "https://raw.githubusercontent.com/julianaboyenval-candidatures/studio-158/main/"


def public_key():
    if os.environ.get("STUDIO_SUPABASE_KEY"):
        return os.environ["STUDIO_SUPABASE_KEY"]
    import re
    js = urllib.request.urlopen(SITE + "config.js", timeout=30).read().decode()
    return re.search(r'key:\s*"([^"]+)"', js).group(1)


KEY = public_key()


def req(method, path, body=None, token=None, headers=None, raw=False):
    h = {"apikey": KEY, "Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    h.update(headers or {})
    data = body if raw else (json.dumps(body).encode() if body is not None else None)
    r = urllib.request.Request(URL + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(r, timeout=60) as res:
            txt = res.read().decode() or "null"
            return json.loads(txt) if txt.strip()[:1] in "[{n" else txt
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur Supabase {e.code} sur {method} {path.split('?')[0]} : {e.read().decode()[:300]}")


def login():
    email, pw = os.environ.get("STUDIO_BOT_EMAIL"), os.environ.get("STUDIO_BOT_PASSWORD")
    if not (email and pw):
        sys.exit("Il manque STUDIO_BOT_EMAIL ou STUDIO_BOT_PASSWORD dans l'environnement.")
    return req("POST", "/auth/v1/token?grant_type=password", {"email": email, "password": pw})["access_token"]


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, tok = argv[0], login()
    if cmd == "check":
        req("GET", "/rest/v1/studio_docs?select=col&limit=1", token=tok)
        print("ok")
    elif cmd == "dump":
        rows = req("GET", "/rest/v1/studio_docs?select=col,id,data&order=col,id&limit=5000", token=tok)
        out = {"posts": {}, "ideas": {}, "meta": {}}
        for r in rows:
            out.setdefault(r["col"], {})[r["id"]] = r["data"]
        print(json.dumps(out, ensure_ascii=False, indent=1))
    elif cmd == "get":
        rows = req("GET", f"/rest/v1/studio_docs?select=data&col=eq.{argv[1]}&id=eq.{argv[2]}", token=tok)
        print(json.dumps(rows[0]["data"] if rows else None, ensure_ascii=False, indent=1))
    elif cmd == "put":
        data = json.load(open(argv[3], encoding="utf8"))
        req("POST", "/rest/v1/studio_docs?on_conflict=col,id", {"col": argv[1], "id": argv[2], "data": data},
            token=tok, headers={"Prefer": "resolution=merge-duplicates,return=minimal"})
        print("ok", argv[1], argv[2])
    elif cmd == "upload":
        blob = open(argv[1], "rb").read()
        req("POST", f"/storage/v1/object/{BUCKET}/{argv[2]}", blob, token=tok, raw=True,
            headers={"Content-Type": "image/jpeg", "x-upsert": "true", "Cache-Control": "max-age=31536000"})
        print(f"{URL}/storage/v1/object/public/{BUCKET}/{argv[2]}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
