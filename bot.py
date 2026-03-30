import requests, json, os, time, random
from datetime import datetime, timedelta

# ---------- CONFIG ----------
BOT_TOKEN = "8718413635:AAG_15ZwTQmm1fRqAiHf8KFdvT19HsGmB08"
GROQ_API_KEY = "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"

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# ---------- FILES ----------
FILES = {
    "memory":"memory.json",
    "econ":"econ.json",
    "xp":"xp.json",
    "daily":"daily.json",
    "bank":"bank.json",
    "stats":"stats.json",
    "protect":"protect.json",
    "marry":"marry.json"
}

MAX_MEMORY = 6

# ---------- UTILS ----------
def load(f):
    if not os.path.exists(f): return {}
    try: return json.load(open(f))
    except: return {}

def save(f,d): json.dump(d,open(f,"w"))

# ---------- TELEGRAM ----------
def send(chat,text):
    requests.post(BASE_URL+"sendMessage",json={"chat_id":chat,"text":text})

def updates(off=None):
    try:
        return requests.get(BASE_URL+"getUpdates",params={"timeout":100,"offset":off}).json()
    except:
        return {"result":[]}

# ---------- CORE SYSTEM ----------
def bal(u):
    d=load(FILES["econ"])
    if u not in d: d[u]={"coins":0}
    save(FILES["econ"],d)
    return d[u]["coins"]

def add_bal(u,a):
    d=load(FILES["econ"])
    if u not in d: d[u]={"coins":0}
    d[u]["coins"]+=a
    save(FILES["econ"],d)

def xp(u,a=0):
    d=load(FILES["xp"])
    if a: d[u]=d.get(u,0)+a; save(FILES["xp"],d)
    return d.get(u,0)

def lvl(u): return xp(u)//1000

def stats(u):
    d=load(FILES["stats"])
    if u not in d: d[u]={"kills":0,"status":"alive"}
    save(FILES["stats"],d)
    return d[u]

def set_status(u,s):
    d=load(FILES["stats"])
    d[u]=d.get(u,{"kills":0})
    d[u]["status"]=s
    save(FILES["stats"],d)

def add_kill(u):
    d=load(FILES["stats"])
    d[u]=d.get(u,{"kills":0,"status":"alive"})
    d[u]["kills"]+=1
    save(FILES["stats"],d)

def rank(u):
    d=load(FILES["econ"])
    s=sorted(d.items(),key=lambda x:x[1]["coins"],reverse=True)
    for i,(x,_) in enumerate(s,1):
        if x==u: return i
    return "-"

# ---------- DAILY ----------
def daily(u):
    d=load(FILES["daily"])
    if u in d:
        if datetime.now()-datetime.fromisoformat(d[u])<timedelta(hours=24):
            return False,0
    streak=d.get(u+"_streak",0)+1
    d[u+"_streak"]=streak
    d[u]=datetime.now().isoformat()
    save(FILES["daily"],d)
    return True,1000+streak*100

# ---------- BANK ----------
def bank(u,a=0):
    d=load(FILES["bank"])
    if a!=0:
        d[u]=d.get(u,0)+a
        save(FILES["bank"],d)
    return d.get(u,0)

# ---------- PROTECT ----------
def protect(u,h=0):
    d=load(FILES["protect"])
    if h:
        d[u]=(datetime.now()+timedelta(hours=h)).isoformat()
        save(FILES["protect"],d)
    return u in d and datetime.now()<datetime.fromisoformat(d[u])

# ---------- MARRY ----------
def marry(u,v=None):
    d=load(FILES["marry"])
    if v:
        d[u]=v; d[v]=u; save(FILES["marry"],d)
    return d.get(u)

# ---------- AI ----------
def ai(cid,msg):
    mem=load(FILES["memory"])
    hist=mem.get(cid,[])
    if not isinstance(hist,list): hist=[]
    msgs=[{"role":"system","content":"Cute Hinglish Sakura girl"}]+hist+[{"role":"user","content":msg}]
    try:
        r=requests.post(GROQ_URL,
            headers={"Authorization":"Bearer "+GROQ_API_KEY},
            json={"model":"openai/gpt-oss-20b","messages":msgs})
        out=r.json()["choices"][0]["message"]["content"]
    except:
        out="error 😅"
    hist+= [{"role":"user","content":msg},{"role":"assistant","content":out}]
    mem[cid]=hist[-MAX_MEMORY:]
    save(FILES["memory"],mem)
    return out

# ---------- LOOP ----------
off=None
while True:
    for u in updates(off).get("result",[]):
        off=u["update_id"]+1
        m=u.get("message",{})
        cid=str(m.get("chat",{}).get("id"))
        txt=m.get("text","")
        user=m.get("from",{}).get("username","user")

        reply=None
        if "reply_to_message" in m:
            reply=m["reply_to_message"]["from"].get("username")

        if txt.startswith("/"):
            cmd=txt.split()[0].lower()
            args=txt.split()[1:]

            st=stats(user)
            if st["status"]=="dead" and cmd not in ["/revive","/bal"]:
                send(cid,"💀 You are dead! Use /revive")
                continue

            # HELP
            if cmd=="/help":
                send(cid,"🔥 Sakura Legendary Bot\nUse /bal /daily /rob /kill /shop /bank /profile")
            
            # BAL
            elif cmd=="/bal":
                send(cid,f"""╔═══『 👤 PROFILE 』═══╗
👤 {user}
💰 ${bal(user)}   🏦 {bank(user)}
🏆 Rank: #{rank(user)}

❤️ {st['status']}   ⚔️ {st['kills']}
⭐ Lv {lvl(user)}   XP {xp(user)}
💍 {marry(user) or 'Single'}
╚══════════════════╝""")

            # DAILY
            elif cmd=="/daily":
                ok,amt=daily(user)
                send(cid,f"🎁 +${amt}" if ok else "⏰ Already claimed")

            # ROB
            elif cmd=="/rob" and reply:
                if "bot" in reply.lower(): send(cid,"🤖 no bots"); continue
                if protect(reply): send(cid,"🛡️ protected"); continue
                steal=min(10000,bal(reply))
                if steal<=0: send(cid,"no money"); continue
                steal=random.randint(1,steal)
                add_bal(user,steal); add_bal(reply,-steal)
                send(cid,f"💸 stole ${steal}")

            # KILL
            elif cmd=="/kill" and reply:
                if "bot" in reply.lower(): send(cid,"🤖 no bots"); continue
                if stats(reply)["status"]=="dead": send(cid,"already dead"); continue
                add_bal(user,random.randint(100,200))
                xp(user,random.randint(1,5))
                add_kill(user); set_status(reply,"dead")
                send(cid,"💀 KILLED")

            # REVIVE
            elif cmd=="/revive":
                set_status(user,"alive")
                send(cid,"🌸 revived")

            # GAMBLE
            elif cmd=="/gamble":
                amt=int(args[0])
                if random.randint(0,1):
                    add_bal(user,amt); send(cid,"🎉 win")
                else:
                    add_bal(user,-amt); send(cid,"😢 lose")

            # BANK
            elif cmd=="/bank":
                send(cid,f"🏦 {bank(user)}")

            elif cmd=="/deposit":
                amt=int(args[0])
                add_bal(user,-amt); bank(user,amt)
                send(cid,"💰 deposited")

            elif cmd=="/withdraw":
                amt=int(args[0])
                bank(user,-amt); add_bal(user,amt)
                send(cid,"💸 withdraw")

            # SHOP
            elif cmd=="/shop":
                send(cid,"🛒 shield $5000")

            elif cmd=="/buy":
                if args and args[0]=="shield":
                    if bal(user)<5000: send(cid,"no money"); continue
                    add_bal(user,-5000)
                    protect(user,24)
                    send(cid,"🛡️ protected 24h")

            # LOOTBOX
            elif cmd=="/lootbox":
                r=random.choice([500,1000,5000,10000])
                add_bal(user,r)
                send(cid,f"🎁 ${r}")

            # DUEL
            elif cmd=="/duel" and reply:
                win=random.choice([user,reply])
                add_bal(win,500)
                send(cid,f"⚔️ {win} wins")

            # MARRY
            elif cmd=="/marry" and reply:
                marry(user,reply)
                send(cid,"💍 married")

            continue

        # AI reply (reply only)
        if "reply_to_message" in m:
            send(cid,ai(cid,txt))

    time.sleep(1)
