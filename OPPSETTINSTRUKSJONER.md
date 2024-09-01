# WALCheckMate Oppsettinstruksjoner

Dette dokumentet gir instruksjoner for oppsett av WALCheckMate, inkludert brannmurkonfigurasjon og andre nødvendige trinn.

## Forutsetninger

- En server som kjører en nyere versjon av Ubuntu (18.04 eller nyere anbefales)
- Docker og Docker Compose installert
- Et domenenavn som peker til serverens IP-adresse

## Trinn 1: Klon Repositoriet

Klon WALCheckMate-repositoriet til serveren din:

```bash
git clone https://your-repository-url.git
cd WALCheckMate
```

## Trinn 2: Konfigurer Brannmuren

1. Gjør brannmur-oppsettskriptet kjørbart:

```bash
chmod +x setup_firewall.sh
```

2. Kjør brannmur-oppsettskriptet:

```bash
sudo ./setup_firewall.sh
```

Dette skriptet vil:
- Installere ufw (Uncomplicated Firewall) hvis det ikke allerede er installert
- Sette standardregler for å nekte innkommende og tillate utgående tilkoblinger
- Tillate SSH (port 22), HTTP (port 80), HTTPS (port 443) og den tilpassede HTTPS-porten (8086)
- Aktivere brannmuren

## Trinn 3: Konfigurer Nginx og Let's Encrypt

1. Rediger `nginx.conf`-filen og erstatt `example.com` med ditt faktiske domenenavn.

2. Rediger `init-letsencrypt.sh`-skriptet:
   - Erstatt `example.com` og `www.example.com` med ditt/dine domene(r)
   - Sett en gyldig e-postadresse for Let's Encrypt-varsler

3. Gjør Let's Encrypt-initialiseringsskriptet kjørbart:

```bash
chmod +x init-letsencrypt.sh
```

4. Kjør Let's Encrypt-initialiseringsskriptet:

```bash
./init-letsencrypt.sh
```

Dette skriptet vil sette opp Let's Encrypt SSL-sertifikater for ditt domene.

## Trinn 4: Konfigurer Miljøvariabler

1. Opprett en `.env`-fil i prosjektets rotmappe:

```bash
cp .env.example .env
```

2. Rediger `.env`-filen og sett de nødvendige miljøvariablene, inkludert:
   - FACEBOOK_ACCESS_TOKEN
   - SLACK_BOT_TOKEN
   - SLACK_CHANNEL
   - Andre nødvendige variabler for ditt spesifikke oppsett

## Trinn 5: Start Applikasjonen

Start WALCheckMate-applikasjonen ved hjelp av Docker Compose:

```bash
docker-compose up -d
```

Denne kommandoen vil starte webapplikasjonen, Nginx reverse proxy og Certbot for SSL-sertifikathåndtering.

## Tilgang til Applikasjonen

Etter å ha fullført disse trinnene, skal WALCheckMate være tilgjengelig på:

`https://ditt-domene.no:8086`

## Feilsøking

- Hvis du støter på problemer med brannmuren, kan du sjekke statusen ved å bruke:
  ```bash
  sudo ufw status verbose
  ```

- For å se logger for applikasjonen, bruk:
  ```bash
  docker-compose logs
  ```

- Sørg for at DNS-innstillingene for ditt domene er riktig konfigurert til å peke på serverens IP-adresse.

## Vedlikehold

- SSL-sertifikater vil automatisk fornyes når det er nødvendig.
- Oppdater serveren og Docker-bildene regelmessig for sikkerhetsoppdateringer.
- Overvåk applikasjonsloggene for eventuelle feil eller problemer.

For ytterligere hjelp eller spørsmål, vennligst kontakt WALCheckMate-supportteamet.