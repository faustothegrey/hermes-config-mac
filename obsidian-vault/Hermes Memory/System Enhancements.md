# System Enhancements

Enhancement candidate per Hermes Agent, da valutare a breve.

---

## 1. Espandere memoria built-in (memory_char_limit)

**Stato:** Da valutare  
**Priorità:** Media  
**Data:** 2026-06-19

**Proposta:** Alzare `memory_char_limit` (hot memory) da 2200 a ~3000 caratteri, e potenzialmente `user_char_limit` da 1375 a ~1800.

**Rischio:** Ogni carattere in più si traduce in token aggiuntivi iniettati nel system prompt di ogni sessione. Con warm memory (Holographic) attivo come recall on-demand, la hot memory può essere più generosa perché i fatti meno importanti vengono gestiti da Holographic (che fa retrieval selettivo invece di iniettare tutto).

**Da verificare:**
- Quanti token in più per ogni 100 caratteri aggiuntivi (circa 25-30 token)
- Impatto sul costo per sessione (trascurabile per provider illimitati come Nous, rilevante per provider pay-per-token)
- Se il limite attuale è già saturo o ha margine

**Note:** Il vantaggio di limiti più alti è che posso salvare più fatti nella memoria built-in senza doverli comprimere o scartare. Lo svantaggio è l'aumento lineare dei token fissi per ogni sessione.

---

## 2. (placeholder per futuri enhancement)