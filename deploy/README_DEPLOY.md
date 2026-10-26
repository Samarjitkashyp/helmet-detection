# Helmet backend ko AWS Lightsail par chalana

Is guide ke baad aapka backend ek Ubuntu server par chalega: **nginx (HTTPS) → FastAPI (systemd) → PostgreSQL**.
Admin panel `https://aapka-domain/panel` par milega, aur Flutter app usi domain se baat karegi.

## 0. Pehle yeh chahiye

| Cheez | Kyun |
|---|---|
| **Domain name** (jaise `helmet.example.com`) | HTTPS certificate (Let's Encrypt) sirf domain ko milta hai, IP ko nahi. Domain ke bina Android app release mein chalegi nahi (HTTP release app mein band hai). |
| **Lightsail instance: Ubuntu 24.04 (ya 22.04), kam se kam 4 GB RAM** | PyTorch + YOLO ko memory chahiye. 1-2 GB wale plan par crash ya swap mein atakna hoga. |
| Lightsail **static IP** | Restart ke baad IP na badle. |

> **Speed ka sach:** Lightsail par GPU nahi hota. 2 vCPU par 1 minute ki video ko kuch minute lagenge (aapke PC jaisa ya thoda slow). Tez chahiye toh bada plan lein, ya admin panel Settings mein "Check every Nth frame" badhayein (jaise 3).

## 1. Lightsail mein setup (console mein)

1. Instance banayein (Linux/Unix → OS Only → Ubuntu).
2. **Networking → Create static IP** karke instance se attach karein.
3. **Networking → IPv4 Firewall** mein sirf yeh rules rakhein: **SSH 22, HTTP 80, HTTPS 443**. Port 8000 mat kholiye (nginx uske aage khada hai).
4. Apne domain ke DNS mein **A record** banayein: `helmet.example.com → static IP`. (Phailne mein kuch minute lag sakte hain.)
5. SSH key (`.pem`) download karke rakhein, aage `scp` ke liye chahiye.

## 2. Windows par bundle banayein

PowerShell mein:

```powershell
cd E:\helmet_detection
.\deploy\make_bundle.ps1
```

`E:\helmet_detection\helmet_bundle.zip` banega (backend + model + scripts). `.env` aur `storage` jaan-boojhkar shamil nahi hote.

## 3. Server par bhejein

```powershell
scp -i C:\path\to\LightsailKey.pem E:\helmet_detection\helmet_bundle.zip ubuntu@STATIC_IP:~
ssh -i C:\path\to\LightsailKey.pem ubuntu@STATIC_IP
```

## 4. Server par setup chalayein

Server ke andar (SSH mein):

```bash
sudo apt-get install -y unzip
unzip -o helmet_bundle.zip -d helmet_bundle
sudo bash helmet_bundle/deploy/setup_server.sh helmet.example.com
```

(`helmet.example.com` ki jagah apna domain.) Script 10-15 minute lega, kyunki PyTorch install hota hai. Woh khud:
- nginx, PostgreSQL, Python environment lagata hai
- database aur **random password / SECRET_KEY** banakar `/opt/helmet/backend/.env` mein rakhta hai (chat ya screen par nahi dikhte)
- backend ko systemd service (`helmet`) banata hai, jo restart par apne aap chalti hai
- roz raat 3 baje database ka backup (7 din ke) lagata hai

## 5. HTTPS certificate

```bash
sudo certbot --nginx -d helmet.example.com --redirect
```

Yeh email aur Let's Encrypt ki terms poochhega (terms aap khud accept karte hain). Certificate apne aap renew hota rahega.

## 6. Admin banayein

```bash
sudo -u helmet bash -c 'cd /opt/helmet/backend && /opt/helmet/venv/bin/python -I scripts/create_admin.py'
```

## 7. Check karein

- Browser: `https://helmet.example.com/health` → `{"status":"ok"}`
- `https://helmet.example.com/panel` → admin login
- Production mein `/docs` band hai (jaan-boojhkar).

## 8. Flutter app ko server se jodna

App ka **release APK** banayein, server address andar daalkar:

```powershell
cd "E:\Flutter Projects\helmet_detection_app"
flutter build apk --release --dart-define=API_URL=https://helmet.example.com
```

APK: `build\app\outputs\flutter-apk\app-release.apk`. Use phone mein install karein. Release app **sirf HTTPS** se baat karti hai (HTTP debug build mein hi chalta hai).

## 9. Naya code ya naya model bhejna

Windows par `make_bundle.ps1` dobara chalayein, `scp` karein, phir server par:

```bash
rm -rf helmet_bundle && unzip -o helmet_bundle.zip -d helmet_bundle
sudo bash helmet_bundle/deploy/update.sh
```

`.env`, database aur photos waise hi rehte hain.

## 10. Suraksha checklist

- [ ] `/opt/helmet/backend/.env` ka permission 600 hai (script khud lagata hai).
- [ ] Admin panel sirf apne IP se kholna ho: `.env` mein `ADMIN_ALLOWED_IPS=aapka.ip` likhkar `sudo systemctl restart helmet`. (Baaki sab ko `/panel` aur `/admin` par 404 milega. App ki API par asar nahi.)
- [ ] Login par galat password 8 baar ke baad 5 minute ke liye rok diya jata hai.
- [ ] Lightsail firewall mein sirf 22/80/443.
- [ ] Lightsail **snapshot** (Snapshots tab) hafte mein ek baar lein: yeh photos (storage) bhi bachata hai. Database ka backup `/var/backups/helmet/` mein roz banta hai.
- [ ] **Privacy:** videos mein logon ke chehre hote hain. Disk bachane aur jokhim kam karne ke liye `.env` mein `KEEP_ORIGINAL_VIDEOS=false` rakh sakte hain: analysis ke baad asli video hat jati hai, sirf proof-photos bachti hain.
- [ ] SSH ke liye password login band rakhein (Lightsail mein default key-only hota hai).

## Dikkat aaye toh

| Dikkat | Kya dekhein |
|---|---|
| Backend nahi chal raha | `sudo journalctl -u helmet -n 80 --no-pager` |
| 502 Bad Gateway | `sudo systemctl status helmet` (service chal rahi hai?) |
| Upload 413 error | nginx `client_max_body_size` (320m set hai) |
| Video "failed: Server restarted" | Processing ke beech service restart hui; video dobara upload karein |
| Disk bhar gayi | `df -h`, `du -sh /opt/helmet/backend/storage/*`; `KEEP_ORIGINAL_VIDEOS=false` karein |
| Certbot fail | DNS A record abhi tak phaila nahi, ya port 80 firewall mein band hai |

## Ek zaroori baat (database badlav)

Abhi tables `create_all` se banti hain, jo **naye column** nahi jodta. Aage agar tables badalni padein, toh Alembic migration chahiye hogi. Bataiye, tab main migrations set kar dunga.

## CCTV monitoring (worker on a PC, alerts to Telegram and the app)

- **Server**: `.env` mein `CCTV_WORKER_KEY` (lamba random string), `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` jodein. Admin panel > Cameras mein camera add karein.
- **PC (camera ke paas)**: `backend/.env` mein wahi `CCTV_WORKER_KEY` aur `CCTV_SERVER_URL=https://<aapka-server>`. Phir `deploy/pc/install_autostart.ps1 -CameraId 1` (har login par apne aap chalta hai).
- **Server ke alerts app mein**: admin account se login karein, "Alerts" tab dikhega (har 20 second mein naye alert check hote hain).
- Table `push_devices` aur `cctv_events`/`cameras` pehli restart par `create_all` se ban jaati hain.

### Phone par asli push (optional, Firebase chahiye)

Bina iske app khula ho tab alerts aate hain aur Telegram hamesha chalta hai. App band ho tab bhi notification ke liye:
1. https://console.firebase.google.com par ek project banayein, usme Android app jodein (package name: `android/app/build.gradle.kts` ka `applicationId`).
2. `google-services.json` download karein (app ke liye) aur **Project settings > Service accounts > Generate new private key** se ek JSON (server ke liye).
3. Server par JSON ko `/opt/helmet/fcm-service-account.json` mein rakhein (`chmod 600`, owner `helmet`), `.env` mein `FCM_PROJECT_ID=<project id>` aur `FCM_SERVICE_ACCOUNT_FILE=/opt/helmet/fcm-service-account.json`, phir `sudo systemctl restart helmet`.
4. App mein Firebase (`firebase_core`, `firebase_messaging`) jodna baaki hai: server taiyar hai (`POST /cctv/devices` token leta hai, `services/push.py` bhejta hai). `google-services.json` milne par ye app-side kaam kiya ja sakta hai.
