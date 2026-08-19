# CasaSpese

Detailed project memory for the CasaSpese expense management tool.

- **Project Path:** `/Users/fausto/Software/CasaSpese`
- **UI Codebase:** `/Users/fausto/Software/CasaSpese/casa-spese-ui`
- **Purpose:** Local Next.js app to parse credit card/bank statements, filter out closed billing periods, check live Google Sheets for already-recorded transactions, classify remaining movements using a deterministic rules engine, suggest expected recurring costs, and post new records chronologically back into the Google Sheet.

---

## 🛠 Architecture & Workflow

### 1. Data Parsing & Billing Periods
- Reads and parses *Banca Cambiano* statements (`Movimenti.csv`).
- Groups transactions into billing periods from the **24th of the previous month** to the **23rd of the current month**.
- A period is considered **closed** if all transactions in that period on the spreadsheet are marked as `"Saldato"`. Closed periods are filtered out of active views.
- **Dynamic Boundary Filtering:** The system scans the live spreadsheet, determines the oldest transaction recorded (e.g. April 2025), and automatically filters out any statement entries older than that boundary.

### 2. Live Reconciliation & Deduplication
- Reads live data from the Google Sheet `"Conti"`.
- Builds a lookup table mapping transaction amounts to recorded dates.
- Matches statement entries with recorded spreadsheet transactions. If they match on amount and date (accounting or value date), they are flagged as already recorded and hidden.

### 3. Rules Engine & Ambivalence Prevention
- Matches transaction descriptions against keywords.
- Rules are defined in [[rules.json]] (or [rules.json](file:///Users/fausto/Software/CasaSpese/casa-spese-ui/data/rules.json)) and ordered by priority (user-defined custom rules execute first).
- **Overlapping Guard:** Implementing `validateRulesetNoOverlaps` in the store layer. If any rule update (POST/PUT) would cause a transaction to be matched by more than one rule, the save is blocked and an error is returned.
- **States:**
  - `AUTO`: Categorizes automatically and allows batch upload.
  - `DA_DECIDERE`: Wizard asks user to choose a category, exclude, or create a new rule.
  - `ESCLUSA`: Excludes from sheet upload (e.g., ATM withdrawals, internal transfers).

### 4. Persistent Transaction Ledger
- Bank statement uploads are merged and deduplicated via the stable key `txId` (`date|amount|description`) into `data/transactions.json` to handle partial statements of varying timeframes.

### 5. Recurrent Items
- Simulates expected monthly/weekly cash and Nexi card transactions (e.g. housekeeper cash, internet fee).
- Generates occurrences within active billing periods and proposes inserting them if they do not yet exist in the sheet.

---

## 📈 UI Dashboards

1. **Home (`/`):** Main workspace for processing statement uploads, editing categorization rules, and executing inserts.
2. **Pro (`/pro`):** Financial dashboard showing total expenditures, income, net balance, an Area chart of historical balances, and a Bar chart of daily spending patterns.

---

## 🚀 Potential Enhancements
- **Rule Exclusions UI:** Add the ability to delete or deactivate rules directly from the web interface instead of manually updating `data/rules.json`.
- **Advanced Charts:** Add a breakdown of category-wise spending over time to the Pro page.

## 2026-06-16 Portfolio Review Notes

Source: [[Software Projects Review 2026-06-16]]

The portfolio review classified CasaSpese as the most advanced project in `/Users/fausto/Software`.

Review takeaways:

- Mature, multi-feature, actively worked in June.
- Real OAuth and Google Sheets integration.
- The deterministic, versioned-rules, no-black-box/ML reconciliation stance is valuable and product-defensible.
- Handling recurrences and cash transactions with no bank trace is a distinctive practical strength.
- API/feature surface mentioned by review: `rules`, `recurrences`, `transactions`, `archive`, Google Sheets sync, OAuth, and `consulente` / advisor message history.

Security/hygiene caution from review, corrected by [[Cross-Project Patterns 2026-06-16]]:

- `credentials.json` and `token.json` were observed in the tree at review time.
- Original review said there was no git repo protection, but follow-up verification found `/Users/fausto/Software/CasaSpese/casa-spese-ui/.git` exists.
- `/Users/fausto/Software/CasaSpese/casa-spese-ui/.gitignore` protects `token.json`, `.env*`, `.DS_Store`, `*.csv`, and `data/transactions.json`.
- Remaining hygiene concern: if `credentials.json` sits in the parent `/Users/fausto/Software/CasaSpese` folder, it is outside the `casa-spese-ui` repo but still a plaintext local credential file.

Cross-project idea:

- Consider integrating or borrowing from `/Users/fausto/Software/SpreadGit` for minimal-diff Google Sheets patching. SpreadGit-style deltas are a natural fit for CasaSpese's auditability/versioned-rules design.

## Deep portfolio assessment notes

Source: [[Deep Portfolio Assessment 2026-06-16]]

Claude's deeper project review keeps CasaSpese as a high-priority project because it is mature and personally useful, while also carrying the most important hygiene/data-risk work.

Key development directions from that assessment:

- Add/verify a CasaSpese-root `.gitignore` before any root `git init`, because the UI subproject is a repo but the parent project root is not.
- Add unit tests for pure rule-engine functions such as `classificaWith`, `findMatchingRuleIds`, and `suggestKeyword`.
- Add a rule-change audit log: which rule version classified which transaction and when.
- Add a rule-coverage view showing auto-classified vs `DA_DECIDERE` transactions.
- Decompose the large home page into smaller components/hooks.
- Replace or supplement ad-hoc Google Sheets writes with SpreadGit-style minimal diffs.
- Longer-term: extract the deterministic ledger/reconciliation engine into a standalone reusable library.

Cross-project leverage:

- Consume SpreadGit for minimal-diff Sheets writes.
- Donate the `agentapi` / subscription-CLI backend pattern to WebElementChat and scripts-ai.
- Reuse the Vault-as-context approach more broadly.
