# CT Secondary Injection & Testing — South African Standards

This guide covers procedures, safety requirements, and acceptance criteria for Current Transformer (CT) testing and secondary injection testing of protection schemes in South Africa. It aligns with **SANS 61869-2** (IEC 61869-2 adopted by SABS), **NRS 074** (Eskom CT specifications for network protection), and **IEC 61869-2** / **IEEE C57.13**.

> **Scope:** This guide covers LV/MV protection CTs (Class P, PX, PR) used in Eskom distribution networks, municipal MV substations, and industrial protection panels. Metering CTs (Class 0.1 – 0.5S) follow additional accuracy requirements under **NRS 057** and **SANS 62052**.

---

## 1. Introduction & Core Concepts

### What is Secondary Injection?

In high-voltage substations it is impractical — and often impossible — to inject thousands of amps through primary busbars. Secondary injection allows engineers to simulate fault conditions by injecting current directly into the CT secondary circuit.

Secondary injection serves two distinct purposes:

1. **CT Health Diagnostics:** Testing the CT core and windings (Magnetization, Winding Resistance, Ratio, Polarity) to verify the CT itself is undamaged and performing to specification.
2. **Protection Scheme Verification:** Injecting simulated fault current into the secondary terminal block to verify that all connected protection relays, instruments, and SCADA equipment operate correctly — including trip timing, pickup values, and directional elements.

### Key Terminology

| Term | Definition |
| :--- | :--- |
| Knee-Point Voltage (Vk) | Voltage at which 10% increase causes ≥50% increase in excitation current |
| Accuracy Limit Factor (ALF) | Ratio of rated accuracy limit current to rated secondary current (e.g., 20 for 5P20) |
| Rated Burden (VA) | Maximum connected load (in VA) the CT can drive while meeting accuracy class |
| Class P | General protection CT per IEC 61869-2 (e.g., 5P10, 5P20) |
| Class PX | Knee-point defined CT, no specified accuracy class — used in differential protection |
| Class PR | Low remanence flux CT — used in high-speed numerical protection |

---

> ### ⚠ CRITICAL SAFETY WARNING: OPEN-CIRCUIT HAZARD
>
> **NEVER open-circuit the secondary of an energised CT.**
>
> A CT behaves as a constant-current source. If its secondary loop is broken while primary current is flowing, the core enters deep magnetic saturation and induces **extremely high voltage** across the open terminals — potentially tens of thousands of volts.
>
> **Consequences:** Lethal electric shock, dielectric breakdown, arc flash, and explosion.
>
> **Golden Rule:** Always apply a **firm short-circuit link** across the CT secondary terminals at the test block **before** disconnecting any relay wiring. This short must remain in place throughout all wiring changes.
>
> **NRS 074 Requirement:** Single-point earthing of the CT secondary circuit must be maintained at all times. Only one earth point is permitted — typically at the LV terminal box or the marshalling kiosk.

---

## 2. Pre-Test Requirements

### 2.1 Permits & Isolation
- Obtain a valid **Permit to Work (PTW)** per OHSA Electrical Machinery Regulations.
- Confirm primary circuit is isolated, locked, and earthed (LOTO applied).
- Verify with an approved voltage detector that no voltage is present on the primary.
- For Eskom network assets: a **Network Instruction (NI)** and **Operational Switching Procedure** must be in place before any testing.

### 2.2 Documentation Required
- CT nameplate data (ratio, class, burden, Vk min for PX class)
- Wiring diagrams for the protection panel
- Previous test records (FAT / SAT from manufacturer or previous maintenance)
- Protection relay settings sheets

---

## 3. Pre-Requisite CT Health Tests

Before secondary injection into the protection relays, the CT must be verified to be healthy. The following tests are performed on the CT itself with all secondary connections **isolated from the relay panel**.

### 3.1 Insulation Resistance (IR) Test
**Standard: SANS 61869-2 / IEC 61869-2**

Tests the integrity of insulation between windings and earth.

**Procedure:**
- Apply a 500 V or 1 000 V DC Megger between:
  - Primary to Secondary (isolated)
  - Primary to Earth
  - Secondary to Earth

**Acceptance Criteria (NRS 074 / SANS 61869-2):**

| Measurement | Minimum Acceptable |
| :--- | :--- |
| Primary to Secondary | ≥ 1 000 MΩ |
| Primary to Earth | ≥ 1 000 MΩ |
| Secondary to Earth | ≥ 100 MΩ |

> Values below 100 MΩ on the secondary circuit indicate moisture ingress or insulation degradation. The CT must not be put into service until the cause is identified.

### 3.2 Winding Resistance Test
**Standard: IEC 61869-2**

Measures DC resistance of the secondary winding.

**Purpose:** Detects broken strands, loose terminals, or poor factory connections.

**Procedure:**
- Inject low DC (e.g., 100 mA) using a precision milli-ohmmeter (4-wire Kelvin method).
- Record temperature at time of measurement.
- Compare to FAT (Factory Acceptance Test) data, corrected to the same temperature.

**Acceptance Criteria:**
- Measured value within **±2%** of FAT data (temperature corrected).
- Values significantly higher than FAT indicate broken strands or loose connections.

### 3.3 Polarity Test (Flick / Battery Test)
**Standard: IEC 61869-2**

Verifies the directional relationship between P1/P2 (primary) and S1/S2 (secondary) terminals.

**Why It Matters:** A CT with reversed polarity in a differential protection scheme will cause the relay to misidentify normal load current as an internal fault — tripping the entire protected zone under full load.

**Procedure:**
1. Ensure secondary is connected to a sensitive galvanometer or multi-meter on the **mA DC range**.
2. Briefly apply a 9 V battery with positive terminal to **P1** and negative to **P2**.
3. The galvanometer/meter must deflect **positively** at S1 → S2 (current out of S1).
4. If deflection is negative: CT polarity is reversed — do not use in directional or differential schemes.

### 3.4 Ratio Test (Voltage Method)
**Standard: SANS 61869-2 / IEC 61869-2**

Verifies the CT turns ratio without injecting primary current.

**Procedure:**
1. Apply AC voltage (e.g., 230 V) to the **secondary** winding (below the Knee-Point Vk).
2. Measure the induced voltage on the **primary** terminals.
3. Calculate ratio: `Ratio = V_secondary ÷ V_primary`

**Acceptance Criteria:**
- Measured ratio within **±0.5%** to **±3.0%** of nameplate ratio (depending on accuracy class).

| CT Class | Max Ratio Error |
| :--- | :--- |
| Class 0.5 (metering) | ±0.5% |
| Class 1 (metering) | ±1.0% |
| Class 5P (protection) | ±1.0% at ALF |
| Class PX (protection) | ±0.25% at rated current |

---

## 4. Magnetization (Excitation) & Knee-Point Test
**Standard: SANS 61869-2 / IEC 61869-2 Annex 2C**

This is the **most critical** diagnostic test for protection-class CTs. It maps the magnetization (V/I) curve and locates the Knee-Point Voltage (Vk) where the core begins to saturate.

### Why Saturation Matters
During a severe through-fault, primary current may exceed the CT's rated current by 10–20× (the ALF). If the CT saturates before reaching the rated Accuracy Limit Current (= ALF × In), it stops accurately reproducing the secondary current — effectively "blinding" the protection relay during the fault it was supposed to detect.

A **Class 5P20** CT must remain within ≤5% composite error at 20× rated current. A **Class PX** CT must achieve a specified minimum Vk without exceeding a specified maximum excitation current.

### Procedure
1. Short the primary terminals firmly.
2. Apply AC voltage to the secondary using a variable transformer (variac).
3. Increase voltage slowly from zero, recording excitation current (Ie) at each voltage step.
4. Continue until clearly into saturation region (current rising steeply).
5. **Demagnetize:** Slowly reduce voltage back to zero — do not switch off abruptly. Residual magnetism significantly degrades CT performance.

### Knee-Point Definition (IEC 61869-2):
The Knee-Point Voltage (Vk) is the point on the magnetization curve where:
`A 10% increase in applied voltage causes a ≥ 50% increase in excitation current`

### Acceptance Criteria

| CT Class | Criterion |
| :--- | :--- |
| Class 5P / 10P | Derived ALF must be ≥ nameplate ALF at rated burden |
| Class PX | Vk_measured ≥ Vk_specified (nameplate minimum) |
| Class PX | Ie at Vk ≤ Ie_max specified on nameplate |
| Class PR | Remanent flux ≤ 10% of saturation flux |

> **NRS 074 Note:** Eskom requires the measured Vk to exceed the specified minimum Vk by a margin of at least **10%** for CTs in differential protection schemes.

### Demagnetization — Critical Step
After completing the magnetization test, the CT core will be partially magnetized. **Always demagnetize** by:
1. Returning the variac to maximum applied voltage briefly.
2. Slowly and continuously reducing voltage to **exactly zero**.
3. Never disconnect the test leads while voltage is still applied to the secondary.

---

## 5. Loop Burden Measurement
**Standard: IEC 61869-2**

The connected burden (cables + relay terminals + relay impedance + meters) must not exceed the CT's rated burden. If the actual burden exceeds the rated burden, the CT will saturate at a lower current than its ALF.

**Procedure:**
1. Reconnect all secondary cables to the terminal block (relay connected, CT shorted out at test block).
2. Inject the rated secondary current (1 A or 5 A) from the CT side of the test block, through the full secondary loop.
3. Measure the voltage across the entire loop.
4. Calculate: `Burden (VA) = I² × Z_loop = V_loop × I_injected`

**Acceptance Criteria:**
- Measured burden **< Rated Burden** stated on CT nameplate (e.g., 15 VA).
- Allow a margin of at least 20% (measured burden ≤ 80% of rated burden).

---

## 6. Secondary Injection into the Protection Scheme

Once the CT is verified healthy, protection scheme verification begins. This is the primary purpose of secondary injection in commissioning and maintenance.

### 6.1 Test Equipment
- Secondary Injection Test Set (e.g., Omicron CMC 356, Doble F6150, ISA DRTS)
- Multi-function protection relay test software
- Calibrated ammeter / clamp meter for verification

### 6.2 Isolation Setup at Test Block

> ⚠ **Critical procedure — do not skip:**

1. At the test block, insert a **shorting link** across the CT secondary terminals (CT side). The CT secondary is now safely shorted.
2. Insert **isolation links** on the relay side to direct your injected current towards the relay (not backwards through the CT).
3. Connect the injection test set to the relay-side terminals of the test block.

```
[Injection Test Set]
      I(+) ──────────────────────────────────────────────────┐
                                                             │
      I(-) ──┐                                              │
             │                                              │
    [CT SHORTED]    [Test Block]    [Terminal Block] ──> [Relay] ──> [Trip Output]
             │           │
         ISOLATED    ← You inject HERE (relay side) →
```

### 6.3 Overcurrent Relay Tests (IDMT / DTL)

For each protection element:

**Pickup (Is) Verification:**
- Inject current from 90% of set pickup — relay must NOT operate.
- Increase to 100% of set pickup — relay must operate (or be stable at boundary).
- Increase to 110% of set pickup — relay MUST operate.
- Record actual pickup current.
- Acceptance: Pickup within **±5%** of relay setting (or per relay manufacturer's spec).

**Inverse Time Curve Verification (IDMT):**
- Inject at 2× Is, 5× Is, and 10× Is.
- Record actual trip time using test set timer.
- Compare to relay's inverse time curve calculation.
- Acceptance: Trip times within **±5%** or ±40 ms (whichever is greater) per IEC 60255-151.

**Standard IDMT Curves used in SA:**
- **Standard Inverse (SI):** Most common in distribution networks
- **Very Inverse (VI):** Used where grading margins are tight
- **Extremely Inverse (EI):** Used where fuse coordination is required

### 6.4 Earth Fault Element Tests
- Test with balanced three-phase injection to confirm earth fault element does NOT operate.
- Inject single-phase current into the earth fault input — verify pickup and time.
- Verify that the high-set instantaneous element (50N) operates at the correct current.

### 6.5 Differential Protection Tests (Transformer / Busbar / Feeder)
- Inject equal currents into restraint windings — relay must NOT operate (through-fault condition).
- Inject operate current (differential current) — relay must operate within specified time.
- Verify harmonic restraint (2nd harmonic blocking) — inject at 15% 2nd harmonic, relay must be restrained.
- Verify inrush blocking is active.

---

## 7. Post-Test Requirements

After completing all tests:

1. **Remove all shorts and isolation links** at the test block — verify CT secondary is correctly re-connected to the relay.
2. **Restore single-point earth** on the CT secondary circuit.
3. **Restore all relay settings** — verify against the approved settings sheet.
4. **Record all results** in the commissioning or maintenance test report.
5. **Functional check:** With the relay in service mode, perform a functional trip test of the trip coil circuit to confirm the output contacts and trip coil are healthy.
6. **Obtain sign-off** from the responsible engineer before re-energising.

> **NRS 097 / Eskom Requirement:** All protection scheme test results for equipment on the Eskom network must be submitted to the Protection Engineer for review and approval before the protection is placed in service.

---

## 8. Summary

Secondary injection testing is the cornerstone of commissioning and maintaining CT-based protection schemes. The two-phase approach — verifying the CT itself first, then verifying the protection scheme — ensures that any anomaly is correctly attributed to either the measuring transformer or the relay system.

**Key rules for every test:**
- **Never open-circuit an energised CT secondary** — always short first.
- **Maintain single-point earthing** throughout the entire test.
- **Demagnetize after every magnetization test** by slowly reducing to zero.
- **Document everything** — results must be traceable and reproducible.
- For Eskom network assets: **no protection may be placed in service without a Protection Engineer's sign-off.**
