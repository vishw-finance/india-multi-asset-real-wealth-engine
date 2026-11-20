# India Multi-Asset Real Wealth & CPI Discounting Engine

A modular Python financial modeling engine built to project nominal and inflation-adjusted (real) wealth across a multi-asset Indian investment portfolio, dynamically discounted using live Consumer Price Index (CPI) data from the World Bank V2 API.

---

## Overview & Motivation

Standard retail SIP and return calculators project future wealth in **nominal rupees**, masking purchasing power erosion over multi-decade horizons and ignoring transaction friction. This engine models three distinct capital deployment routes simultaneously—allowing both **consolidated portfolio forecasting** and **isolated single-route stress testing**—while converting all future cash flows and terminal corpuses back into **Year-0 purchasing power**.

---

## Portfolio Architecture (3 Investment Routes)

1. **Route 1 — Step-Up Equity SIP (Core Compounding Engine)**
   - Models monthly equity contributions with annual percentage step-ups (`c%`).
   - Uses **effective monthly CAGR conversion** rather than naive linear division:
     $$r_{\text{monthly}} = (1 + r_{\text{annual}})^{1/12} - 1$$
   - Applies start-of-month discounting $\left(t = (i - 1) + \frac{m}{12}\right)$ so Year-1 Month-1 capital is treated as Year-0 cash flow.

2. **Route 2 — Nifty 50 / Flexi-Cap Lump Sum & Windfall Hook**
   - Compounds initial Year-0 lump sum capital alongside an optional dictionary of irregular future cash injections (`{year: amount}`) such as annual bonuses or liquidity events.
   - Each windfall compounds for exact remaining tenure $(T - t_{\text{arrival}})$ and discounts back to Year-0 real principal.

3. **Route 3 — Quarterly Gold ETF Execution (`GOLDIETF` / `SBIGOLD`)**
   - Models quarterly capital deployment using effective quarterly CAGR:
     $$r_{\text{quarterly}} = (1 + r_{\text{annual}})^{1/4} - 1$$
   - Explicitly accounts for fixed delivery brokerage drag per order (`₹5` default) while tracking cumulative brokerage savings achieved by batching monthly allocations into quarterly limit orders.

---

## Macro Inflation & Resilience Features

- **Live World Bank V2 API Integration:** Queries indicator `FP.CPI.TOTL.ZG` for India (`IND`) across a user-defined trailing window (`mrv=N` years) to compute an empirical average CPI rate.
- **Fault-Tolerant Fallback:** Implements custom `User-Agent` headers, timeout handling, and automated retries with graceful fallback (`5.50%` historical average) if the external API experiences downtime.
- **Indian Numbering Formatter (`format_inr`):** Formats all monetary outputs into standard Indian comma notation (`₹XX,XX,XXX.XX`).
- **Defensive CLI Guards:** Supports isolated route testing (entering `0` skips inactive routes), blank-input defaults, comma/currency symbol stripping (`1,00,000` or `₹1,00,000`), and zero-division protection.

---

## Quick Start

Requires **Python 3.8+** (uses Python standard library only—no external `pip` dependencies required).

```bash
git clone [https://github.com/vishw-finance/india-multi-asset-real-wealth-engine.git](https://github.com/vishw-finance/india-multi-asset-real-wealth-engine.git)
cd india-multi-asset-real-wealth-engine
python wealth_engine.py