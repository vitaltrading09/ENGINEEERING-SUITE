# Transformer Testing Procedures

These procedures cover routine, acceptance and repair testing of distribution and power transformers
in accordance with **SANS 780**, **SANS 60076 (IEC 60076)** and **Transformco Work Procedures (WP 19 – WP 52)**.
All tests must be witnessed and signed off by an approved Tester. Results are recorded on the
Transformer Test Certificate and Oil Test Certificate issued with every completed unit.

---

## 1. Routine Test Schedule

The tests required depend on the stage of manufacture or repair.


### a) Tests at Receiving of Transformer (Repair)

| Test | Work Procedure |
|---|---|
| Insulation Resistance (Megger) | WP 31 |
| Ratio Test | WP 32 |
| Positive Sequence Impedance | WP 33 |
| Vector Group Test | WP 34 |

### b) Tests on New Windings & Core (Pre-Test)

| Test | Work Procedure |
|---|---|
| Insulation Resistance (Megger) | WP 31 |
| Ratio Test | WP 32 |
| Positive Sequence Impedance | WP 33 |
| Vector Group Test | WP 34 |

### c) Final Tests on Completed Transformer

| Test | Work Procedure |
|---|---|
| Insulation Resistance (Megger) | WP 31 |
| Ratio Test | WP 32 |
| Winding Resistance | WP 35 |
| Positive Sequence Impedance | WP 33 |
| Vector Group Test | WP 34 |
| Induced Over Voltage Withstand | WP 36 |
| Separate Source Voltage Withstand | WP 37 |
| Load & No Load Loss | WP 38 |
| Heat Run *(New Transformers Only — if required by Customer)* | WP 67 |

> Any failure or irregular test result must be reported immediately to the Designer, Internal Sales Manager, or Winding Foreman.

---

## 2. Mini Sub-Station Test Schedule (WP 24)


The Switchgear Supplier provides a MV Switchgear Test Certificate for each unit supplied.
MV Switchgear Test Certificates are kept by the Quality Representative or Technical Director for record.
The Tester will conduct an Insulation Resistance Test on the MV Switchgear between each Phase and Earth,
and between Phases on the Low Voltage Panel to ensure no breakdown of insulation is evident.

### a) Pre-Tests on Transformer Windings & Core

| Test | Work Procedure |
|---|---|
| Insulation Resistance (Megger) | WP 31 |
| Turns Ratio Test | WP 32 |
| Winding Resistance Test | WP 35 |
| Vector Group Test | WP 34 |

### b) Final Tests on Completed Transformer

| Test | Work Procedure |
|---|---|
| Insulation Resistance | WP 31 |
| Ratio Test | WP 32 |
| Winding Resistance | WP 35 |
| Positive Sequence Impedance | WP 33 |
| Vector Group Test | WP 34 |
| Induced Over Voltage | WP 36 |
| Separate Source Voltage Withstand | WP 37 |
| Load & No-Load Loss Test | WP 38 |

---

## 3. Safety Prerequisites — Non-Negotiable

Before any test equipment is connected:

- **De-energize & Isolate:** Disconnect all HV and LV sources. Confirm isolation with an approved voltage detector.
- **Earth All Windings:** Apply earthing clamps to HV terminals, LV terminals and the tank before touching any component. Discharge any residual charge — large transformers hold significant capacitive energy.
- **Discharge Residual Charge:** Before measuring IR, earth the components under test for a few seconds to ensure any residual electrical charge is completely discharged. A residual charge will give incorrect IR readings.
- **Lock Out / Tag Out (LOTO):** Apply padlocks and danger tags per your site LOTO procedure. Retain the key.
- **PPE:** Rubber insulating gloves (rated for the voltage class), arc flash face shield, and flame-resistant clothing required for all HV and LV work.
- **Open Circuit Hazard:** An open circuit during Winding Resistance testing is extremely dangerous — it can cause Flash-Over in the Transformer, damage instruments and harm the Tester.
- **Gas Check (Oil Transformers):** Check for combustible gas accumulation before opening inspection covers on oil-filled units.

---

## 4. WP 31 — Insulation Resistance (Megger) Test


### Purpose
Measures leakage current through the insulation system to detect moisture ingress, surface contamination,
or thermal aging before a failure occurs. Uses a high-voltage DC Insulation Resistance Tester (Megger)
capable of testing up to 10 kV DC.

### Test Configurations
The following combinations are tested between Earth and individual components:

- Primary (HV) Coils and Earth
- Secondary (LV) Coils and Earth
- Primary (HV) Coils and Secondary (LV) Coils
- Core Clamps and Earth
- Core to Core Clamps
- Secondary LV Connections

### Megger Voltage Settings

| Transformer Rated Voltage | Megger Voltage Setting |
|---|---|
| ≤ 1 000 V | 2.5 kV |
| 1 000 V | 2.5 kV |
| 3 300 V | 5 kV |
| 6 600 V | 10 kV |
| 11 000 V | 10 kV |
| 22 000 V | 2.5 kV |
| 33 000 V | 2.5 kV |

### Minimum Acceptable IR Values

| Component | Minimum IR |
|---|---|
| New LV Coil to Earth | 500 MΩ |
| New HV Coil to Earth | 500 MΩ |
| Between new LV and HV Coils | 500 MΩ |
| Overhauled LV Coils | 500 MΩ |
| Overhauled HV Coils | 500 MΩ |
| Between LV & HV Overhauled Coils | 500 MΩ |
| Between Core and Core Clamps | 400 MΩ |

### Procedure
1. Ensure all windings are earthed and residual charge is discharged before connecting the Megger.
2. Apply test voltage for no more than **60 seconds** per measurement.
3. Measure the Temperature of the Winding and record on the Transformer Test Report.
4. Test Earth connection integrity when testing HV and LV Coils to ensure a proper Earth Connection.
5. Record all results on the Transformer Test Report.

### Failure Interpretation

| IR Reading | Interpretation |
|---|---|
| 0 MΩ (Zero) | Complete breakdown or short to earth exists |
| < 100 MΩ | Insulation is wet, or leakage/breakdown to earth is present |
| < Minimum specified | Investigate before energising |

> **Wet Coils / Core:** If the Core or Coils are wet, place in the Baking Oven at **100°C** for 12 to 18 hours, or until the IR fully complies with specified requirements. Re-test and record results after drying.

---

## 5. WP 32 — Turns Ratio Test


### Purpose
Validates that the actual turns ratio matches the nameplate, confirms tap changer operation on all taps,
and verifies the Vector Group of the Winding.

### Procedure
1. Connect the Ratiometer in the Test Bay to the **H1, H2 and H3 leads** of the Primary (HV) Windings.
2. The **H0 lead** connection is only applicable when a Neutral is on the Primary Winding.
3. Connect **X1, X2 and X3 leads** to the Secondary Windings, and **X0** to the Neutral Bar of the Secondary Coils.
4. Enter the Tap readings on the Ratiometer and press **"START"**.
5. Switch ON the Ratiometer and press "START".
6. Record readings from the Ratiometer on the Transformer Test Report.
7. Once completed, compare Ratio Test results with the calculated results from the Designer and Winding Specification.
8. When the Transformer has more than one tapping, measure the Voltage Ratio relative to each tapping.
9. The Vector Group of the Winding will be confirmed by the Ratiometer.
10. Record Ratio Test results on the Transformer Test Certificate.
11. When required, a copy of the Ratiometer Results will be printed.

### Acceptance Criteria
- A difference of **≤ 0.5%** between the Measured value and the Calculated value is acceptable.
- The Vector Group of the Winding must match the Design Vector Diagram.

---

## 6. WP 33 — Positive Sequence Impedance Test (Copper Loss)


### Purpose
Measures the Short Circuit Impedance (Vk%) and Load Loss (Copper Loss) of the Transformer.
The load-loss is made up of I²R losses in the winding plus all stray losses due to eddy currents and
leakage flux between windings when the Transformer is on full working load.

### Procedure
1. Connect Test cable leads to the **Primary (HV) side** of the Transformer.
2. Short the **Secondary (LV) side** connections (excluding Neutral) with drilled copper bars, cables or flexible links.
   - The cross-section of the short-circuit link must be able to carry the current; contacts must be tight and secured.
3. Switch Test Bench **"ON"** and select the circuit for the 3 Phase Variac and Transformer.
4. Calculate Full Load Current on the Primary (HV) side and Secondary (LV) side.
5. Determine the Test Voltages required (refer to table below).
6. Monitor voltage and current on the **HV (Primary) side** of the Transformer and record Volts and Amps.
7. Switch **"OFF"** supply to Transformer.
8. Use Variac to increase current up to Full Load Current.
9. Record the Voltage and Watt readings of the Transformer on the Power Analyser.
10. Record the Current readings on the LV (Secondary) short-circuit side of the Transformer.
11. Calculate the Impedance using the formulae below.
12. Record results on the Transformer Test Report.

### Test Voltages

| Transformer Rated Voltage | Test Voltage |
|---|---|
| 1 000 V | 50 V |
| 3 000 V | 150 V |
| 6 000 V | 280 V |
| 11 000 V | 400 V |
| 22 000 V | 800 V |

### Impedance Calculation

**3-Phase:**
```
Z (%) = (VP × kV² × √3) / (IP × VA × 100)
```

**1-Phase:**
```
Z (%) = (VP × kV²) / (IP × VA × 100)
```

Where:
- `VP` = Primary Test Voltage in kV
- `IP` = Primary Test Current
- `kV` = No Load Voltage in kV

### Acceptance Criteria (SANS 780)

| Rated Power P (kVA) | Impedance Range (%) |
|---|---|
| P < 200 | 3.0 – 4.5 |
| 200 < P < 500 | 4.0 – 5.0 |
| 500 < P < 1 250 | 4.5 – 5.5 |
| 1 250 < P < 3 150 | 5.0 – 6.5 |

> The Load Loss at rated Current must be corrected to a reference Temperature of **75°C**.

---

## 7. WP 34 — Vector Group Test


### Purpose
The Vector Group Detection Test is done simultaneously with the Turns Ratio Test to determine whether
the transformer's measured results match the Design Vector Diagram.

### Procedure
1. Short circuit the **"A" phase** on the Secondary (HV) side with the **"a" phase** on the Primary (LV) side
   by turning the Selector Switch.
2. Connect the Connection leads from the Test Panel on the **Primary (HV) side** of the Transformer to be tested.
3. Connect the leads from the Multimeter to **S1 and S2 Connectors** on the Test Panel — this provides a Voltage
   Output of **400 volts**.
4. Take Voltage readings as required from the Multimeter and record.
5. Measure the Voltages between Secondary and Primary Terminals of the Transformer:
   - A and b
   - B and b
   - C and b
   - B and c
   - C and b
6. Use the readings obtained to draw up the Vector Diagram.
7. Compare the drawn-up Vector Diagram with the Design Vector Diagram.
8. Once completed with the Vector Group Test, switch off the supply and remove the Multimeter.
9. Always adhere to all Safety standards and requirements when working with Live equipment.

---

## 8. WP 35 — Winding Resistance Test


### Purpose
Measures the DC resistance of Primary and Secondary Windings to identify loose connections, broken strands,
or poor contacts. Uses a calibrated Micro Ohm Resistance Meter.

### Procedure
1. Use a **calibrated Micro Ohm Resistance Meter** to conduct the Phase Resistance Test on the Primary and
   Secondary Windings.
2. **Before** conducting the Resistance Test, **short out the phases** of the Primary and Secondary Windings
   — a residual charge present in the windings can damage the Resistance Meter.
3. Make sure all connections at the Winding terminals are properly and securely made.
4. Measure and record the **Ambient Temperature** on the Transformer Test Report.
5. When measuring Resistance, always wait until the Resistance Meter has **discharged the leads** before
   changing to the next phase.
6. When taking measurements, wait until the Resistance measurement has **stabilised for approximately ±30 seconds**.
7. Measure the Resistance (Ω) on all three **Primary (HV) Windings** and record on the Transformer Test Report.
8. Measure the Resistance (Ω) on all three **Secondary (LV) Windings** in the case of a Three Phase Transformer,
   and both coils in the case of a Single Phase Transformer.
9. Record the Resistance results on the Transformer Test Report.

> **WARNING:** An Open Circuit is extremely dangerous — it can cause Flash-Over in the Transformer, damage the instrument and harm the Tester. Never break the current circuit while the meter is injecting.

---

## 9. WP 36 — Induced Over Voltage Withstand Test (High Frequency Test)


### Purpose
Verifies that the inter-turn and inter-layer insulation of the coils is sound and the design specification
is correct by applying **twice the rated voltage** at increased frequency to the Secondary (LV) terminals.

### Test Voltages

| System Voltage | Test Voltage (New) | Test Voltage (Repeated — 75%) |
|---|---|---|
| 2.2 kV | 4.4 kV | 3.3 kV |
| 3.3 kV | 6.6 kV | 5.0 kV |
| 6.6 kV | 13 kV | 9.75 kV |
| 11 kV | 22 kV | 16.5 kV |
| 22 kV | 44 kV | 33 kV |

### Procedure
1. Apply the alternating test voltage to the **Secondary (LV) terminals** of the Transformer.
2. The **Primary (HV) Terminals** will be open-circuited.
3. A voltage of **twice the rated value** will be induced in the Secondary (LV) winding.
4. To avoid excessive currents during the Test, the frequency must be **at least twice** the normal operating
   frequency — use **150 Hz** (achieved via Motor and Generator set).
5. Start the Induced Over Voltage Withstand Test by bolting supply leads from the Test Panel to the selected terminals.
6. Switch **"ON"** supply and use the Variac to bring the Supply Voltage to **twice the rated voltage** for
   New Windings and maintain for **40 seconds at 150 Hz**.
7. **Repeated Transformers** (previously tested): Test Voltage shall not exceed **75%** of the rated Voltage
   unless otherwise agreed by the Customer.
8. Watch the Ammeter for signs of **excessive Current** — this indicates the insulation is breaking down before
   the current is large enough to trip the breaker. Switch supply **"OFF"** immediately if current increases abnormally.
9. Record the Test Voltage and Time on the Transformer Test Report.
10. When using a frequency higher than 100 Hz, the testing time will be reduced proportionally.
11. After the test, use the Variac to **rapidly bring the Voltage down to less than one third** of the Test Voltage
    before switching **"OFF"**.
12. The Transformer has **Passed** the Induced Overvoltage Withstand Test if **no collapse of the Test Voltage**
    occurs during the test period.

---

## 10. WP 37 — Separate Source Voltage Withstand Test (Pressure Test)


### Purpose
Tests the insulation integrity between each winding and earth by applying a separate AC voltage source
to each winding in turn while the remaining windings, core, frame and tank are earthed.

### Test Voltages

| System Voltage | Test Voltage | Test Voltage (Repeated — 75%) |
|---|---|---|
| ≤ 1 000 V | 2.5 kV | 1.9 kV |
| 3.3 kV | 16 kV | 12 kV |
| 6.6 kV | 22 kV | 16.5 kV |
| 11 kV | 28 kV | 21 kV |
| 22 kV | 50 kV | 37.5 kV |
| 33 kV | 70 kV | 52.5 kV |

### Procedure
1. The test is conducted by applying the Test Voltage to **each winding in turn**, while the remaining windings,
   core, frame and tank of the Transformer are **connected together and earthed**.
2. Single Phase voltage is obtained from a separate source using a Test Winding ratio **1000:1** of HV Transformer
   (400 V → 100 000 V).
3. A Multimeter is connected to the HV side to monitor voltage (reading = multimeter reading ÷ kV Divider Ratio).
4. **To test the HV side:** Wire all HV Terminals together (flash test). All LV terminals wired together and
   tightened to the tank Earthing Bolt.
5. **To test the LV side:** Short out HV terminals and connect to earth.
6. Connect the earth side of the voltage transformer to the earth bolt on the tank.
7. Use copper wire to connect the HV terminal of the high voltage transformer to the required terminal of the
   Transformer under test.
8. Use the Variac to increase the Voltage to the required Test Voltage.
9. Maintain the **Test Voltage for 60 seconds**.
10. After 60 seconds, **rapidly decrease** the Test Voltage to Zero using the Variac.
11. Switch off the instrument or allow the supply contact breaker to trip.
12. Any **breakdown of insulation** will cause the Test Instrument or supply contact breaker to trip.
13. When conducting Repeated tests, the Test Voltage shall not exceed **75%** of the original Test Voltage
    unless otherwise agreed by the Customer.

> **SAFETY:** The Test Transformer Supply Point must **always be Earthed** whenever Bridging or Un-bridging the Test Leads. Adhere to all safety requirements at all times.

---

## 11. WP 38 — Load & No Load Loss Test


### Purpose
Measures the No Load Loss (Iron Loss) and Full Load Loss (Copper Loss) of the Transformer.
Results are compared against SANS 780 specification limits.

### Procedure

**No Load Loss (Iron Loss):**
1. Ensure the Test Bench is switched **"OFF"**.
2. Connect Red, White and Blue leads to the **Secondary (LV) Bushings** of the Transformer.
3. Supply **Rated Voltage** to the Terminals on the Secondary (LV) side of the Transformer.
4. **Leave the HV Connections Open.**
5. Switch Supply **"On"** from the Main Test Panel.
6. Record No Load Loss Test Results — Volts, Current and Watts on the Transformer Test Report.

**Full Load Loss (Copper Loss):**
7. Fit the Supply Leads to the **HV Terminals**.
8. On the Secondary (LV) side, **Short Out Terminals** with Copper Busbars or Copper Straps.
9. Apply at least **50%** of the Rated Current (HV Current) to the HV Terminals from the Test Panel.
10. Measure and record Losses, Volts, Current and Watts on the Transformer Test Report.
11. Calculate the Impedance of the Transformer and refer to the Table.
12. Compare the No Load and Full Load Losses to the **SANS 780 Specification**.

### Impedance Voltage Range at Principal Tapping (SANS 780)

| Rated Power P (kVA) | Impedance Range (%) |
|---|---|
| P < 200 | 3.0 – 4.5 |
| 200 < P < 500 | 4.0 – 5.0 |
| 500 < P < 1 250 | 4.5 – 5.5 |
| 1 250 < P < 3 150 | 5.0 – 6.5 |

### Acceptance Criteria
- Permissible Full Load Losses and No Load Losses must **not exceed 15%** of specified values (SANS 780).
- Full Load Losses and No Load Losses **combined must not exceed 10%** of Total Losses.

---

## 12. WP 52 — Insulation Resistance Temperature Correction to 40°C


### Purpose
When the Winding Temperature differs from 40°C, the measured IR value must be corrected to 40°C
for comparison against standard minimum values.

### Correction Formula

```
Rc = Kt × Rt
```

Where:
- `Rc` = Insulation Resistance corrected to 40°C (MΩ)
- `Rt` = Measured Insulation Resistance at temperature t°C (MΩ)
- `Kt` = Insulation Resistance temperature coefficient at t°C from SANS 780

### Minimum Required IR Value

```
Rm = (1 + k) MΩ
```

Where:
- `Rm` = Recommended minimum insulation resistance at 40°C (MΩ)
- `k`  = Ratio of rated transformer voltage (in volts) to 1 000, as a number

**Example Calculation — 33 kV Transformer:**
```
k  = 33 000 / 1 000 = 33
Rm = (1 + 33) MΩ = 34 MΩ
```

> **Note:** For insulation in good condition, IR readings of 10 to over 100 times the value of the recommended minimum Rm are not uncommon in practice. A reading just above Rm should be investigated.

---

## 13. Typical Transformer Test Specification

The following is extracted from a typical customer Transformer Specification (Inland unit):


| Parameter | Value |
|---|---|
| Temperature Rise | 60 / 65°C |
| Ambient Temperature | 40°C |
| Insulation Class | A @ 105°C |
| Altitude (ASL) max | 1 800 m |
| Environmental Finish | Inland |

### Required Tests

| Test | Required |
|---|---|
| Insulation Resistance Test | Yes |
| Voltage Ratio & Polarity Test | Yes |
| Winding Resistance | Yes |
| Short Circuit Impedance & Load Loss (Copper Loss) | Yes |
| No Load Loss & Current (Iron Loss) | Yes |
| Di-electric Routine Tests (SANS 60076) | Yes |
| Separate Source AC Withstand Voltage (Pressure Test) | Yes |
| Induced Overvoltage Withstand (High Frequency Test) | Yes |

### Documents Issued with Completed Unit

| Document | Issued |
|---|---|
| General Arrangement Drawing | Yes |
| Transformer Test Certificate | Yes |
| Oil Test Certificate | Yes |
