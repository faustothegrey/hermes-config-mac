# Nous Portal Billing — HTML Scrape Reference

## URL

```
https://portal.nousresearch.com/orgs/c2b2d336/billing
```

Redirects to `https://portal.nousresearch.com/refresh?callbackUrl=...` when unauthenticated, then to `https://portal.nousresearch.com/login?callbackUrl=...`.

## Auth mechanism

Privy-powered OAuth login dialog. Options in the modal:
- **Google** — OAuth button
- **GitHub** — OAuth button
- **Discord** — OAuth button
- **Email** — inline textbox with Submit button (sends confirmation code via email)
- **More options** — opens a crypto wallet picker (MetaMask, Phantom, etc.) — **not** the path for email login

## Cookie capture approach

After successful login via browser:
1. Navigate to the billing page URL
2. Extract cookies via `browser_console(expression="document.cookie")`
3. Save to `~/.hermes/secrets/nous-cookies.txt` in Netscape cookie jar format:

```bash
# Netscape HTTP Cookie File
portal.nousresearch.com   TRUE   /   FALSE   1777777777   __session   eyJ...
portal.nousresearch.com   TRUE   /   FALSE   1777777777   __privy    abc...
```

Use `chmod 600 ~/.hermes/secrets/nous-cookies.txt`.

## Vercel Security Checkpoint — blocks all curl/CLI requests

The Nous Portal is served through **Vercel** and uses a **Vercel Security Checkpoint** (JS challenge) that activates after repeated auth-detected attempts. Characteristics:

- HTTP **429** status code
- HTML body: title `Vercel Security Checkpoint`, JS proof-of-work module embedded in `<script>` tags
- curl cannot execute the JS challenge, so even valid cookies won't reach the billing page
- The page never passes the Vercel edge — curl gets the challenge page, not the app

**Curl will NOT work against the billing page even with valid cookies.** The Vercel challenge intercepts at the edge before application routing.

## Cookie injection via browser_console — attempted Privy bypass

Since curl is Vercel-blocked, injecting cookies into Browserbase headless was tried:

```
# On privy.nousresearch.com (cookie domain):
browser_console(expression='document.cookie = "privy-access-token=<JWT>..."')
browser_console(expression='document.cookie = "privy-refresh-token=<token>..."')
# On portal.nousresearch.com:
browser_console(expression='document.cookie = "privy-id-token=<JWT>..."')
browser_console(expression='document.cookie = "privy-session=privy.nousresearch.com..."')
```

**Result:** Still redirects to login. Reason: Privy uses an **iframe-based SDK** (`privy.nousresearch.com` embedded in an iframe on the portal page) with postMessage-based auth. Setting cookies alone does not trigger the Privy SDK's runtime auth state. Full user-initiated login is required.

**No known programmatic bypass exists.** The only reliable way to get billing data is:
1. Full interactive login via browser tools (email → OTP code → billing page)
2. User screenshot from their physical browser (the user is already logged in)

## Billing page structure (observed via screenshot, 2026-06-27)

The billing page at `https://portal.nousresearch.com/orgs/c2b2d336/billing` shows:

### Header
- Title: **BILLING** / subtitle: "Manage subscription and top-up credits for this team."
- Org ID in URL: `c2b2d336` (the user's team/org)

### Total balance
- Large centered dollar amount: **$23.86** (example value)
- Right-aligned text: "Cycle ends Jul 17, 2026"

### Balance breakdown (stacked bar chart + legend)

| Component | Icon color | Value | Details |
|-----------|-----------|-------|---------|
| Top-up Credits | Green | $20.00 | Last purchase date; "Does not expire" |
| Subscription Credits | Blue | $3.86 | "$22.00 provided this period"; "Expires or rolls over on <date>" |
| Spent This Period | Dashed | -$18.14 | Link to "Detailed usage" |

### Credit deduction logic (footer info box)
- Light blue box: "Usage is deducted from subscription credit first."
- "At the end of the period, subscription credit may expire or roll over according to plan rules; top-up credit remains available."

### Fallback: user screenshot approach
When automated login fails (browser session dies, rate-limited, Vercel challenge), ask the user to open the billing URL in their physical browser and either:
1. Paste the numbers directly, or
2. Take a screenshot for vision_analyze

Key terms to look for: "Top-up Credits", "Subscription Credits", "Spent This Period", "Cycle ends".

## Privy login modal — exact browser interaction flow

The login uses **Privy** (embedded OAuth widget). The modal has several distinct states:

### State 1: Login dialog — "Welcome to Nous Portal"

Triggered by clicking button `login _` [ref=e3/e4] on the sign-in page. The dialog contains:

| Element | Ref | Action |
|---------|-----|--------|
| `Google` button | e21 | OAuth redirect — not usable from headless browser |
| `GitHub` button | e22 | OAuth redirect — not usable |
| `Discord` button | e23 | OAuth redirect — not usable |
| Email textbox | e28 | Type the user's email here |
| `Submit` button | e29 | Initially `[disabled]` — enables after typing email |
| `More options` | e24 | **Dead end for email login** — opens a crypto wallet picker (MetaMask, Phantom, 600+ entries). Close via the close-modal button to return to the standard dialog. |

**Steps to submit email:**
```
browser_click(ref="@e4")        # click "login _"
browser_type(ref="@e28", text="user@email.com")
browser_click(ref="@e29")       # click Submit (now enabled)
```

**Pitfall:** `More options` opens a huge wallet list. If you accidentally click it, close the modal and re-open: click the close button (e20/e21/e27 depending on state), then `login _` again.

**Pitfall — user can't type `@`:** The user cannot type the `@` symbol on their keyboard. When you need their email, ask for the parts separately: "what's the part before @ and the part after?" — never ask for the full email inline.

### State 2: "Enter confirmation code" — 6-digit OTP

After submitting the email, the dialog shows:

| Element | Ref | Action |
|---------|-----|--------|
| heading "Enter confirmation code" | e28 | Text indicator of state |
| Textbox 1 (first digit) | e20 | Type first digit |
| Textbox 2 | e21 | Type second digit |
| Textbox 3 | e22 | Type third digit |
| Textbox 4 | e23 | Type fourth digit |
| Textbox 5 | e24 | Type fifth digit |
| Textbox 6 | e25 | Type sixth digit |
| `Resend code` button | e29 | Click if the code expires |

**Steps to enter code (e.g., `964536`):**
```
browser_type(ref="@e20", text="9")
browser_type(ref="@e21", text="6")
browser_type(ref="@e22", text="4")
browser_type(ref="@e23", text="5")
browser_type(ref="@e24", text="3")
browser_type(ref="@e25", text="6")
```

**Auto-submit behaviour:** The form may or may not auto-submit after all 6 digits are entered. After entering all digits:
- First check the page snapshot — if the login modal disappears → login succeeded
- If the modal stays on the code-entry screen → the code likely expired (see below)
- Pressing Enter usually doesn't help when the code is already expired
- **Workflow: get the code → type it immediately → check result.** Any delay between the user providing the code and the last digit being typed risks expiry.

**Pitfall — browser session volatility:** The Privy login flow (email → OTP code → redirect → billing page) is sensitive to session continuity. Browserbase headless sessions can die or reset between navigations (visible as a sudden "(empty page)" snapshot with `top: null` in the frame tree). If the session dies mid-flow:

1. Navigate back to `https://portal.nousresearch.com/login?callbackUrl=...` to restart
2. Re-type the email
3. Ask the user for a fresh confirmation code since the old one will have expired
4. Type the code and move to the billing page in one sequence without delays

To minimise session death, complete the email → code → billing navigation chain as quickly as possible. Do not take intermediate snapshots beyond what's needed to find refs.

**Code expiry:** Confirmation codes sent via email expire after a few minutes. If entering the code doesn't advance past the OTP screen (pressing Enter after all 6 digits doesn't help either), the code has expired. Click `Resend code` [ref=e29] and ask the user for the new code. Type the new code immediately — don't take intermediate steps or navigate elsewhere first.

### State 3: Post-login (billing page)

*Not yet observed — update this section after a successful login session.*

Expected: redirect to `https://portal.nousresearch.com/orgs/{org_id}/billing`. Document the HTML elements that contain:
- Credits remaining (dollar amount)
- Usage this period
- Plan tier / subscription type
- Reset date
