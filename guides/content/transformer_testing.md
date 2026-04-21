# Transformer Testing — South African Standards

This guide covers routine, acceptance, and diagnostic testing of distribution and power transformers in South Africa. It aligns with **SANS 780:2014** (distribution transformers), **SANS 60076** (IEC 60076 adopted by SABS), **NRS 097-2** (Eskom Network & Customer specifications), and **SANS 10142-1** where applicable to LV wiring associated with transformers.

> **Important:** Always cross-reference your specific client's specification. Eskom, City Power, and municipal utilities may impose additional requirements beyond SANS minimums via their own Network Standards (NRS series).

---

## 1. Safety Prerequisites — Non-Negotiable

Before any test equipment is connected, the following steps are **mandatory** under South African OHS Act (Act 85 of 1993) and SANS 10142-1:

- **De-energize & Isolate:** Disconnect all HV and LV sources. Confirm isolation with an approved voltage detector.
- **Lock Out / Tag Out (LOTO):** Apply padlocks and danger tags per your site LOTO procedure. Retain the key.
- **Earth all Windings:** Apply earthing clamps to HV and LV terminals, and to the tank. Discharge stored energy.
- **Discharge Capacitance:** Large transformers hold capacitive charge — wait the prescribed discharge time (typically 5 minutes per 10 kV of winding voltage class) after isolation before touching terminals.
- **PPE:** Rubber insulating gloves (class rated for the voltage), arc flash face shield, and flame-resistant clothing are required for all LV and MV work.
- **Gas Check (Oil Transformers):** Check for combustible gas accumulation before opening inspection covers on oil-filled units.

---

## 2. Insulation Resistance (IR) Test
**Status: MANDATORY (Routine) — SANS 780:2014 / NRS 097-2**

### Purpose
IR testing detects moisture ingress, surface contamination, and thermal aging of the winding insulation before a catastrophic failure occurs. A high-voltage DC source (Megger / insulation tester) measures the leakage current through the dielectric to calculate resistance in MΩ or GΩ.

### Recommended Test Voltages (DC)

| Winding Voltage Class | Recommended Megger Voltage |
| :--- | :--- |
| LV Side (415 V / 1 kV class) | 500 V or 1 000 V DC |
| HV Side (up to 11 kV) | 2 500 V DC |
| HV Side (11 kV – 33 kV) | 5 000 V DC |
| HV Side (above 33 kV) | 10 000 V DC |

### Minimum Acceptance Criteria (at 20°C)

| Voltage Class | Oil-Filled (Min MΩ) | Dry-Type (Min MΩ) |
| :--- | :--- | :--- |
| Up to 600 V (incl. 415 V) | 100 MΩ | 500 MΩ |
| 600 V – 5 kV (incl. 1.2 kV) | 1 000 MΩ | 5 000 MΩ |
| 5 kV – 15 kV (incl. 11 kV) | 5 000 MΩ | 25 000 MΩ |
| 15 kV – 69 kV (incl. 22 kV, 33 kV) | 10 000 MΩ | 50 000 MΩ |

> **NRS 097-2 Note:** Eskom requires a minimum IR of 1 000 MΩ for distribution transformers at 11 kV on the HV side. Values below 100 MΩ on any winding are considered a failure requiring investigation.

### Temperature Correction
IR readings are halved for every 10°C increase. Normalise all readings to **20°C** to compare against baseline or Factory Acceptance Test (FAT) data.

`IR_20°C = IR_Measured × Correction Factor`

| Temp (°C) | 0°C | 10°C | 20°C | 30°C | 40°C | 50°C |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Factor** | 0.25 | 0.50 | 1.00 | 1.98 | 3.95 | 7.85 |

### Test Configurations
All three configurations below must be measured:

1. **HV to (LV + Tank/Earth):** Megger on HV terminals; short and earth the LV terminals and tank.
2. **LV to (HV + Tank/Earth):** Megger on LV terminals; short and earth the HV terminals and tank.
3. **(HV + LV) to Tank/Earth:** Both windings connected to Megger; tank earthed. Tests inter-winding and core insulation together.

---

## 3. Polarization Index (PI)
**Status: MANDATORY (Routine) — IEEE 43 / SANS 60076**

The PI is derived from the IR test and provides information about the moisture content and condition of the insulation.

`PI = IR (10-minute reading) ÷ IR (1-minute reading)`

| PI Value | Insulation Condition |
| :--- | :--- |
| < 1.0 | **Dangerous** — Moisture or breakdown suspected |
| 1.0 – 1.5 | **Poor** — Investigate before energising |
| 1.5 – 2.0 | **Questionable** — Monitor closely |
| 2.0 – 4.0 | **Good** |
| > 4.0 | **Excellent** |

> A PI below 1.5 on a transformer that was previously in service should trigger a Dissolved Gas Analysis (DGA) before re-energisation.

---

## 4. Transformer Turns Ratio (TTR) Test
**Status: MANDATORY (Routine) — SANS 780:2014 / IEC 60076-1**

### Purpose
Validates that the actual turns ratio matches the nameplate, confirms tap changer operation, and verifies correct phase configuration on all taps.

### Procedure
1. Apply the TTR test set to HV and LV terminal pairs (A-a, B-b, C-c for 3-phase).
2. Test on **all tap positions** if an OLTC or DETC is fitted.
3. Record ratio and phase displacement for each tap.

### Acceptance Criteria (SANS 780:2014 / IEC 60076-1)
- Ratio must be within **±0.5%** of the theoretical nameplate ratio on all taps.
- Phase displacement (vector group) must match nameplate (e.g., Dyn11).

> **Common SA Vector Groups:** Dyn11 (most distribution transformers), YNyn0, Yzn11. Confirm with nameplate — incorrect vector group assumption is a frequent commissioning error.

---

## 5. Winding Resistance Test
**Status: MANDATORY (Routine) — SANS 780:2014 / IEC 60076-1**

### Purpose
Measures the DC resistance of copper or aluminium windings to identify loose connections, broken strands, poor solder joints, or tap changer contact problems.

### Procedure
- Inject a continuous DC test current (1 A to 10 A).
- Wait for the inductive core to saturate — the reading must be **stable** before recording (this can take several minutes on large transformers).
- Use a **4-wire (Kelvin) connection** to eliminate test lead resistance.
- Measure all three phases on both HV and LV sides.
- Test on all tap positions if OLTC/DETC fitted.

### Temperature Correction
All readings must be corrected to **75°C** (or the factory reference temperature) using:

`R_ref = R_measured × (T_ref + 235) / (T_measured + 235)`   *(for copper)*
`R_ref = R_measured × (T_ref + 225) / (T_measured + 225)`   *(for aluminium)*

### Acceptance Criteria
- Deviation between any two identical phases: **≤ 1.0%** (SANS 780), **≤ 2.0%** (IEC 60076).
- All readings must match FAT data within **±2%** when temperature-corrected.

---

## 6. Short Circuit Impedance & Load Loss Test
**Status: MANDATORY (Type Test / FAT) — IEC 60076-1**

Verifies the transformer's short-circuit impedance (Vk%) which is critical for fault level calculations and protection coordination (see Short Circuit Current calculator in this suite).

### Acceptance Criteria
- Vk% must be within **±7.5%** of the nameplate value for distribution transformers (IEC 60076-11).
- Standard SA distribution transformer Vk% values (SANS 780):
  - 50 kVA – 500 kVA: **4.0%**
  - 630 kVA – 2 500 kVA: **6.0%**

---

## 7. Tan Delta (Dissipation Factor) Test
**Status: HIGHLY RECOMMENDED (Diagnostic) — IEC 60250 / SANS 60076-3**

Evaluates the overall health of the combined insulation system (paper + oil). Sensitive to moisture ingress and aging. Performed with a Tan Delta bridge (e.g., Megger DELTA 4000, Omicron Dirana).

### Measurement Modes
- **GST (Grounded Specimen Test):** HV winding to earth — detects bulk insulation degradation.
- **UST (Ungrounded Specimen Test):** HV winding to LV winding — tests interwinding insulation.

### Acceptance Criteria

| Condition | Tan δ Value | Interpretation |
| :--- | :--- | :--- |
| New transformer (at 20°C) | < 0.5% | Excellent |
| In-service (acceptable) | 0.5% – 1.0% | Good |
| Requires monitoring | 1.0% – 2.0% | Deteriorating |
| Immediate action required | > 2.0% | Significant moisture or aging |

> **SA Climate Note:** In coastal regions (Durban, Cape Town) humidity accelerates paper insulation aging. Tan delta values above 1.5% on a transformer less than 10 years old warrants oil filtration and vacuum drying.

---

## 8. Oil Diagnostics
**Status: MANDATORY for Oil-Filled Units — SANS 290 / IEC 60156**

### 8.1 Breakdown Voltage (BDV)
Tests the dielectric strength of the insulating oil.

| Standard | Minimum BDV |
| :--- | :--- |
| SANS 290 (new oil) | ≥ 60 kV |
| SANS 290 (service oil, 11–33 kV transformers) | ≥ 40 kV |
| NRS 097-2 (Eskom distribution) | ≥ 50 kV |

### 8.2 Water Content (Karl Fischer Titration)

| Application | Maximum Water Content |
| :--- | :--- |
| Transmission (≥ 132 kV) | < 10 ppm |
| Distribution (11 kV – 33 kV) | < 20 ppm |
| LV Distribution (≤ 11 kV) | < 30 ppm |

### 8.3 Dissolved Gas Analysis (DGA) — SANS 60599
DGA is the most powerful diagnostic tool for detecting incipient faults inside oil-filled transformers. Key fault gases and their significance:

| Gas | Fault Indicated | Action Threshold |
| :--- | :--- | :--- |
| Hydrogen (H₂) | Partial discharge (corona) | > 100 ppm |
| Methane (CH₄) | Thermal fault (< 300°C) | > 120 ppm |
| Ethylene (C₂H₄) | Thermal fault (> 300°C) | > 50 ppm |
| Acetylene (C₂H₂) | **Arcing / flashover** | **> 5 ppm** |
| Carbon Monoxide (CO) | Solid insulation overheating | > 500 ppm |
| Carbon Dioxide (CO₂) | Solid insulation aging | > 10 000 ppm |

> **Critical:** Any detection of Acetylene (C₂H₂) above 5 ppm warrants immediate investigation. Acetylene is only produced at temperatures above 700°C, indicating arcing inside the tank.

---

## 9. Sweep Frequency Response Analysis (SFRA)
**Status: SPECIALIZED — IEC 60076-18 / CIGRE TB 342**

SFRA detects mechanical deformation of the core and windings — winding displacement, core movement, or clamping loosening — that cannot be detected by electrical tests alone.

### When to Perform SFRA
- After a through-fault or close-in short circuit
- After transport (especially by road in South Africa — rural roads cause vibration damage)
- As a baseline test on commissioning of new large transformers (≥ 5 MVA)
- If transformer shows unusual noise or vibration in service

### Interpretation
Compare the measured frequency response curve against the baseline (FAT or previous site measurement). Deviations in specific frequency bands indicate:
- **Low frequency (< 1 kHz):** Core deformation, clamping issues
- **Mid frequency (1 kHz – 100 kHz):** Main winding deformation
- **High frequency (> 100 kHz):** Lead connections, tap changers, local winding buckling

---

## 10. Summary of Test Sequence

The recommended test sequence for SA commissioning is:

1. **Visual Inspection** — tank, bushings, silica gel, oil level, nameplate verification
2. **IR & PI** — all three configurations (MANDATORY before energisation)
3. **Winding Resistance** — all taps, temperature corrected
4. **TTR** — all taps, all phases
5. **Tan Delta** — GST and UST modes (if test equipment available)
6. **Oil BDV & Water Content** — sample from bottom valve (MANDATORY oil-filled)
7. **DGA** — baseline or diagnostic (MANDATORY oil-filled ≥ 500 kVA)
8. **SFRA** — post-fault or post-transport
9. **Short Circuit Impedance** — verify Vk% matches nameplate (FAT or commissioning)
10. **Protection Scheme Verification** — see Engineering Guides: CT Secondary Injection

> **Eskom / NRS 097-2 Note:** For transformers being connected to the Eskom network, submit all test results to the relevant Eskom regional office for review before energisation. Transformers ≥ 5 MVA typically require a witnessed FAT and SAT.
