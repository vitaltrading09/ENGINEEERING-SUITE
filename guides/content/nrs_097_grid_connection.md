# NRS 097 — Grid Connection Requirements for Embedded Generation (South Africa)

This guide covers the South African requirements for connecting embedded generation (solar PV, battery storage, generators) to the distribution grid. The primary standard is **NRS 097-2-1:2017** (Small-scale embedded generation ≤ 100 kVA) and **NRS 097-2-3** (Medium-scale embedded generation 100 kVA – 1 MVA). Municipal utilities may impose additional requirements via their own grid codes.

> **Important:** Requirements differ significantly between Eskom-connected customers and municipality-connected customers. Always confirm the applicable network operator's technical standard before design.

---

## 1. Regulatory Framework

### 1.1 Key Standards & Legislation

| Document | Description |
| :--- | :--- |
| **NRS 097-2-1:2017** | SSEG ≤ 100 kVA — Single-phase ≤ 16 A, Three-phase ≤ 50 kVA |
| **NRS 097-2-3:2014** | MSEG 100 kVA – 1 000 kVA |
| **SANS 10142-1:2020** | Wiring of premises — LV installation requirements |
| **SANS 10142-3** | PV installations on premises |
| **NERSA Grid Code** | National standard (Grid Connection Code for Renewable Power Plants) |
| **Electricity Act 4 of 2006** | Licensing and registration requirements |
| **OHS Act 85 of 1993** | Occupational health and safety |

### 1.2 Registration Requirements
- **SSEG (≤ 100 kVA):** Notify the network operator. In most municipalities, submit a **Small-Scale Embedded Generation (SSEG) application** and obtain approval before energising.
- **MSEG (> 100 kVA):** Requires a formal grid connection agreement, protection study, and in many cases a NERSA generation licence.
- **Certificate of Compliance (CoC):** Required for any electrical installation — must be issued by a registered wireman/electrician under the Electrical Installation Regulations.

---

## 2. Protection Requirements — NRS 097-2-1

The inverter or protection relay at the point of connection must implement the following protection functions.

### 2.1 Anti-Islanding Protection (Mandatory)

> **Critical Safety Requirement:** Anti-islanding protection prevents the embedded generator from continuing to supply power to a section of the grid after the network has been de-energised by the utility. If islanding occurs, utility workers may encounter a live conductor they believe to be dead — with fatal consequences.

All grid-connected inverters must incorporate **active anti-islanding** detection. Passive detection alone is not sufficient per NRS 097-2-1.

**Tripping requirement:** The inverter must detect islanding and disconnect within **2 seconds** of islanding occurring.

### 2.2 Voltage Protection

| Protection Function | Trip Setting | Time Delay |
| :--- | :--- | :--- |
| Over-Voltage Stage 1 (OV1) | > 110% Vn (> 253 V for 230 V system) | 2.0 s |
| Over-Voltage Stage 2 (OV2) | > 115% Vn (> 264.5 V) | 0.2 s |
| Under-Voltage Stage 1 (UV1) | < 85% Vn (< 195.5 V) | 2.0 s |
| Under-Voltage Stage 2 (UV2) | < 80% Vn (< 184 V) | 0.5 s |

> Note: Vn = 230 V (single-phase L-N) or 400 V (L-L three-phase) per SANS 61000-2-2 for SA LV networks.

### 2.3 Frequency Protection

| Protection Function | Trip Setting | Time Delay |
| :--- | :--- | :--- |
| Over-Frequency (OF) | > 51.5 Hz | 0.5 s |
| Under-Frequency Stage 1 (UF1) | < 49.0 Hz | 0.5 s |
| Under-Frequency Stage 2 (UF2) | < 47.0 Hz | 0.2 s |

> SA nominal frequency is **50 Hz**. Eskom's normal operating band is 49.85 – 50.15 Hz.

### 2.4 Reconnection Requirements
After a trip on voltage or frequency, the inverter must **not reconnect** to the grid until:
- Voltage is within the normal operating range for a continuous period of **60 seconds**.
- Frequency is within the normal operating band for a continuous period of **60 seconds**.

This prevents rapid reconnection during unstable grid conditions.

---

## 3. Power Quality Requirements — NRS 097 / SANS 61000

### 3.1 Harmonic Distortion
- Total Harmonic Distortion (THD) of injected current: **≤ 5%** at rated output (NRS 097-2-1 Table 3).
- Individual harmonic limits per SANS 61000-3-2 (for equipment ≤ 16 A per phase).

### 3.2 DC Injection
- Maximum DC current injection at the point of connection: **≤ 0.5%** of rated AC output current (NRS 097-2-1).
- DC injection can cause transformer core saturation and accelerated aging.

### 3.3 Power Factor
- For SSEG ≤ 100 kVA: unity power factor operation (or within 0.95 leading/lagging if agreed with utility).
- Eskom distribution networks typically require **unity PF** for SSEG to avoid causing voltage regulation issues.

### 3.4 Flicker
- Pst (short-term flicker): **≤ 1.0** at the point of connection (SANS 61000-3-3).
- Plt (long-term flicker): **≤ 0.65**.

---

## 4. Metering Requirements

### 4.1 Import/Export Metering
All SSEG/MSEG installations require a **bi-directional smart meter** capable of measuring both imported and exported energy.

- **SSEG (≤ 100 kVA):** CT/VT-based metering typically not required. Direct-connect smart meter (e.g., Landis+Gyr E350, Itron ACE6000) acceptable.
- **MSEG (> 100 kVA):** CT-based metering required. Metering CTs must comply with **SANS 62052** (accuracy class 0.5S or better).

### 4.2 Communication
- For Eskom-connected MSEG: communication-capable meters required (PLC or GPRS).
- Municipalities vary — confirm with the relevant utility.

### 4.3 Protection Metering vs Revenue Metering
Revenue metering must be separate from protection metering. Do not use protection CTs for revenue metering in MSEG installations — accuracy classes differ (protection: 5P; revenue: 0.5S or 0.2S).

---

## 5. Technical Connection Requirements

### 5.1 Point of Connection (POC)
The POC is the boundary point between the customer's installation and the network operator's infrastructure. For most residential/commercial SSEG:
- **Single-phase SSEG ≤ 16 A:** Connect at the distribution board, behind the utility meter. Feed directly from the DB via a dedicated MCB.
- **Three-phase SSEG ≤ 50 kVA:** Connect at the MCC or main DB. Dedicated AC disconnect required between inverter and POC.

### 5.2 Isolation & Disconnection
A **visible, lockable AC isolator** must be installed between the inverter and the grid at a location accessible to the network operator — typically at the main DB or on the meter board.

This allows the utility to safely isolate the embedded generator during network maintenance.

### 5.3 Cable Sizing
All AC cabling from inverter to POC must comply with **SANS 10142-1:2020**:
- Sized for the **maximum continuous AC output** of the inverter (not the DC input).
- Voltage drop ≤ 5% per SANS 10142-1 §6.2.7.
- Apply all applicable derating factors (ambient temperature, grouping, installation method).

Use the Voltage Drop and Cable CCC calculators in this suite for these calculations.

### 5.4 Earthing
- All metallic enclosures (inverter chassis, DC combiner, AC panel) must be connected to the installation earth.
- For transformerless inverters (most string inverters): the PV array negative pole must **not** be earthed — most modern inverters incorporate floating DC bus with earth leakage monitoring.
- Earthing of the PV array frame is required as a protective measure (not functional earth).
- Follow **SANS 10142-1 Part 3** for PV-specific earthing requirements.

---

## 6. DC Side Requirements (PV Specific) — SANS 10142-3

### 6.1 String & Array Protection
- **String fuses or combiner fuse holders:** Required where more than 2 strings are connected in parallel, per SANS 10142-3.
- **DC isolator:** Required at the inverter DC input terminals and at the PV array (roof level). Must be rated for DC voltage (AC-rated isolators are not suitable).
- **DC cable ratings:** Must be rated for the open-circuit voltage of the PV string at minimum cell temperature (use Voc × 1.15 correction for cold climates, or manufacturer's Voc temperature coefficient × lowest expected temperature).

### 6.2 PV String Voltage (SA Climate Considerations)
South Africa's Highveld can reach temperatures below 5°C in winter mornings (Johannesburg: min ~4°C in July). Use temperature-corrected Voc:

`Voc_corrected = Voc_STC × [1 + β_Voc × (T_min − 25°C)]`

where β_Voc is the voltage temperature coefficient (typically −0.3% to −0.4%/°C).

Ensure the string Voc_corrected does not exceed the inverter's maximum input voltage at any time.

---

## 7. Application Process — Typical SA Municipality (e.g., City of Joburg / Tshwane)

1. **Pre-Application:** Engage a registered electrical contractor and energy consultant.
2. **Load Analysis:** Confirm the installation's maximum demand (MD) and average consumption to size the system appropriately.
3. **Submit SSEG Application:** Submit to the municipality's Energy Department with:
   - Completed SSEG application form
   - Single-line diagram of the installation
   - Equipment specifications (inverter, PV panels)
   - CoC from a registered wireman
4. **Municipality Technical Review:** Review of protection settings and grid impact (typically 10–30 business days).
5. **Meter Upgrade:** Municipality installs bi-directional smart meter.
6. **Energisation:** Conditional approval issued; system may be energised.
7. **Annual Monitoring:** Some municipalities require annual energy data submission.

> **Common Rejection Reasons:** Missing CoC, inverter not on approved product list, protection settings not compliant with NRS 097-2-1, system oversized relative to installation's consumption.

---

## 8. Quick Reference: SSEG System Size Limits

| Connection Type | Max Inverter Output | Max PV Array Size | Typical Application |
| :--- | :--- | :--- | :--- |
| Single-phase (16 A) | 3.68 kW | ~4.5 kWp | Residential |
| Three-phase (3×16 A) | 11.04 kW | ~13 kWp | Large residential / small commercial |
| Three-phase (3×32 A) | 22.08 kW | ~26 kWp | Commercial |
| Three-phase (≤ 100 kVA) | 100 kVA | ~110 kWp | Commercial / light industrial |
| MSEG (≤ 1 MVA) | 1 MVA | ~1.1 MWp | Industrial / large commercial |

> Note: Some municipalities limit SSEG to 75% or 80% of the installation's notified maximum demand. Confirm with your specific network operator.

---

## 9. Relevant Contacts & Resources

| Organisation | Resource |
| :--- | :--- |
| NERSA | www.nersa.org.za — SSEG licensing threshold information |
| SANEDI | www.sanedi.org.za — SA renewable energy technical resources |
| SABS | www.sabs.co.za — NRS and SANS standard procurement |
| Eskom | www.eskom.co.za/distribution — Eskom SSEG application portal |
| SAPVIA | www.sapvia.co.za — SA Photovoltaic Industry Association |
