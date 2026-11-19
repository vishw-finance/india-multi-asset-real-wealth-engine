import urllib.request
import json
import time

# 0. Helpers: Indian Numbering Formatter & Bulletproof Numeric Inputs
def format_inr(amount):
    sign = "-" if amount < 0 else ""
    amt_str = f"{abs(amount):.2f}"
    int_part, dec_part = amt_str.split(".")
    
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last_three = int_part[-3:]
        rest = int_part[:-3]
        pairs = []
        while len(rest) > 2:
            pairs.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            pairs.append(rest)
        formatted_int = ",".join(reversed(pairs)) + "," + last_three
        
    return f"{sign}₹{formatted_int}.{dec_part}"

def get_float(prompt, default=0.0):
    while True:
        val = input(prompt).strip().replace(",", "").replace("₹", "")
        if val == "":
            return float(default)
        try:
            return float(val)
        except ValueError:
            print("  Invalid input. Please enter a valid number (e.g., 100000 or 1,00,000).")

def get_int(prompt, default=0):
    while True:
        val = input(prompt).strip().replace(",", "").replace("₹", "")
        if val == "":
            return int(default)
        try:
            return int(val)
        except ValueError:
            print("  Invalid input. Please enter a whole number (e.g., 15).")

# 1. Live India CPI Inflation Puller
def get_india_inflation(years, retries=3):
    url = f"https://api.worldbank.org/v2/country/IND/indicator/FP.CPI.TOTL.ZG?format=json&mrv={years}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            rates = []
            year_labels = []
            for entry in data[1]:
                if entry["value"] is not None:
                    rates.append(float(entry["value"]))
                    year_labels.append(entry["date"])

            if rates:
                return sum(rates) / len(rates), f"{min(year_labels)}-{max(year_labels)}"
        except Exception as e:
            if attempt < retries - 1:
                print(f"Server busy ({e}), retrying...")
                time.sleep(2)
            else:
                print(f"World Bank API unavailable ({e}). Using historical fallback rate.")
                return 5.50, "Fallback Average"

    return 5.50, "Fallback Average"

# 2. Independent Route Calculation Functions
def calculate_route1_sip(monthly_sip, years, step_up_pct, cagr_pct, inf_dec):
    if monthly_sip <= 0:
        return 0.0, 0.0, 0.0, 0.0

    nom_principal = 0.0
    real_principal = 0.0
    nom_corpus = 0.0
    monthly_rate = ((1 + (cagr_pct / 100)) ** (1 / 12)) - 1
    current_sip = monthly_sip

    for i in range(1, years + 1):
        if i > 1:
            current_sip += (step_up_pct / 100) * current_sip
        print(f"Year {i} Monthly SIP: {format_inr(current_sip)}")

        for m in range(12):
            yr_fraction = (i - 1) + (m / 12)
            nom_principal += current_sip
            real_principal += current_sip / ((1 + inf_dec) ** yr_fraction)
            nom_corpus = (nom_corpus + current_sip) * (1 + monthly_rate)

    real_corpus = nom_corpus / ((1 + inf_dec) ** years)
    return nom_principal, real_principal, nom_corpus, real_corpus

def calculate_route2_lumpsum(initial_ls, windfalls_dict, years, cagr_pct, inf_dec):
    if initial_ls <= 0 and not windfalls_dict:
        return 0.0, 0.0, 0.0, 0.0

    nom_principal = initial_ls
    real_principal = initial_ls
    nom_corpus = initial_ls * ((1 + (cagr_pct / 100)) ** years)

    for wf_year, wf_amt in sorted(windfalls_dict.items()):
        if 1 <= wf_year <= years and wf_amt > 0:
            years_remaining = years - wf_year
            nom_principal += wf_amt
            real_principal += wf_amt / ((1 + inf_dec) ** wf_year)
            nom_corpus += wf_amt * ((1 + (cagr_pct / 100)) ** years_remaining)

    real_corpus = nom_corpus / ((1 + inf_dec) ** years)
    return nom_principal, real_principal, nom_corpus, real_corpus

def calculate_route3_gold(q_gross, brokerage_fee, years, cagr_pct, inf_dec):
    if q_gross <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    nom_principal = 0.0
    real_principal = 0.0
    nom_corpus = 0.0
    quarterly_rate = ((1 + (cagr_pct / 100)) ** (1 / 4)) - 1
    net_q_gold = max(0.0, q_gross - brokerage_fee)
    total_brok = brokerage_fee * (years * 4)
    brok_saved = (brokerage_fee * (years * 12)) - total_brok

    for q in range(1, (years * 4) + 1):
        yr_fraction = (q - 1) / 4
        nom_principal += q_gross
        real_principal += q_gross / ((1 + inf_dec) ** yr_fraction)
        nom_corpus = (nom_corpus + net_q_gold) * (1 + quarterly_rate)

    real_corpus = nom_corpus / ((1 + inf_dec) ** years)
    return nom_principal, real_principal, nom_corpus, real_corpus, total_brok, brok_saved

# 3. Main Interactive Execution
if __name__ == "__main__":
    print("(Tip: Enter 0 on any route to skip/isolate it)\n")
    t = get_int("Enter total investment horizon in years (default 15):- ", 15)

    # --- Route 1 Inputs ---
    print("\n=== ROUTE 1: STEP-UP EQUITY SIP ===")
    n = get_float("Enter the first monthly SIP amount (0 to skip):- ", 0)
    if n > 0:
        c = get_float("Enter the annual step-up percentage (%):- ", 0)
        z_sip = get_float("Enter Expected Annual Return (CAGR) for SIP (%):- ", 12)
    else:
        c, z_sip = 0.0, 0.0

    # --- Route 2 Inputs ---
    print("\n=== ROUTE 2: NIFTY 50 / FLEXI-CAP LUMP SUM & WINDFALLS ===")
    lump_sum = get_float("Enter initial Lump Sum amount (0 to skip, Enter for 1,00,000):- ", 100000)
    windfalls = {}
    add_wf = input("Do you want to add expected future windfalls/bonuses? (y/n):- ").strip().lower()
    if add_wf == "y":
        wf_count = get_int("How many windfall events do you want to add?:- ", 0)
        for w in range(1, wf_count + 1):
            wf_year = get_int(f"  Windfall #{w} - Arrival Year (1 to {t}):- ", 1)
            wf_amt = get_float(f"  Windfall #{w} - Amount (INR):- ", 0)
            if wf_amt > 0:
                windfalls[wf_year] = windfalls.get(wf_year, 0.0) + wf_amt

    if lump_sum > 0 or windfalls:
        z_nifty = get_float("Enter Expected Annual Return (CAGR) for Lump Sum/Flexi-Cap (%):- ", 12)
    else:
        z_nifty = 0.0

    # --- Route 3 Inputs ---
    print("\n=== ROUTE 3: QUARTERLY GOLD ETF ===")
    q_gold_gross = get_float("Enter Quarterly Gold ETF order amount (0 to skip, Enter for 4,500):- ", 4500)
    if q_gold_gross > 0:
        brokerage = get_float("Enter brokerage per quarterly order (default 5):- ", 5)
        z_gold = get_float("Enter Expected Annual Return (CAGR) for Gold ETF (%):- ", 9)
    else:
        brokerage, z_gold = 0.0, 0.0

    # --- Macro Inflation ---
    print("\n=== MACRO INFLATION ===")
    cpi_years = get_int("How many years-average CPI do you require (default 10):- ", 10)
    inflation_rate, period = get_india_inflation(cpi_years)
    inf_dec = inflation_rate / 100
    print(f"\nUsing India CPI Inflation ({period}): {inflation_rate:.2f}%\n")

    # --- Run Calculations ---
    sip_np, sip_rp, sip_nc, sip_rc = calculate_route1_sip(n, t, c, z_sip, inf_dec)
    ls_np, ls_rp, ls_nc, ls_rc = calculate_route2_lumpsum(lump_sum, windfalls, t, z_nifty, inf_dec)
    gold_np, gold_rp, gold_nc, gold_rc, tot_brok, brok_saved = calculate_route3_gold(
        q_gold_gross, brokerage, t, z_gold, inf_dec
    )

    # --- Consolidated Totals ---
    tot_nom_principal = sip_np + ls_np + gold_np
    tot_nom_corpus = sip_nc + ls_nc + gold_nc
    tot_nom_gains = tot_nom_corpus - tot_nom_principal

    tot_real_principal = sip_rp + ls_rp + gold_rp
    tot_real_corpus = sip_rc + ls_rc + gold_rc
    tot_real_gains = tot_real_corpus - tot_real_principal

    if tot_nom_corpus > 0:
        equity_share = ((sip_nc + ls_nc) / tot_nom_corpus) * 100
        gold_share = (gold_nc / tot_nom_corpus) * 100
    else:
        equity_share, gold_share = 0.0, 0.0

    # --- Dashboard Output ---
    print("\n" + "=" * 68)
    print(f"          CONSOLIDATED WEALTH DASHBOARD ({t}-YEAR HORIZON)")
    print("=" * 68)

    if windfalls:
        wf_summary = ", ".join([f"Yr {yr}: {format_inr(amt)}" for yr, amt in sorted(windfalls.items())])
        print(f"Active Windfall Injections:  {wf_summary}")

    print("\n[1] ACTIVE ROUTE BREAKDOWN (NOMINAL -> REAL TODAY'S VALUE)")
    if sip_np > 0:
        print(f"Route 1 (Step-Up SIP):       {format_inr(sip_nc):>17}  ->  {format_inr(sip_rc):>17}")
    if ls_np > 0:
        print(f"Route 2 (LumpSum+Windfalls): {format_inr(ls_nc):>17}  ->  {format_inr(ls_rc):>17}")
    if gold_np > 0:
        print(f"Route 3 (Gold ETF):          {format_inr(gold_nc):>17}  ->  {format_inr(gold_rc):>17}")
    if tot_nom_principal == 0:
        print("No active investment routes selected (all inputs were 0).")

    print("\n[2] COMBINED NOMINAL SUMMARY (Future Rupees)")
    print(f"Total Principal Invested:    {format_inr(tot_nom_principal):>17}")
    print(f"Total Nominal Gains:         {format_inr(tot_nom_gains):>17}")
    print(f"Total Nominal Corpus:        {format_inr(tot_nom_corpus):>17}")

    print("\n[3] COMBINED REAL SUMMARY (Today's Purchasing Power)")
    print(f"Real Principal Invested:     {format_inr(tot_real_principal):>17}")
    print(f"Real Purchasing Gains:       {format_inr(tot_real_gains):>17}")
    print(f"Total Real Corpus:           {format_inr(tot_real_corpus):>17}")

    print("\n[4] EXECUTION EFFICIENCY & MATURITY ALLOCATION")
    if gold_np > 0:
        print(f"Total Gold ETF Brokerage:    {format_inr(tot_brok)} (Saved {format_inr(brok_saved)} vs monthly orders)")
    print(f"Equities (SIP + LumpSum/Flexi): {equity_share:.1f}%")
    print(f"Gold (GOLDIETF/SBIGOLD):        {gold_share:.1f}%")
    print("=" * 68)
