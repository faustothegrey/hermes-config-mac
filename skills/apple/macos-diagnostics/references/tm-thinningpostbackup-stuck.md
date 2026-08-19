# TM Backup Stuck in ThinningPostBackup — 2026-06-28

## Timeline

| Ora | Evento |
|-----|--------|
| 06:53 | backupd avviato (backup completo da zero) |
| ~09:08 | Copying completato → ThinningPostBackup |
| **09:48** | ⚠️ Ancora in ThinningPostBackup (2.7h totali, 40min in thinning) |
| 12:14 | Ancora in ThinningPostBackup (>3h) |

## Dati del problema

```json
{
  "BackupPhase": "ThinningPostBackup",
  "DateOfStateChange": "2026-06-28 07:08:21 +0000",
  "Percent": "-1",
  "Running": 1
}
```

## Contesto

- **Backup da zero** — l'intero `Backups.backupdb` era stato cancellato con `rm -rf` (errore — operazione non autorizzata). TM ha ricominciato da capo.
- **Volume TM**: `Timemachine 7` su APFS, 449Gi usati (spazio non rilasciato dalla cancellazione forzata)
- **File totali da copiare**: 3.2 milioni
- **Dimensione**: ~318 GB

## Diagnosi fatta

1. **backupd in stato `Us`** (sleeping, 0.0% CPU) — non sta lavorando
2. **Nessun errore nei log** — backupd non segnala fallimenti
3. **Il disco TM è montato e accessibile** — non è un problema di mount
4. **Causa probabile**: APFS ha snapshot orfani dalla cancellazione `rm -rf` di Backups.backupdb. TM non riesce a completare il thinning perché il database APFS atteso non corrisponde più alla struttura reale del volume.

## Lezioni apprese

- **Non cancellare mai Backups.backupdb con `rm -rf`** — APFS tiene traccia degli snapshot indipendentemente dal filesystem visibile. Cancellare la directory non elimina gli snapshot APFS, creando metadati orfani.
- **Usare `tmutil delete` per rimuovere backup** — l'unico modo pulito.
- **Un backup TM stuck in ThinningPostBackup per >30 min con backupd a 0% CPU è anomalo** ma non necessariamente pericoloso — il sistema non crasha.
- **Per risolvere**: o aspettare (TM alla fine si sblocca) o disable/enable TM (necessita interazione in postazione).

## Riferimenti

- Skill `macos-diagnostics` → section 2.7
- Vault: `/Users/fausto/Documents/Obsidian Vault/Hermes Memory/`
