# Incidente: Mac surriscaldato — backup git gonfiato a 13GB (2026-08-19)

> Nota scritta per Fausto, da leggere con calma un altro giorno. Racconta cosa è
> successo, perché, e come è stato risolto. Nessuna azione richiesta: il problema
> è già risolto. Related: [[Hermes Environment and Infrastructure Reference]].

## In una frase

Il Mac scaldava e girava a load 23 (ventole al massimo) perché il backup notturno
di configurazione aveva gonfiato la cartella `.git` a **13 GB**, e un processo
`git pack-objects` la stava ricomprimendo al **481% di CPU per 22 minuti**. La
vault (che sospettavamo) non c'entrava nulla (pesa 508 KB). Risolto: kill del
processo, secrets tolti da git, storia git azzerata (13GB → 161MB), script del
backup reso leggero. Backup ora gira in **15 secondi**.

---

## Come è iniziato

Fausto: «ma perché questo Mac si riscalda tanto?»

Diagnosi con `ps` + `sysctl vm.loadavg`:

| Processo | %CPU | Note |
|----------|------|------|
| **git-core/git** | **481%** | ~5 core su 8 saturati da un solo processo |
| Python 3.10 | 78% | |
| Telegram | 48% | |
| hermes-agent | 45% | normale |

- **Load average: 23.33** su 8 core (soglia critica ~18 → sistema completamente saturo).
- Termico: nessun warning *ancora* registrato, ma con load 23 sostenuto era imminente.

## Cos'era quel git

```
git pack-objects --all --thin --delta-base-offset
  ├── girava da 22 minuti
  ├── cwd = ~/Backups/hermes-config     (il repo di backup config)
  └── PPID = 843 = hermes gateway       (lo lancia il backup notturno)
```

Era il **backup notturno di configurazione** che faceva `git push` verso
`github.com:faustothegrey/hermes-config-mac.git`. Il `pack-objects` è la fase in
cui git comprime gli oggetti prima di spedirli.

## La causa radice (il punto importante)

Ipotesi iniziale «è la vault troppo grossa» → **SBAGLIATA**. I numeri reali:

```
obsidian-vault/  → 508K     ← minuscola, irrilevante
skills/          → 72M
secrets/         → 163M      ← bundle cifrato
.git/            → 13 GB     ← IL VERO MOSTRO
```

Perché `.git` era esploso a 13 GB? Lo script `backup-hermes.sh` (righe 34-35)
ogni notte faceva:

```bash
openssl rand 32 > aes.key          # chiave AES NUOVA e casuale ogni notte
openssl enc -aes-256-cbc ...        # cifra i secrets → file da 162MB SEMPRE DIVERSO
git add . && git commit && push     # git lo vede come file nuovo → lo aggiunge alla storia
```

Il bundle secrets conteneva soprattutto **`state.db`** (il DB delle conversazioni,
**525 MB**), che compresso faceva 162 MB. Ma siccome la **chiave AES era casuale
ogni notte**, il file cifrato risultante era **completamente diverso ad ogni
backup**, anche a secret invariati. git non poteva calcolare il "delta" → lo
trattava come 162 MB di roba nuova da aggiungere alla storia, ogni notte.

**162 MB × ~80 notti ≈ 13 GB di `.git`.** E ogni push/gc doveva ricomprimere
tutto quel malloppo → il pack-objects che frigge la CPU.

## La soluzione (eseguita passo-passo, con OK di Fausto ad ogni passo)

Decisione di Fausto: **secrets solo LOCALI** (non servono off-site su GitHub).

1. **Kill del git pack** (`kill 2585`, solo quello — gateway PID 843 intatto)
   → load **23.33 → 6.49** in pochi secondi.
2. **`secrets/` in `.gitignore`** (prima c'era un `!secrets/*.enc` che li FORZAVA
   dentro). Ora i file secrets restano su disco per il restore, ma non entrano
   più nei commit.
3. **`git rm -r --cached secrets/`** → scollegati dal tracking (file locali salvi).
4. **Storia git fresca**: `git checkout --orphan` + commit radice pulito +
   `git gc --prune=now --aggressive` → **13 GB → 160 MB** (recuperati ~12.8 GB).
5. **`git push --force`** → GitHub allineato alla storia pulita.
6. **Patch dello script** `backup-hermes.sh`: la generazione del bundle secrets
   (che re-cifrava 525MB ogni notte = spreco CPU anche senza push) ora è SALTATA
   di default. Si riattiva solo con `BACKUP_SECRETS=1`.
7. **Prova a secco** del backup completo → **15 secondi** (era 22+ minuti di CPU).

## Stato finale (verificato)

| Metrica | Prima | Dopo |
|---------|-------|------|
| Load 1-min | 23.33 | ~3.0 |
| git pack-objects | 481% CPU, 22 min | assente |
| `.git` size | 13 GB | 161 MB |
| Secrets tracciati in git | sì (162MB/notte) | 0 |
| Durata backup notturno | 22+ min (frigge CPU) | ~15 s |

## Se un giorno servisse rimettere i secrets off-site

Lanciare il backup con `BACKUP_SECRETS=1`. MA attenzione: si ri-gonfia `.git`
per lo stesso motivo (chiave random ogni notte). Soluzione migliore da valutare
allora: cifratura DETERMINISTICA (stessa chiave finché i secret non cambiano),
oppure snapshot dei secrets separato dal repo git di config.

## File toccati

- `~/Backups/hermes-config/.gitignore` — `secrets/` ora ignorato
- `~/Backups/hermes-config/scripts/backup-hermes.sh` — switch `BACKUP_SECRETS`
- Storia git del repo riscritta (force-push su GitHub)
- Nessun dato perso: i secrets sono ancora in `~/Backups/hermes-config/secrets/`
  in locale; `state.db` originale intatto in `~/.hermes/state.db`

## Nota a margine

Durante l'intervento, il loop autonomo di Rebar Phase 1 ha continuato a lavorare
per conto suo (ha prodotto lo step G2/timeout), del tutto estraneo al problema
termico. Vedi [[Rebar Phase 1 Autonomous Review Loop Runbook]].
