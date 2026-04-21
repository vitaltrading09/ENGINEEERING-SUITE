# SANS 10142-1 — Electrical Installation Requirements (South Africa)

This guide summarises key requirements from **SANS 10142-1:2020** (Wiring of premises — Low-voltage installations) with practical guidance for South African electrical installations. This is the primary standard governing all LV electrical installations in South Africa, enforced under the **Electrical Installation Regulations, 2009** (promulgated under the OHS Act 85 of 1993).

---

## 1. Legal Framework & Compliance

### 1.1 Who Must Comply
- Every electrical installation in South Africa must comply with SANS 10142-1.
- All work must be performed by a **registered person** under the Electrical Installation Regulations:
  - **Master Installation Electrician (MIE)** — may certify any installation.
  - **Installation Electrician (IE)** — may certify single-phase and three-phase LV installations up to the limit of their registration.
  - **Registered Persons (RP)** — limited to specific categories.

### 1.2 Certificate of Compliance (CoC)
A **Certificate of Compliance** must be issued by a registered electrician for:
- All new electrical installations.
- Any extension or alteration to an existing installation.
- Change of ownership of property (a valid CoC is required for property transfer).

The CoC must be submitted to the **Department of Employment and Labour** and to the **supply authority** (Eskom / municipality).

> **Validity:** A CoC is valid for 2 years or until any addition or alteration is made to the installation, whichever occurs first.

---

## 2. Protection Against Electric Shock — SANS 10142-1 Chapter 4

### 2.1 Basic Protection (Direct Contact)
Protection against direct contact with live parts is achieved by:
- **Insulation** of live conductors (correct cable rating).
- **Barriers and enclosures** (minimum IP2X or IPXXB — prevents finger contact).
- **Obstacles** (for authorised persons areas only).
- **Placing out of reach** (overhead lines, etc.).

### 2.2 Fault Protection (Indirect Contact)
Protection against indirect contact (touching metalwork that has become live due to a fault) is achieved by:
- **Protective earthing** — all exposed conductive parts bonded to earth.
- **Automatic disconnection of supply (ADS)** — faults must cause disconnection within the times specified in SANS 10142-1 Table 41A.

### 2.3 ADS Disconnection Times (SANS 10142-1 Table 41A)

| System | 230 V circuits | 400 V & above |
| :--- | :--- | :--- |
| TN system | 0.4 s | 0.2 s |
| TT system | 0.2 s | 0.07 s |

> For distribution circuits (final circuits > 32 A), a 5-second disconnection time is permitted if the earth loop impedance is verified to be within limits.

### 2.4 Earthing System Types in SA
South Africa predominantly uses the **TN-C-S (PME)** earthing system for municipal/Eskom LV distribution:
- **TN-C** from the transformer to the last pole/kiosk (combined PEN conductor).
- **TN-S** within the customer's premises (separate N and PE from the point of supply).

The supply authority connects PEN to earth at the service entrance — customers must NOT earth the neutral within their premises in a TN-C-S system.

**TT system** is used where the supply authority does not provide a protective earth — common in rural areas. Requires an RCD with trip current: `IΔn × RA ≤ 50 V` where RA = earth electrode resistance.

---

## 3. Overcurrent Protection — SANS 10142-1 §5.3

### 3.1 Types of Overcurrent Protection
- **Overload protection:** Protects cables from sustained overload. The device must operate before the cable reaches its thermal limit.
- **Short circuit protection:** Must operate within the thermal withstand time of the cable.

### 3.2 Overload Protection Conditions (SANS 10142-1 §5.3.3)

For a protective device to provide overload protection:

`Ib ≤ In ≤ Iz`   and   `I2 ≤ 1.45 × Iz`

Where:
- **Ib** = design current of the circuit (A)
- **In** = rated current of the protective device (A)
- **Iz** = current carrying capacity of the cable (A) — derated for all conditions
- **I2** = current that causes effective operation of the device within the conventional time (typically 1.45 × In for MCBs)

### 3.3 Short Circuit Protection
The protective device must disconnect the fault before the cable exceeds its short-circuit temperature. This is verified by:

`I²t ≤ k²S²`

Where:
- **I** = fault current (A)
- **t** = disconnection time (s)
- **k** = material constant (115 for PVC/copper, 143 for XLPE/copper)
- **S** = conductor cross section (mm²)

Use the Short Circuit Current calculator in this suite to determine Isc, then verify the device's I²t characteristic.

---

## 4. Distribution Boards — SANS 10142-1 §5.7

### 4.1 General Requirements
- Every electrical installation must have a **main distribution board (MDB)** at or near the point of supply.
- Sub-distribution boards (SDBs) are permitted downstream of the MDB.
- **Isolation:** A main switch or circuit breaker capable of isolating all live conductors (including neutral in TT/IT systems) must be provided at the MDB.

### 4.2 Busbar & Wiring Requirements
- All busbars and connections must be rated for the maximum prospective short circuit current — use the Short Circuit Current calculator to verify.
- Trunking and cable management within DB must maintain segregation between LV and ELV circuits (if applicable).
- All wiring terminations must be clearly labelled and correspond to the circuit schedule (hard copy must be displayed inside the DB door).

### 4.3 RCD Requirements (SANS 10142-1 §5.7)

| Circuit Type | RCD Requirement |
| :--- | :--- |
| All socket outlets ≤ 20 A (TT system) | 30 mA RCD mandatory |
| Socket outlets in wet locations (bathrooms, kitchens) | 30 mA RCD mandatory |
| Outdoor socket outlets | 30 mA RCD mandatory |
| Circuits supplying luminaires in bathrooms (Zone 1) | 30 mA RCD mandatory |
| Agricultural / horticultural installations | 30 mA RCD mandatory |
| Swimming pool circuits | 30 mA RCD mandatory |

> SANS 10142-1:2020 now recommends (and in many cases requires) RCD protection for all socket outlet circuits in new installations, regardless of system type. This aligns with SANS/IEC practice and significantly reduces shock risk.

---

## 5. Voltage Drop — SANS 10142-1 §6.2.7

### Maximum Permitted Voltage Drop
- **5% of nominal supply voltage** from the origin of the installation to any point of utilisation.
- For a 230 V single-phase supply: max Vd = 11.5 V
- For a 400 V three-phase supply: max Vd = 20 V (L-L)

> Use the **Voltage Drop Calculator** in this suite to verify compliance. SANS 10142-1 §6.2.7 uses the mV/A/m method (Table 6) for tabulated calculations, or the impedance method for more detailed analysis.

### Practical Guideline
For long distribution cables, limit voltage drop to **2.5%** at the sub-board and **2.5%** for the final circuit wiring to allow for cumulative effects in large installations.

---

## 6. Cable Selection — SANS 10142-1 §5.2

### 6.1 Current Carrying Capacity
All cable sizes must be selected such that the derated CCC (Iz) ≥ design current (Ib). Use the **Cable CCC & Derating calculator** in this suite with the appropriate:
- Insulation type (PVC or XLPE)
- Installation method (SANS 10142-1 Tables 1–5)
- Ambient temperature correction (Table 3)
- Grouping correction (Table 4)

### 6.2 Minimum Conductor Sizes (SANS 10142-1 §5.2.5)

| Application | Minimum Size |
| :--- | :--- |
| Fixed wiring (general) | 1.5 mm² copper |
| Socket outlet circuits | 2.5 mm² copper |
| Lighting circuits | 1.0 mm² copper (1.5 mm² recommended) |
| Earth conductors (to 35 mm² phase) | Same size as phase conductor |
| Earth conductors (phase > 35 mm²) | ≥ 50% of phase conductor size |

### 6.3 Aluminium Conductors
Aluminium conductors are permitted in South Africa for:
- Main cables and sub-mains (typically ≥ 16 mm²).
- Not permitted for final circuits or flexible cables.
- Requires anti-oxidant compound at all terminations.
- Never mix aluminium and copper in the same terminal without an approved bimetallic connector.

---

## 7. Special Locations — SANS 10142-1 Chapter 7

### 7.1 Bathrooms & Wet Areas (Location 701)
- Zone 0 (inside the bath/shower basin): Only SELV 12 V AC or 30 V DC permitted. No socket outlets.
- Zone 1 (above the bath/shower to 2.25 m height): IPX4 minimum. Only SELV or circuits protected by 30 mA RCD.
- Zone 2 (0.6 m outside zone 1): IPX4 minimum. Socket outlets only if protected by 30 mA RCD and shaver supply unit (isolation transformer).
- Supplementary bonding required between all exposed metalwork (taps, pipes, towel rails, heating elements).

### 7.2 Swimming Pools & Fountains (Location 702)
- Zone 0 (inside the pool): Only SELV ≤ 12 V AC / 30 V DC. Transformers outside Zone 0.
- Zone 1 (within 2 m of pool edge, up to 2.5 m height): Only SELV, 30 mA RCD-protected circuits. IPX5.
- Equipotential bonding of all metalwork mandatory.

### 7.3 Agricultural & Horticultural Premises (Location 705)
- All socket outlets: 30 mA RCD protection.
- Wiring: mechanical protection required (conduit or armoured cable) against damage by animals and equipment.
- Consideration for corrosive environments (livestock areas).

---

## 8. Inspection & Testing — SANS 10142-1 Chapter 6

All electrical installations must be tested before issuing a CoC. Minimum tests:

1. **Continuity of protective conductors** — verify all earth conductors are continuous and correctly terminated.
2. **Insulation resistance** — verify IR between live conductors and between live and earth (minimum 1 MΩ per circuit at 500 V DC for standard LV circuits).
3. **Polarity** — verify all single-pole devices (switches, fuses, MCBs) are in the phase conductor only, never the neutral.
4. **Earth fault loop impedance (Zs)** — verify ADS will operate within the required disconnection time.
5. **RCD operation** — verify trip time and trip current with an approved RCD tester (30 mA RCD must trip within 300 ms at rated current, within 40 ms at 5× rated current).
6. **Functional testing** — all equipment must function correctly after testing.

> All test results must be recorded on the CoC form or in a separate test schedule attached to the CoC.

---

## 9. Reference Quick-Check Summary

| Check | Requirement | Standard Reference |
| :--- | :--- | :--- |
| Voltage drop | ≤ 5% of Vn | §6.2.7 |
| Cable CCC | Ib ≤ In ≤ Iz | §5.3.3 |
| RCD trip current (standard) | ≤ 30 mA | §5.7 |
| RCD trip time at IΔn | ≤ 300 ms | §5.7 |
| IR (per circuit) | ≥ 1 MΩ | Chapter 6 |
| Min conductor size (final circuit) | 1.5 mm² Cu | §5.2.5 |
| Min socket outlet circuit size | 2.5 mm² Cu | §5.2.5 |
| ADS disconnection (TN, 230 V) | ≤ 0.4 s | Table 41A |
| CoC validity | 2 years | Electrical Installation Regulations |
