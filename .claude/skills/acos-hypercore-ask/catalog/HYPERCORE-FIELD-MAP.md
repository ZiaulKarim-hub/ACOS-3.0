# Hypercore Field Map

_Browsable index of the askable numbers & facts in Hypercore, by domain → block._  
_Generated 2026-06-26 from live introspection + probe. Machine source: `hypercore-catalog.yaml`._

## Access reality

| Domain | Root type | Access |
|---|---|---|
| Loan | `Loan` | RELIABLE — loans(filter:{searchString}){ pageItems{ … summary{…} } } |
| Investor position (LoanFunding) | `LoanFunding` | RELIABLE — loanFundings 2-step (assetId→loanFundingId); dual-filter 500s |
| Funding entity / investor (portfolio) | `FundingEntity` | RELIABLE — fundingEntities(filter:{searchString}){ pageItems{…} } |
| Borrower (ClientExtended) | `ClientExtended` | DEGRADED — clients resolver HTTP 500 (2026-06-26); schema-mapped, probe deferred |
| Equity | `Equity` | FORBIDDEN — equities resolver HTTP 403 (out of read-scope); schema-mapped only |

## Loan

- Root: `Loan` · RELIABLE — loans(filter:{searchString}){ pageItems{ … summary{…} } }
- Probe entity: `{"id": "134", "name": "Beehive Waldorff"}`
- 1422 askable value fields shown (707 bool/text fields in YAML only)

### `_direct`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `annualCompoundingInterestRate` | rate | None | annual compounding interest rate — PERCENT not fraction |
| `annualInterestRate` | rate | 15 | **annual interest rate** — PERCENT not fraction (example 15 = 15%); do not divide by 100 again |
| `approvalDate` | date | 2024-02-09 | approval date |
| `baseCurrency` | enum | USD | base currency |
| `closingDate` | date | None | closing date — Often null; contractClosingDate is the contractual variant |
| `commitment` | money | 30,000,000 | **total commitment** — This is the headline commitment; terms[].approvedPrincipal/proposedPrincipal carry the same figure per-term version \| Headline commitment is duplicated as terms[].approvedPrincipal/proposedPrincipal per term version — the same money, not additive. Use commitment OR a single chosen term, never both summed. |
| `contractClosingDate` | date | None | contract closing date |
| `currency` | enum | USD | loan currency |
| `duesCalculationMethod` | enum | AfterDisbursement | dues calculation method |
| `endDate` | date | 2025-08-15 | **loan end date** — Contractual end; scheduleEndDate/scheduleExpectedEndDate are computed schedule horizons |
| `fileEntriesCount` | count | 0 | document count |
| `lifeCycle` | enum | Defaulted | **loan life-cycle stage** — LoanLifeCycle enum (Active/Defaulted/Repaid/...); this is where default shows, not status |
| `repaymentStrategy[]` | enum | Penalties | repayment waterfall order — InstallmentComponentType enum list (e.g. Penalties first); order matters |
| `scheduleEndDate` | date | 2026-06-26 | schedule end date — Computed schedule horizon (example == today's date for a defaulted loan); not the contractual maturity |
| `scheduleExpectedEndDate` | date | 2026-05-20 | expected schedule end date |
| `startDate` | date | 2024-02-09 | **loan start date** |
| `status` | enum | Active | **loan status** — LoanStatusEnum (e.g. Active); distinct from lifeCycle which carries Defaulted/Repaid |
| `submittedOnDate` | date | 2024-02-09 | submitted-on date |

### `agingAnalysis`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `agingAnalysis.cohorts[].numberOfDays` | count | 0 | **aging bucket days** — Bucket boundary in days (e.g. 0/30/60/90) |
| `agingAnalysis.cohorts[].total.accruedCompoundingInterest` | money | None |  |
| `agingAnalysis.cohorts[].total.compoundingInterest` | money | 0 |  |
| `agingAnalysis.cohorts[].total.fees[].amount` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.fees[].compoundingAmount` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.fees[].periodCharge` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.indexedPrincipal` | money | None |  |
| `agingAnalysis.cohorts[].total.interest` | money | 462,500 | aging bucket interest |
| `agingAnalysis.cohorts[].total.penalties[].amount` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.penalties[].compoundingAmount` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.penalties[].periodCharge` | money | (empty_list) |  |
| `agingAnalysis.cohorts[].total.principal` | money | 0 | aging bucket principal |
| `agingAnalysis.cohorts[].total.total` | money | 1,905,062.20 | **aging bucket total** |
| `agingAnalysis.cohorts[].total.totalFees` | money | 250,771.18 |  |
| `agingAnalysis.cohorts[].total.totalPenalties` | money | 1,191,791.02 | aging bucket penalties |
| `agingAnalysis.cohorts[].total.totalTaxes` | money | 0 |  |
| `agingAnalysis.cohorts[].total.totalWithTaxes` | money | 1,905,062.20 |  |
| `agingAnalysis.total.accruedCompoundingInterest` | money | None |  |
| `agingAnalysis.total.compoundingInterest` | money | 0 |  |
| `agingAnalysis.total.fees[].amount` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].compoundingAmount` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.calculationType` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.chargeDate` | date | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.dueDate` | date | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.minAmount` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.outstanding` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.ratePer` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.timing` | enum | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.totalDue` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].fee.value` | money | (empty_list) |  |
| `agingAnalysis.total.fees[].periodCharge` | money | (empty_list) |  |
| `agingAnalysis.total.indexedPrincipal` | money | None |  |
| `agingAnalysis.total.interest` | money | 855,000 | aging total interest |
| `agingAnalysis.total.penalties[].amount` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].compoundingAmount` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.dueDate` | date | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.minAmount` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.outstanding` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.timing` | enum | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.totalDue` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].fee.value` | money | (empty_list) |  |
| `agingAnalysis.total.penalties[].periodCharge` | money | (empty_list) |  |
| `agingAnalysis.total.principal` | money | 27,240,937.50 | aging total principal |
| `agingAnalysis.total.total` | money | 31,870,609.80 | aging total — Mirrors overdue/totalOutstanding totals |
| `agingAnalysis.total.totalFees` | money | 903,521.18 |  |
| `agingAnalysis.total.totalPenalties` | money | 2,871,151.12 | aging total penalties |
| `agingAnalysis.total.totalTaxes` | money | 0 |  |
| `agingAnalysis.total.totalWithTaxes` | money | 31,870,609.80 |  |

### `baseCurrencyExchangeRate[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `baseCurrencyExchangeRate[].baseRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].effectiveDate` | date | (empty_list) |  |
| `baseCurrencyExchangeRate[].finalRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].floatingRateDate` | date | (empty_list) |  |
| `baseCurrencyExchangeRate[].fromDate` | date | (empty_list) |  |
| `baseCurrencyExchangeRate[].margin` | money | (empty_list) |  |
| `baseCurrencyExchangeRate[].maxRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].minRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].ratePer` | enum | (empty_list) |  |
| `baseCurrencyExchangeRate[].updateEndDate` | date | (empty_list) |  |
| `baseCurrencyExchangeRate[].updatedMargin` | money | (empty_list) |  |
| `baseCurrencyExchangeRate[].updatedMaxRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].updatedMinRate` | rate | (empty_list) |  |
| `baseCurrencyExchangeRate[].updatedRate` | rate | (empty_list) |  |

### `compoundingInterestRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `compoundingInterestRatesData[].baseRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].effectiveDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].finalRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].floatingRateDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].fromDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].margin` | money | (empty_list) |  |
| `compoundingInterestRatesData[].maxRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].minRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].ratePer` | enum | (empty_list) |  |
| `compoundingInterestRatesData[].updateEndDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMargin` | money | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMaxRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMinRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].updatedRate` | rate | (empty_list) |  |

### `deal`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `deal.chatMessages[].role` | enum | (absent) |  |
| `deal.chatMessages[].timestamp` | date | (absent) |  |
| `deal.createdAt` | date | (absent) |  |
| `deal.facilitySize` | money | (absent) | deal facility size — deal block is absent on this loan; redundant with commitment when present |
| `deal.files[].createdAt` | date | (absent) |  |
| `deal.files[].deletedAt` | date | (absent) |  |
| `deal.files[].entityType` | enum | (absent) |  |
| `deal.files[].extraction.extractionStatus` | enum | (absent) |  |
| `deal.files[].sizeInBytes` | count | (absent) |  |
| `deal.files[].updatedAt` | date | (absent) |  |
| `deal.status` | enum | (absent) |  |
| `deal.updatedAt` | date | (absent) |  |

### `defaultEvents[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `defaultEvents[].endDate` | date | None | default event end date — Null while default is open |
| `defaultEvents[].startDate` | date | 2025-08-15 | **default event start date** |

### `disbursements[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `disbursements[].amount` | money | 11,162,476.16 | **disbursement amount** — Per-draw amount; sum across array for total drawn (cf. summary.totalDisbursed) |
| `disbursements[].date` | date | 2024-02-09 | **disbursement date** |
| `disbursements[].deductions.accruedCompoundingInterest` | money | None |  |
| `disbursements[].deductions.compoundingInterest` | money | None |  |
| `disbursements[].deductions.fees[].amount` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].compoundingAmount` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.calculationType` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.chargeDate` | date | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.dueDate` | date | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.minAmount` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.outstanding` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.ratePer` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.timing` | enum | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.totalDue` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].fee.value` | money | (empty_list) |  |
| `disbursements[].deductions.fees[].periodCharge` | money | (empty_list) |  |
| `disbursements[].deductions.indexedPrincipal` | money | None |  |
| `disbursements[].deductions.interest` | money | None |  |
| `disbursements[].deductions.penalties[].amount` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].compoundingAmount` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.dueDate` | date | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.minAmount` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.outstanding` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.timing` | enum | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.totalDue` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].fee.value` | money | (empty_list) |  |
| `disbursements[].deductions.penalties[].periodCharge` | money | (empty_list) |  |
| `disbursements[].deductions.principal` | money | None |  |
| `disbursements[].deductions.total` | money | None | disbursement deductions total — Amount netted out of a draw (e.g. origination fee) |
| `disbursements[].deductions.totalFees` | money | None | disbursement fee deductions |
| `disbursements[].deductions.totalPenalties` | money | None |  |
| `disbursements[].deductions.totalTaxes` | money | None |  |
| `disbursements[].deductions.totalWithTaxes` | money | None |  |

### `exchangeRateRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `exchangeRateRatesData[].baseRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].effectiveDate` | date | (empty_list) |  |
| `exchangeRateRatesData[].finalRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].floatingRateDate` | date | (empty_list) |  |
| `exchangeRateRatesData[].fromDate` | date | (empty_list) |  |
| `exchangeRateRatesData[].margin` | money | (empty_list) |  |
| `exchangeRateRatesData[].maxRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].minRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].ratePer` | enum | (empty_list) |  |
| `exchangeRateRatesData[].updateEndDate` | date | (empty_list) |  |
| `exchangeRateRatesData[].updatedMargin` | money | (empty_list) |  |
| `exchangeRateRatesData[].updatedMaxRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].updatedMinRate` | rate | (empty_list) |  |
| `exchangeRateRatesData[].updatedRate` | rate | (empty_list) |  |

### `fees[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `fees[].accrualFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].accrualFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].accrualFrequency.daysOffset` | count | None |  |
| `fees[].accrualFrequency.endDate` | date | None |  |
| `fees[].accrualFrequency.every` | enum | None |  |
| `fees[].accrualFrequency.everyMultiplier` | count | None |  |
| `fees[].accrualFrequency.on` | enum | None |  |
| `fees[].accrualFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].accrualFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].accrualFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].accrualFrequency.repetitions` | count | None |  |
| `fees[].accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].accrualFrequency.startDate` | date | None |  |
| `fees[].calculationType` | enum | PercentageOfApprovedAmount |  |
| `fees[].chargeDate` | date | None |  |
| `fees[].chargeFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].chargeFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].chargeFrequency.daysOffset` | count | None |  |
| `fees[].chargeFrequency.endDate` | date | None |  |
| `fees[].chargeFrequency.every` | enum | None |  |
| `fees[].chargeFrequency.everyMultiplier` | count | None |  |
| `fees[].chargeFrequency.on` | enum | None |  |
| `fees[].chargeFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].chargeFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].chargeFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].chargeFrequency.repetitions` | count | None |  |
| `fees[].chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].chargeFrequency.startDate` | date | None |  |
| `fees[].chargePeriod.endDate` | date | None |  |
| `fees[].chargePeriod.relativeStartDate.amount` | count | None |  |
| `fees[].chargePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].chargePeriod.relativeStartDate.type` | enum | None |  |
| `fees[].chargePeriod.startDate` | date | None |  |
| `fees[].chargePeriod.timeInterval` | enum | None |  |
| `fees[].chargePeriod.timeIntervalMultiplier` | count | None |  |
| `fees[].chargeTiming` | enum | OnFirstDisbursement |  |
| `fees[].compoundingFeeCapitalizationComponent` | enum | None |  |
| `fees[].compoundingFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].compoundingFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].compoundingFrequency.daysOffset` | count | None |  |
| `fees[].compoundingFrequency.endDate` | date | None |  |
| `fees[].compoundingFrequency.every` | enum | None |  |
| `fees[].compoundingFrequency.everyMultiplier` | count | None |  |
| `fees[].compoundingFrequency.on` | enum | None |  |
| `fees[].compoundingFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].compoundingFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].compoundingFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].compoundingFrequency.repetitions` | count | None |  |
| `fees[].compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].compoundingFrequency.startDate` | date | None |  |
| `fees[].depositConditions` | enum | None |  |
| `fees[].depositNumberOfRepayments` | count | None |  |
| `fees[].depositPaysFor` | enum | None |  |
| `fees[].dueDate` | date | None |  |
| `fees[].duesCalculationMethod` | enum | None |  |
| `fees[].feePeriod.endDate` | date | None |  |
| `fees[].feePeriod.relativeStartDate.amount` | count | None |  |
| `fees[].feePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].feePeriod.relativeStartDate.type` | enum | None |  |
| `fees[].feePeriod.startDate` | date | None |  |
| `fees[].feePeriod.timeInterval` | enum | None |  |
| `fees[].feePeriod.timeIntervalMultiplier` | count | None |  |
| `fees[].fixedRepaymentAmount` | money | None |  |
| `fees[].minAmount` | money | None |  |
| `fees[].oidRecognitionStartDate` | date | None |  |
| `fees[].outstanding` | money | 0 | loan-level fee outstanding |
| `fees[].penaltyGrace.endDate` | date | None |  |
| `fees[].penaltyGrace.relativeStartDate.amount` | count | None |  |
| `fees[].penaltyGrace.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].penaltyGrace.relativeStartDate.type` | enum | None |  |
| `fees[].penaltyGrace.startDate` | date | None |  |
| `fees[].penaltyGrace.timeInterval` | enum | None |  |
| `fees[].penaltyGrace.timeIntervalMultiplier` | count | None |  |
| `fees[].ratePer` | enum | Year |  |
| `fees[].repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].repaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].repaymentFrequency.daysOffset` | count | None |  |
| `fees[].repaymentFrequency.endDate` | date | None |  |
| `fees[].repaymentFrequency.every` | enum | None |  |
| `fees[].repaymentFrequency.everyMultiplier` | count | None |  |
| `fees[].repaymentFrequency.on` | enum | None |  |
| `fees[].repaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].repaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].repaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].repaymentFrequency.repetitions` | count | None |  |
| `fees[].repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].repaymentFrequency.startDate` | date | None |  |
| `fees[].repaymentTiming` | enum | OnFirstDisbursement |  |
| `fees[].secondaryValue` | money | None |  |
| `fees[].timeIntervalToEffectiveValue.timeInterval` | enum | None |  |
| `fees[].timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | None |  |
| `fees[].timing` | enum | OnFirstDisbursement |  |
| `fees[].totalDue` | money | 1,200,000 | loan-level fee total due |
| `fees[].value` | money | 4 | loan-level fee rate/value — PERCENT when percent-based (example 4) |

### `fundingSourcesAsyncUpdate`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `fundingSourcesAsyncUpdate.lastUpdate` | date | 2026-06-26T03:43:29.722Z |  |
| `fundingSourcesAsyncUpdate.updateRequestTimestamp` | date | 2026-05-04T20:50:01.282Z |  |

### `groupLoanAsyncUpdate`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `groupLoanAsyncUpdate.lastUpdate` | date | None |  |
| `groupLoanAsyncUpdate.updateRequestTimestamp` | date | None |  |

### `interestRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `interestRatesData[].baseRate` | rate | 15 | base interest rate — PERCENT not fraction (example 15) |
| `interestRatesData[].effectiveDate` | date | None |  |
| `interestRatesData[].finalRate` | rate | 15 | **final interest rate** — PERCENT; base + margin combined |
| `interestRatesData[].floatingRateDate` | date | None |  |
| `interestRatesData[].fromDate` | date | 2024-02-08 | rate effective-from date |
| `interestRatesData[].margin` | money | None | interest margin — PERCENT not fraction |
| `interestRatesData[].maxRate` | rate | None | interest rate cap — PERCENT |
| `interestRatesData[].minRate` | rate | None | interest rate floor — PERCENT |
| `interestRatesData[].ratePer` | enum | Year | rate period basis — FrequencyEveryEnum (e.g. Year) |
| `interestRatesData[].updateEndDate` | date | None |  |
| `interestRatesData[].updatedMargin` | money | None |  |
| `interestRatesData[].updatedMaxRate` | rate | None |  |
| `interestRatesData[].updatedMinRate` | rate | None |  |
| `interestRatesData[].updatedRate` | rate | None |  |

### `oidRestructureEvents[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `oidRestructureEvents[].date` | date | 2024-02-09 | OID/restructure event date |
| `oidRestructureEvents[].effectiveDate` | date | 2024-02-09 | restructure effective date |
| `oidRestructureEvents[].newRate` | rate | None | restructure new rate — PERCENT |
| `oidRestructureEvents[].relatedEntityType` | enum | LoanTransaction |  |

### `oidTerms`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `oidTerms.components[].createdAt` | date | (absent) |  |
| `oidTerms.components[].date` | date | (absent) |  |
| `oidTerms.components[].initialAmortizedAmount` | money | (absent) |  |
| `oidTerms.components[].type` | enum | (absent) |  |
| `oidTerms.components[].value` | money | (absent) |  |
| `oidTerms.date` | date | (absent) |  |
| `oidTerms.daysInMonth` | enum | (absent) |  |
| `oidTerms.daysInYear` | enum | (absent) |  |
| `oidTerms.frequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `oidTerms.frequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `oidTerms.frequency.daysOffset` | count | (absent) |  |
| `oidTerms.frequency.endDate` | date | (absent) |  |
| `oidTerms.frequency.every` | enum | (absent) |  |
| `oidTerms.frequency.everyMultiplier` | count | (absent) |  |
| `oidTerms.frequency.on` | enum | (absent) |  |
| `oidTerms.frequency.relativeStartDate.amount` | count | (absent) |  |
| `oidTerms.frequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `oidTerms.frequency.relativeStartDate.type` | enum | (absent) |  |
| `oidTerms.frequency.repetitions` | count | (absent) |  |
| `oidTerms.frequency.specificDates[]` | date | (absent) |  |
| `oidTerms.frequency.startDate` | date | (absent) |  |
| `oidTerms.fundingTerms.components[].allocationType` | enum | (absent) |  |
| `oidTerms.fundingTerms.components[].allocationValue` | money | (absent) |  |
| `oidTerms.fundingTerms.components[].assetComponent.createdAt` | date | (absent) |  |
| `oidTerms.fundingTerms.components[].assetComponent.date` | date | (absent) |  |
| `oidTerms.fundingTerms.components[].assetComponent.initialAmortizedAmount` | money | (absent) |  |
| `oidTerms.fundingTerms.components[].assetComponent.type` | enum | (absent) |  |
| `oidTerms.fundingTerms.components[].assetComponent.value` | money | (absent) |  |
| `oidTerms.method` | enum | (absent) |  |
| `oidTerms.nonAccrualPeriods[].endDate` | date | (absent) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.amount` | count | (absent) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.timeUnit` | enum | (absent) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.type` | enum | (absent) |  |
| `oidTerms.nonAccrualPeriods[].startDate` | date | (absent) |  |
| `oidTerms.nonAccrualPeriods[].timeInterval` | enum | (absent) |  |
| `oidTerms.nonAccrualPeriods[].timeIntervalMultiplier` | count | (absent) |  |

### `principalIndexRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `principalIndexRatesData[].baseRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].effectiveDate` | date | (empty_list) |  |
| `principalIndexRatesData[].finalRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].floatingRateDate` | date | (empty_list) |  |
| `principalIndexRatesData[].fromDate` | date | (empty_list) |  |
| `principalIndexRatesData[].margin` | money | (empty_list) |  |
| `principalIndexRatesData[].maxRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].minRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].ratePer` | enum | (empty_list) |  |
| `principalIndexRatesData[].updateEndDate` | date | (empty_list) |  |
| `principalIndexRatesData[].updatedMargin` | money | (empty_list) |  |
| `principalIndexRatesData[].updatedMaxRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].updatedMinRate` | rate | (empty_list) |  |
| `principalIndexRatesData[].updatedRate` | rate | (empty_list) |  |

### `repaymentSchedule`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `repaymentSchedule.agingAnalysis.cohorts[].numberOfDays` | count | 0 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.indexedPrincipal` | money | None |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.interest` | money | 462,500 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.principal` | money | 0 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.total` | money | 1,905,062.20 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalFees` | money | 250,771.18 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalPenalties` | money | 1,191,791.02 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalTaxes` | money | 0 |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalWithTaxes` | money | 1,905,062.20 |  |
| `repaymentSchedule.agingAnalysis.total.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.agingAnalysis.total.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.agingAnalysis.total.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.indexedPrincipal` | money | None |  |
| `repaymentSchedule.agingAnalysis.total.interest` | money | 855,000 |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.agingAnalysis.total.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.agingAnalysis.total.total` | money | 31,870,609.80 |  |
| `repaymentSchedule.agingAnalysis.total.totalFees` | money | 903,521.18 |  |
| `repaymentSchedule.agingAnalysis.total.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.agingAnalysis.total.totalTaxes` | money | 0 |  |
| `repaymentSchedule.agingAnalysis.total.totalWithTaxes` | money | 31,870,609.80 |  |
| `repaymentSchedule.expectedDeployments[].commitment` | money | (empty_list) |  |
| `repaymentSchedule.expectedDeployments[].date` | date | (empty_list) |  |
| `repaymentSchedule.expectedDeployments[].deployment` | money | (empty_list) |  |
| `repaymentSchedule.loanKPIs.dpi` | money | 0.4114212295 | **DPI** — Multiple (example 0.41x), not a percent |
| `repaymentSchedule.loanKPIs.dpiIncludingEquity` | money | 0.4114212295 | DPI incl. equity — Multiple |
| `repaymentSchedule.loanKPIs.expectedDpi` | money | 1.58 | expected DPI — Multiple |
| `repaymentSchedule.loanKPIs.expectedDpiIncludingEquity` | money | 1.58 |  |
| `repaymentSchedule.loanKPIs.expectedIrr` | money | -56.81 | **expected IRR** — PERCENT; can be negative (example -56.8) |
| `repaymentSchedule.loanKPIs.expectedIrrIncludingEquity` | money | -56.81 | expected IRR incl. equity — PERCENT |
| `repaymentSchedule.loanKPIs.expectedTvpi` | money | 1.58 | expected TVPI — Multiple |
| `repaymentSchedule.loanKPIs.expectedTvpiIncludingEquity` | money | 1.58 |  |
| `repaymentSchedule.loanKPIs.irr` | money | 31.40 | **IRR** — PERCENT (example 31.4 = 31.4%); IncludingEquity variant folds in equity legs |
| `repaymentSchedule.loanKPIs.irrIncludingEquity` | money | 31.40 | IRR incl. equity — PERCENT |
| `repaymentSchedule.loanKPIs.tvpi` | money | 1.58 | **TVPI** — Multiple (example 1.58x) |
| `repaymentSchedule.loanKPIs.tvpiIncludingEquity` | money | 1.58 | TVPI incl. equity — Multiple |
| `repaymentSchedule.scheduleTable[].baseCurrencyExchangeRate` | rate | None |  |
| `repaymentSchedule.scheduleTable[].compoundingChargedOnPeriod` | money | None |  |
| `repaymentSchedule.scheduleTable[].compoundingInterestRate` | rate | None |  |
| `repaymentSchedule.scheduleTable[].compoundingRatePer` | enum | Year |  |
| `repaymentSchedule.scheduleTable[].date` | date | 2024-02-09 | **schedule row date** — One row per scheduled period |
| `repaymentSchedule.scheduleTable[].disbursedAmount` | money | None | period disbursed amount |
| `repaymentSchedule.scheduleTable[].due.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.compoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.fees[].amount` | money | 1,200,000 |  |
| `repaymentSchedule.scheduleTable[].due.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.interest` | money | None | period interest due |
| `repaymentSchedule.scheduleTable[].due.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.principal` | money | 11,162,476.16 | period principal due |
| `repaymentSchedule.scheduleTable[].due.total` | money | 12,362,476.16 | **period total due** — Net of components |
| `repaymentSchedule.scheduleTable[].due.totalFees` | money | 1,200,000 |  |
| `repaymentSchedule.scheduleTable[].due.totalPenalties` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].due.totalTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.totalWithTaxes` | money | 12,362,476.16 |  |
| `repaymentSchedule.scheduleTable[].effectiveDate` | date | 2024-02-09 |  |
| `repaymentSchedule.scheduleTable[].index` | count | 0 | schedule row index |
| `repaymentSchedule.scheduleTable[].interestChargedOnPeriod` | money | None |  |
| `repaymentSchedule.scheduleTable[].interestRate` | rate | 15 | period interest rate — PERCENT not fraction (example 15) |
| `repaymentSchedule.scheduleTable[].nonCapitalizedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.amount` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].amortized` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].unamortized` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.indexedRemainingCost` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.rate` | rate | None | period OID rate — PERCENT |
| `repaymentSchedule.scheduleTable[].oid.remainingCost` | money | None | period OID remaining cost |
| `repaymentSchedule.scheduleTable[].oid.totalWithInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.capitalizedBalance` | money | 11,162,476.16 |  |
| `repaymentSchedule.scheduleTable[].outstanding.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].amount` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.interest` | money | 12,500 |  |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].amount` | money | 1,550.34 |  |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].periodCharge` | money | 1,550.34 | per-diem penalty accrual — Per-row daily accrual; 'periodCharge'/'due' on an accrual row is the per-diem |
| `repaymentSchedule.scheduleTable[].outstanding.principal` | money | 11,162,476.16 | period-end principal outstanding — Per-row running balance, not the loan-level outstanding |
| `repaymentSchedule.scheduleTable[].outstanding.total` | money | 8,926,526.50 | period-end total outstanding — Net of components; can dip below principal due to credits |
| `repaymentSchedule.scheduleTable[].outstanding.totalCompoundingInterest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalFees` | money | -2,250,000 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalPenalties` | money | 1,550.34 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalTaxes` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalWithTaxes` | money | 8,926,526.50 |  |
| `repaymentSchedule.scheduleTable[].paid.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].amount` | money | 1,200,000 |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.interest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.principal` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.total` | money | 3,450,000 | period total paid |
| `repaymentSchedule.scheduleTable[].paid.totalFees` | money | 3,450,000 |  |
| `repaymentSchedule.scheduleTable[].paid.totalPenalties` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.totalTaxes` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.totalWithTaxes` | money | 3,450,000 |  |
| `repaymentSchedule.scheduleTable[].principalRealizedBalance` | money | 11,162,476.16 | principal realized balance |
| `repaymentSchedule.scheduleTable[].ratePer` | enum | Year |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.date` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.effectiveDate` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.effectiveFrom` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.accruedCompoundingInterest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.compoundingInterest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.indexedPrincipal` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.interest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.principal` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.total` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalFees` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalPenalties` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalTaxes` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalWithTaxes` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.type` | enum | (absent) |  |
| `repaymentSchedule.scheduleTable[].type` | enum | ExpectedDisbursement |  |
| `repaymentSchedule.scheduleTable[].waived.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.compoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.interest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.principal` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.total` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalFees` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalPenalties` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalWithTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.compoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.interest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.principal` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.total` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalFees` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalPenalties` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalWithTaxes` | money | None |  |
| `repaymentSchedule.summary.compoundingInterestRate` | rate | None |  |
| `repaymentSchedule.summary.distributedPrincipal` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.exchangeRateImpact.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.exchangeRateImpact.interest` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.principal` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.total` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.expectedPaidInCapital` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.interestRate` | rate | 15 |  |
| `repaymentSchedule.summary.oidRate` | rate | None |  |
| `repaymentSchedule.summary.oidRemainingCost` | money | None |  |
| `repaymentSchedule.summary.outstandingPrincipalBeforeAmortization` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.overdue.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.overdue.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.overdue.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.overdue.interest` | money | 855,000 |  |
| `repaymentSchedule.summary.overdue.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.overdue.total` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.overdue.totalFees` | money | 903,521.18 |  |
| `repaymentSchedule.summary.overdue.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.summary.overdue.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.overdue.totalWithTaxes` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.paidInCapital` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalDisbursed` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalDue.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalDue.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalDue.interest` | money | 855,000 |  |
| `repaymentSchedule.summary.totalDue.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalDue.total` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.totalDue.totalFees` | money | 903,521.18 |  |
| `repaymentSchedule.summary.totalDue.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.summary.totalDue.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.totalWithTaxes` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.totalExpected.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalExpected.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalExpected.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalExpected.interest` | money | 10,862,500 |  |
| `repaymentSchedule.summary.totalExpected.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalExpected.total` | money | 43,078,109.80 |  |
| `repaymentSchedule.summary.totalExpected.totalFees` | money | 2,103,521.18 |  |
| `repaymentSchedule.summary.totalExpected.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.summary.totalExpected.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalExpected.totalWithTaxes` | money | 43,078,109.80 |  |
| `repaymentSchedule.summary.totalExpectedDisbursements` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalExpectedToDate.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalExpectedToDate.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalExpectedToDate.interest` | money | 10,862,500 |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalExpectedToDate.total` | money | 43,078,109.80 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalFees` | money | 2,103,521.18 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalWithTaxes` | money | 43,078,109.80 |  |
| `repaymentSchedule.summary.totalOID.amount` | money | 0 |  |
| `repaymentSchedule.summary.totalOID.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.capitalizedBalance` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalOutstanding.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalOutstanding.interest` | money | 855,000 |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.principal` | money | 27,240,937.50 |  |
| `repaymentSchedule.summary.totalOutstanding.total` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.totalOutstanding.totalCompoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.totalFees` | money | 903,521.18 |  |
| `repaymentSchedule.summary.totalOutstanding.totalPenalties` | money | 2,871,151.12 |  |
| `repaymentSchedule.summary.totalOutstanding.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.totalWithTaxes` | money | 31,870,609.80 |  |
| `repaymentSchedule.summary.totalPaid.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalPaid.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalPaid.interest` | money | 10,007,500 |  |
| `repaymentSchedule.summary.totalPaid.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.total` | money | 11,207,500 |  |
| `repaymentSchedule.summary.totalPaid.totalFees` | money | 1,200,000 |  |
| `repaymentSchedule.summary.totalPaid.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.totalWithTaxes` | money | 11,207,500 |  |
| `repaymentSchedule.summary.totalWaived.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalWaived.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalWaived.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.total` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalWrittenOff.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalWrittenOff.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.total` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.unutilizedPrincipal` | money | 2,759,062.50 |  |
| `repaymentSchedule.updatedAt` | date | 2026-06-26T03:43:29.000Z |  |

### `summary`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `summary.compoundingInterestRate` | rate | None | summary compounding rate — PERCENT not fraction |
| `summary.distributedPrincipal` | money | 0 | distributed principal |
| `summary.exchangeRateImpact.accruedCompoundingInterest` | money | None |  |
| `summary.exchangeRateImpact.compoundingInterest` | money | 0 |  |
| `summary.exchangeRateImpact.fees[].amount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].fee.value` | money | (empty_list) |  |
| `summary.exchangeRateImpact.fees[].periodCharge` | money | (empty_list) |  |
| `summary.exchangeRateImpact.indexedPrincipal` | money | None |  |
| `summary.exchangeRateImpact.interest` | money | 0 |  |
| `summary.exchangeRateImpact.penalties[].amount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].fee.value` | money | (empty_list) |  |
| `summary.exchangeRateImpact.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.exchangeRateImpact.principal` | money | 0 |  |
| `summary.exchangeRateImpact.total` | money | 0 |  |
| `summary.exchangeRateImpact.totalFees` | money | 0 |  |
| `summary.exchangeRateImpact.totalPenalties` | money | 0 |  |
| `summary.exchangeRateImpact.totalTaxes` | money | 0 |  |
| `summary.exchangeRateImpact.totalWithTaxes` | money | 0 |  |
| `summary.expectedPaidInCapital` | money | 27,240,937.50 | expected paid-in capital |
| `summary.interestRate` | rate | 15 | **summary interest rate** — PERCENT not fraction (example 15) |
| `summary.oidRate` | rate | None | OID rate — PERCENT not fraction |
| `summary.oidRemainingCost` | money | None | OID remaining cost |
| `summary.outstandingPrincipalBeforeAmortization` | money | 27,240,937.50 | outstanding principal before amortization |
| `summary.overdue.accruedCompoundingInterest` | money | None |  |
| `summary.overdue.compoundingInterest` | money | 0 |  |
| `summary.overdue.fees[].amount` | money | (empty_list) |  |
| `summary.overdue.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.overdue.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.overdue.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.overdue.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.overdue.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.overdue.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.overdue.fees[].fee.value` | money | (empty_list) |  |
| `summary.overdue.fees[].periodCharge` | money | (empty_list) |  |
| `summary.overdue.indexedPrincipal` | money | None |  |
| `summary.overdue.interest` | money | 855,000 | **overdue interest** |
| `summary.overdue.penalties[].amount` | money | (empty_list) |  |
| `summary.overdue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.overdue.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.overdue.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.overdue.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.overdue.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.overdue.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.overdue.penalties[].fee.value` | money | (empty_list) |  |
| `summary.overdue.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.overdue.principal` | money | 27,240,937.50 | **overdue principal** |
| `summary.overdue.total` | money | 31,870,609.80 | **total overdue** — NET of components; principal-only via .principal |
| `summary.overdue.totalFees` | money | 903,521.18 | overdue fees |
| `summary.overdue.totalPenalties` | money | 2,871,151.12 | **overdue penalties** |
| `summary.overdue.totalTaxes` | money | 0 |  |
| `summary.overdue.totalWithTaxes` | money | 31,870,609.80 | total overdue incl. taxes |
| `summary.paidInCapital` | money | 27,240,937.50 | **paid-in capital** |
| `summary.totalDisbursed` | money | 27,240,937.50 | **total disbursed** |
| `summary.totalDue.accruedCompoundingInterest` | money | None |  |
| `summary.totalDue.compoundingInterest` | money | 0 | compounding interest due |
| `summary.totalDue.fees[].amount` | money | (empty_list) |  |
| `summary.totalDue.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalDue.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalDue.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalDue.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalDue.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalDue.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalDue.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalDue.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalDue.indexedPrincipal` | money | None |  |
| `summary.totalDue.interest` | money | 855,000 | **interest due** |
| `summary.totalDue.penalties[].amount` | money | (empty_list) |  |
| `summary.totalDue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalDue.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalDue.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalDue.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalDue.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalDue.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalDue.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalDue.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalDue.principal` | money | 27,240,937.50 | **principal due** |
| `summary.totalDue.total` | money | 31,870,609.80 | **total amount due** — NET of components like the outstanding block; for principal-only use .principal |
| `summary.totalDue.totalFees` | money | 903,521.18 | fees due |
| `summary.totalDue.totalPenalties` | money | 2,871,151.12 | **penalties due** |
| `summary.totalDue.totalTaxes` | money | 0 |  |
| `summary.totalDue.totalWithTaxes` | money | 31,870,609.80 | total due incl. taxes |
| `summary.totalExpected.accruedCompoundingInterest` | money | None |  |
| `summary.totalExpected.compoundingInterest` | money | 0 |  |
| `summary.totalExpected.fees[].amount` | money | (empty_list) |  |
| `summary.totalExpected.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalExpected.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalExpected.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalExpected.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalExpected.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalExpected.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalExpected.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalExpected.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalExpected.indexedPrincipal` | money | None |  |
| `summary.totalExpected.interest` | money | 10,862,500 | **expected interest (life-of-loan)** |
| `summary.totalExpected.penalties[].amount` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalExpected.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalExpected.principal` | money | 27,240,937.50 | expected principal |
| `summary.totalExpected.total` | money | 43,078,109.80 | **total expected (life-of-loan)** — Full-term projection; totalExpectedToDate is the as-of-today cut \| Same component-netting as the other .total fields — NET, not a gross life-of-loan cash projection. Use the component sub-fields (interest, principal) for a gross basis; totalExpectedToDate.total is the as-of-today net cut. |
| `summary.totalExpected.totalFees` | money | 2,103,521.18 | expected fees |
| `summary.totalExpected.totalPenalties` | money | 2,871,151.12 | expected penalties |
| `summary.totalExpected.totalTaxes` | money | 0 |  |
| `summary.totalExpected.totalWithTaxes` | money | 43,078,109.80 |  |
| `summary.totalExpectedDisbursements` | money | 27,240,937.50 | total expected disbursements |
| `summary.totalExpectedToDate.accruedCompoundingInterest` | money | None |  |
| `summary.totalExpectedToDate.compoundingInterest` | money | 0 |  |
| `summary.totalExpectedToDate.fees[].amount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalExpectedToDate.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalExpectedToDate.indexedPrincipal` | money | None |  |
| `summary.totalExpectedToDate.interest` | money | 10,862,500 | interest expected to date |
| `summary.totalExpectedToDate.penalties[].amount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalExpectedToDate.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalExpectedToDate.principal` | money | 27,240,937.50 |  |
| `summary.totalExpectedToDate.total` | money | 43,078,109.80 | total expected to date — As-of-today slice of totalExpected |
| `summary.totalExpectedToDate.totalFees` | money | 2,103,521.18 |  |
| `summary.totalExpectedToDate.totalPenalties` | money | 2,871,151.12 |  |
| `summary.totalExpectedToDate.totalTaxes` | money | 0 |  |
| `summary.totalExpectedToDate.totalWithTaxes` | money | 43,078,109.80 |  |
| `summary.totalOID.amount` | money | 0 | total OID amount |
| `summary.totalOID.interest` | money | 0 | total OID interest |
| `summary.totalOutstanding.capitalizedBalance` | money | 27,240,937.50 | capitalized balance (memo) — NON-additive MEMO — equals principal; do NOT add into a sum |
| `summary.totalOutstanding.compoundingInterest` | money | 0 | outstanding compounding interest |
| `summary.totalOutstanding.fees[].amount` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalOutstanding.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalOutstanding.indexedPrincipal` | money | None | indexed principal outstanding |
| `summary.totalOutstanding.interest` | money | 855,000 | **outstanding interest** |
| `summary.totalOutstanding.penalties[].amount` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalOutstanding.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalOutstanding.principal` | money | 27,240,937.50 | **outstanding principal** — Use THIS for an interest basis, NOT totalOutstanding.total (which is net of fee/credit components) |
| `summary.totalOutstanding.total` | money | 31,870,609.80 | **total outstanding (net)** — NET of fee/credit components — NOT principal; example 31.87M vs principal 27.24M. For an interest basis use .principal |
| `summary.totalOutstanding.totalCompoundingInterest` | money | 0 | total outstanding compounding interest |
| `summary.totalOutstanding.totalFees` | money | 903,521.18 | **outstanding fees** |
| `summary.totalOutstanding.totalPenalties` | money | 2,871,151.12 | **outstanding penalties** — Penalties here are the default/late-interest bucket |
| `summary.totalOutstanding.totalTaxes` | money | 0 | outstanding taxes |
| `summary.totalOutstanding.totalWithTaxes` | money | 31,870,609.80 | total outstanding incl. taxes — == total when totalTaxes is 0 |
| `summary.totalPaid.accruedCompoundingInterest` | money | None |  |
| `summary.totalPaid.compoundingInterest` | money | 0 |  |
| `summary.totalPaid.fees[].amount` | money | (empty_list) |  |
| `summary.totalPaid.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalPaid.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalPaid.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalPaid.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalPaid.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalPaid.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalPaid.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalPaid.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalPaid.indexedPrincipal` | money | None |  |
| `summary.totalPaid.interest` | money | 10,007,500 | **interest paid** |
| `summary.totalPaid.penalties[].amount` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalPaid.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalPaid.principal` | money | 0 | **principal paid** — Can be 0 even when interest/fees paid (interest-only loan) |
| `summary.totalPaid.total` | money | 11,207,500 | **total paid** — Like the other .total buckets (totalOutstanding/totalDue/overdue), this is NET of fee/credit components — NOT a gross sum of cash received. For principal-only paid use .principal; do not treat .total as gross amount paid. |
| `summary.totalPaid.totalFees` | money | 1,200,000 | fees paid |
| `summary.totalPaid.totalPenalties` | money | 0 | penalties paid |
| `summary.totalPaid.totalTaxes` | money | 0 |  |
| `summary.totalPaid.totalWithTaxes` | money | 11,207,500 | total paid incl. taxes |
| `summary.totalWaived.accruedCompoundingInterest` | money | None |  |
| `summary.totalWaived.compoundingInterest` | money | 0 |  |
| `summary.totalWaived.fees[].amount` | money | (empty_list) |  |
| `summary.totalWaived.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalWaived.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalWaived.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalWaived.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalWaived.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalWaived.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalWaived.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalWaived.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalWaived.indexedPrincipal` | money | None |  |
| `summary.totalWaived.interest` | money | 0 | interest waived |
| `summary.totalWaived.penalties[].amount` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalWaived.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalWaived.principal` | money | 0 |  |
| `summary.totalWaived.total` | money | 0 | total waived |
| `summary.totalWaived.totalFees` | money | 0 |  |
| `summary.totalWaived.totalPenalties` | money | 0 | penalties waived |
| `summary.totalWaived.totalTaxes` | money | 0 |  |
| `summary.totalWaived.totalWithTaxes` | money | 0 |  |
| `summary.totalWrittenOff.accruedCompoundingInterest` | money | None |  |
| `summary.totalWrittenOff.compoundingInterest` | money | 0 |  |
| `summary.totalWrittenOff.fees[].amount` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.timing` | enum | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].fee.value` | money | (empty_list) |  |
| `summary.totalWrittenOff.fees[].periodCharge` | money | (empty_list) |  |
| `summary.totalWrittenOff.indexedPrincipal` | money | None |  |
| `summary.totalWrittenOff.interest` | money | 0 | interest written off |
| `summary.totalWrittenOff.penalties[].amount` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.dueDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.minAmount` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.outstanding` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.timing` | enum | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.totalDue` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].fee.value` | money | (empty_list) |  |
| `summary.totalWrittenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `summary.totalWrittenOff.principal` | money | 0 | principal written off |
| `summary.totalWrittenOff.total` | money | 0 | **total written off** |
| `summary.totalWrittenOff.totalFees` | money | 0 |  |
| `summary.totalWrittenOff.totalPenalties` | money | 0 |  |
| `summary.totalWrittenOff.totalTaxes` | money | 0 |  |
| `summary.totalWrittenOff.totalWithTaxes` | money | 0 |  |
| `summary.unutilizedPrincipal` | money | 2,759,062.50 | **unutilized principal** — commitment minus drawn (example 2.76M = 30M commitment - 27.24M drawn) |

### `taxRules[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `taxRules[].date` | date | (empty_list) | tax rule effective date |
| `taxRules[].vat` | money | (empty_list) | VAT rate — Likely a PERCENT; empty for this loan |

### `terms[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `terms[].amortizationType` | enum | EqualPrincipalPayments |  |
| `terms[].approvedPrincipal` | money | 30,000,000 | **approved principal** — Per-term version of commitment (example 30M) \| Per-term restatement of the SAME commitment figure (example 30M = loan-level commitment), repeated once per term version. Do NOT sum across terms[] — take the latest/approved term only; summing double-counts the commitment. |
| `terms[].approvedPrincipalInBaseCurrency` | money | None |  |
| `terms[].capitalizationComponent` | enum | None |  |
| `terms[].commitmentExpirationDate` | date | None | commitment expiration date |
| `terms[].compoundingInterestFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].compoundingInterestFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].compoundingInterestFrequency.daysOffset` | count | (absent) |  |
| `terms[].compoundingInterestFrequency.endDate` | date | (absent) |  |
| `terms[].compoundingInterestFrequency.every` | enum | (absent) |  |
| `terms[].compoundingInterestFrequency.everyMultiplier` | count | (absent) |  |
| `terms[].compoundingInterestFrequency.on` | enum | (absent) |  |
| `terms[].compoundingInterestFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].compoundingInterestFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].compoundingInterestFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].compoundingInterestFrequency.repetitions` | count | (absent) |  |
| `terms[].compoundingInterestFrequency.specificDates[]` | date | (absent) |  |
| `terms[].compoundingInterestFrequency.startDate` | date | (absent) |  |
| `terms[].compoundingInterestGrace[].endDate` | date | (empty_list) |  |
| `terms[].compoundingInterestGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `terms[].compoundingInterestGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `terms[].compoundingInterestGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `terms[].compoundingInterestGrace[].startDate` | date | (empty_list) |  |
| `terms[].compoundingInterestGrace[].timeInterval` | enum | (empty_list) |  |
| `terms[].compoundingInterestGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `terms[].compoundingInterestRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.daysOffset` | count | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.endDate` | date | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.every` | enum | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.everyMultiplier` | count | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.on` | enum | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.repetitions` | count | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.specificDates[]` | date | (absent) |  |
| `terms[].compoundingInterestRepaymentFrequency.startDate` | date | (absent) |  |
| `terms[].customPrincipalAmortization[].amortizationType` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].date` | date | (empty_list) |  |
| `terms[].customPrincipalAmortization[].fixedRepaymentAmount` | money | (empty_list) |  |
| `terms[].customPrincipalAmortization[].percentageOfAmountToAmortize` | rate | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.endDate` | date | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.every` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.on` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.repetitions` | count | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].customPrincipalAmortization[].repaymentFrequency.startDate` | date | (empty_list) |  |
| `terms[].customPrincipalAmortization[].type` | enum | (empty_list) |  |
| `terms[].date` | date | 2024-02-09 | term date — terms[] is versioned; latest entry is current |
| `terms[].decreasedCompoundingPaymentLimit` | money | None |  |
| `terms[].decreasedCompoundingPaymentPercentage` | rate | None |  |
| `terms[].disbursementDayInMonthForRepaymentsDelay` | count | None |  |
| `terms[].effectiveDate` | date | None | term effective date |
| `terms[].expectedScheduleEndDate` | date | 2025-02-07 | expected schedule end date (term) |
| `terms[].fees[].accrualFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].fees[].accrualFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].fees[].accrualFrequency.daysOffset` | count | None |  |
| `terms[].fees[].accrualFrequency.endDate` | date | None |  |
| `terms[].fees[].accrualFrequency.every` | enum | None |  |
| `terms[].fees[].accrualFrequency.everyMultiplier` | count | None |  |
| `terms[].fees[].accrualFrequency.on` | enum | None |  |
| `terms[].fees[].accrualFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].fees[].accrualFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].fees[].accrualFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].fees[].accrualFrequency.repetitions` | count | None |  |
| `terms[].fees[].accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].fees[].accrualFrequency.startDate` | date | None |  |
| `terms[].fees[].calculationType` | enum | PercentageOfApprovedAmount |  |
| `terms[].fees[].chargeDate` | date | None | fee charge date |
| `terms[].fees[].chargeFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].fees[].chargeFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].fees[].chargeFrequency.daysOffset` | count | None |  |
| `terms[].fees[].chargeFrequency.endDate` | date | None |  |
| `terms[].fees[].chargeFrequency.every` | enum | None |  |
| `terms[].fees[].chargeFrequency.everyMultiplier` | count | None |  |
| `terms[].fees[].chargeFrequency.on` | enum | None |  |
| `terms[].fees[].chargeFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].fees[].chargeFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].fees[].chargeFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].fees[].chargeFrequency.repetitions` | count | None |  |
| `terms[].fees[].chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].fees[].chargeFrequency.startDate` | date | None |  |
| `terms[].fees[].chargePeriod.endDate` | date | None |  |
| `terms[].fees[].chargePeriod.relativeStartDate.amount` | count | None |  |
| `terms[].fees[].chargePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `terms[].fees[].chargePeriod.relativeStartDate.type` | enum | None |  |
| `terms[].fees[].chargePeriod.startDate` | date | None |  |
| `terms[].fees[].chargePeriod.timeInterval` | enum | None |  |
| `terms[].fees[].chargePeriod.timeIntervalMultiplier` | count | None |  |
| `terms[].fees[].chargeTiming` | enum | OnFirstDisbursement |  |
| `terms[].fees[].compoundingFeeCapitalizationComponent` | enum | None |  |
| `terms[].fees[].compoundingFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].fees[].compoundingFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].fees[].compoundingFrequency.daysOffset` | count | None |  |
| `terms[].fees[].compoundingFrequency.endDate` | date | None |  |
| `terms[].fees[].compoundingFrequency.every` | enum | None |  |
| `terms[].fees[].compoundingFrequency.everyMultiplier` | count | None |  |
| `terms[].fees[].compoundingFrequency.on` | enum | None |  |
| `terms[].fees[].compoundingFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].fees[].compoundingFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].fees[].compoundingFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].fees[].compoundingFrequency.repetitions` | count | None |  |
| `terms[].fees[].compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].fees[].compoundingFrequency.startDate` | date | None |  |
| `terms[].fees[].depositConditions` | enum | None |  |
| `terms[].fees[].depositNumberOfRepayments` | count | None |  |
| `terms[].fees[].depositPaysFor` | enum | None |  |
| `terms[].fees[].dueDate` | date | None | fee due date |
| `terms[].fees[].duesCalculationMethod` | enum | None |  |
| `terms[].fees[].feePeriod.endDate` | date | None |  |
| `terms[].fees[].feePeriod.relativeStartDate.amount` | count | None |  |
| `terms[].fees[].feePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `terms[].fees[].feePeriod.relativeStartDate.type` | enum | None |  |
| `terms[].fees[].feePeriod.startDate` | date | None |  |
| `terms[].fees[].feePeriod.timeInterval` | enum | None |  |
| `terms[].fees[].feePeriod.timeIntervalMultiplier` | count | None |  |
| `terms[].fees[].fixedRepaymentAmount` | money | None |  |
| `terms[].fees[].minAmount` | money | None | fee minimum amount |
| `terms[].fees[].oidRecognitionStartDate` | date | None |  |
| `terms[].fees[].outstanding` | money | 0 | fee outstanding |
| `terms[].fees[].penaltyGrace.endDate` | date | None |  |
| `terms[].fees[].penaltyGrace.relativeStartDate.amount` | count | None |  |
| `terms[].fees[].penaltyGrace.relativeStartDate.timeUnit` | enum | None |  |
| `terms[].fees[].penaltyGrace.relativeStartDate.type` | enum | None |  |
| `terms[].fees[].penaltyGrace.startDate` | date | None |  |
| `terms[].fees[].penaltyGrace.timeInterval` | enum | None |  |
| `terms[].fees[].penaltyGrace.timeIntervalMultiplier` | count | None |  |
| `terms[].fees[].ratePer` | enum | Year |  |
| `terms[].fees[].repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].fees[].repaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].fees[].repaymentFrequency.daysOffset` | count | None |  |
| `terms[].fees[].repaymentFrequency.endDate` | date | None |  |
| `terms[].fees[].repaymentFrequency.every` | enum | None |  |
| `terms[].fees[].repaymentFrequency.everyMultiplier` | count | None |  |
| `terms[].fees[].repaymentFrequency.on` | enum | None |  |
| `terms[].fees[].repaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].fees[].repaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].fees[].repaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].fees[].repaymentFrequency.repetitions` | count | None |  |
| `terms[].fees[].repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].fees[].repaymentFrequency.startDate` | date | None |  |
| `terms[].fees[].repaymentTiming` | enum | OnFirstDisbursement |  |
| `terms[].fees[].secondaryValue` | money | None |  |
| `terms[].fees[].timeIntervalToEffectiveValue.timeInterval` | enum | None |  |
| `terms[].fees[].timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | None |  |
| `terms[].fees[].timing` | enum | OnFirstDisbursement |  |
| `terms[].fees[].totalDue` | money | 1,200,000 | **fee total due** — Absolute amount (example 1,200,000 = 4% of 30M) |
| `terms[].fees[].value` | money | 4 | **fee rate/value** — When percent-based this is a PERCENT (example 4 = 4%), not a fraction |
| `terms[].fixedRepaymentAmount` | money | None |  |
| `terms[].fundingSourcesNumberOfDelayedPrincipalRepayments` | count | None |  |
| `terms[].fundingSourcesPrincipalRepaymentDelay.timeInterval` | enum | None |  |
| `terms[].fundingSourcesPrincipalRepaymentDelay.timeIntervalMultiplier` | count | None |  |
| `terms[].fundingTerms.commitmentAmount` | money | None | funding commitment amount |
| `terms[].fundingTerms.seniority` | count | None | funding seniority rank |
| `terms[].interestAccrualFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].interestAccrualFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].interestAccrualFrequency.daysOffset` | count | None |  |
| `terms[].interestAccrualFrequency.endDate` | date | None |  |
| `terms[].interestAccrualFrequency.every` | enum | None |  |
| `terms[].interestAccrualFrequency.everyMultiplier` | count | None |  |
| `terms[].interestAccrualFrequency.on` | enum | None |  |
| `terms[].interestAccrualFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].interestAccrualFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].interestAccrualFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].interestAccrualFrequency.repetitions` | count | None |  |
| `terms[].interestAccrualFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].interestAccrualFrequency.startDate` | date | None |  |
| `terms[].interestCalculationPeriodType` | enum | None |  |
| `terms[].interestFloatDays` | count | None | interest float days |
| `terms[].interestGrace[].endDate` | date | (empty_list) |  |
| `terms[].interestGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `terms[].interestGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `terms[].interestGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `terms[].interestGrace[].startDate` | date | (empty_list) |  |
| `terms[].interestGrace[].timeInterval` | enum | (empty_list) |  |
| `terms[].interestGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `terms[].interestRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].interestRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].interestRepaymentFrequency.daysOffset` | count | None |  |
| `terms[].interestRepaymentFrequency.endDate` | date | None |  |
| `terms[].interestRepaymentFrequency.every` | enum | Month |  |
| `terms[].interestRepaymentFrequency.everyMultiplier` | count | 1 |  |
| `terms[].interestRepaymentFrequency.on` | enum | Start |  |
| `terms[].interestRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].interestRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].interestRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].interestRepaymentFrequency.repetitions` | count | None |  |
| `terms[].interestRepaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].interestRepaymentFrequency.startDate` | date | None |  |
| `terms[].interestType` | enum | FlatOnApprovedAmount |  |
| `terms[].maturityDate` | date | None | **term maturity date** — Per-term maturity; loan-level maturity is endDate |
| `terms[].minDaysToFirstRepayment` | count | None |  |
| `terms[].minimumBalanceForInterestAccrual` | money | None | minimum balance for interest accrual |
| `terms[].netPrincipal` | money | None | net principal |
| `terms[].partialPeriodDaysInYear` | count | None | day-count basis — Day-count convention driver |
| `terms[].principalAmortizationDeterminationEvent` | enum | None |  |
| `terms[].principalGrace[].endDate` | date | (empty_list) |  |
| `terms[].principalGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `terms[].principalGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `terms[].principalGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `terms[].principalGrace[].startDate` | date | (empty_list) |  |
| `terms[].principalGrace[].timeInterval` | enum | (empty_list) |  |
| `terms[].principalGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `terms[].principalRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `terms[].principalRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `terms[].principalRepaymentFrequency.daysOffset` | count | None |  |
| `terms[].principalRepaymentFrequency.endDate` | date | None |  |
| `terms[].principalRepaymentFrequency.every` | enum | Month |  |
| `terms[].principalRepaymentFrequency.everyMultiplier` | count | 12 |  |
| `terms[].principalRepaymentFrequency.on` | enum | None |  |
| `terms[].principalRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `terms[].principalRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `terms[].principalRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `terms[].principalRepaymentFrequency.repetitions` | count | 1 |  |
| `terms[].principalRepaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `terms[].principalRepaymentFrequency.startDate` | date | 2025-02-07 |  |
| `terms[].proposedPrincipal` | money | 30,000,000 | proposed principal |
| `terms[].revolvingPeriod.endDate` | date | None | revolving period end |
| `terms[].revolvingPeriod.relativeStartDate.amount` | count | None |  |
| `terms[].revolvingPeriod.relativeStartDate.timeUnit` | enum | None |  |
| `terms[].revolvingPeriod.relativeStartDate.type` | enum | None |  |
| `terms[].revolvingPeriod.startDate` | date | None |  |
| `terms[].revolvingPeriod.timeInterval` | enum | None |  |
| `terms[].revolvingPeriod.timeIntervalMultiplier` | count | None |  |

### `valuations[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `valuations[].currency` | enum | (empty_list) |  |
| `valuations[].date` | date | (empty_list) | valuation date |
| `valuations[].valuation` | money | (empty_list) | **collateral valuation** — Empty for this loan; the appraisal/AsIs value used for LTV \| This is an absolute collateral value in money (appraisal / As-Is dollars), NOT an LTV ratio — the figure tag 'ltv' is misleading. LTV must be COMPUTED as outstanding/valuation; never render this dollar value as a percent. |

## Investor position (LoanFunding)

- Root: `LoanFunding` · RELIABLE — loanFundings 2-step (assetId→loanFundingId); dual-filter 500s
- Probe entity: `{"id": "338", "name": null}`
- 1037 askable value fields shown (458 bool/text fields in YAML only)

### `_direct`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `commitmentAmount` | money | 3,000,000 | **funding commitment amount** |
| `commitmentAmountInFundingEntityCurrency` | money | 3,000,000 | funding commitment (funder currency) — FX-converted twin of commitmentAmount; equals it when funder currency == loan currency |
| `currency` | enum | USD | funding currency |
| `currentCompoundingInterestRate` | rate | None | current compounding (PIK) rate — Percent not fraction; null when no compounding/PIK component on this funding |
| `currentInterestRate` | rate | 14 | **current interest rate** — Percent not fraction (14 means 14%); a value >1 is a percent |
| `currentOidRemainingCost` | money | None | current OID remaining cost — null when no OID terms attached |
| `duesCalculationMethod` | enum | AfterDisbursement | dues calculation method — Enum (e.g. AfterDisbursement); config not a number |
| `fileEntriesCount` | count | 0 | file entries count — Plumbing count |
| `participationPercentage` | rate | 5.26 | **participation percentage** — Percent not fraction (5.26 means 5.26%); it is share of the loan, not an interest rate |

### `cashReceived`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `cashReceived.accruedCompoundingInterest` | money | None | accrued compounding interest received — null when no PIK component |
| `cashReceived.compoundingInterest` | money | 0 | compounding interest received |
| `cashReceived.fees[].amount` | money | (empty_list) |  |
| `cashReceived.fees[].compoundingAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.calculationType` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `cashReceived.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.dueDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.minAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.outstanding` | money | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.ratePer` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `cashReceived.fees[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.timing` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.totalDue` | money | (empty_list) |  |
| `cashReceived.fees[].fee.value` | money | (empty_list) |  |
| `cashReceived.fees[].periodCharge` | money | (empty_list) |  |
| `cashReceived.indexedPrincipal` | money | None | indexed principal received — null unless principal is index-linked |
| `cashReceived.interest` | money | 157,500 | **interest cash received** |
| `cashReceived.penalties[].amount` | money | (empty_list) |  |
| `cashReceived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.dueDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.minAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.outstanding` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.timing` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.totalDue` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.value` | money | (empty_list) |  |
| `cashReceived.penalties[].periodCharge` | money | (empty_list) |  |
| `cashReceived.principal` | money | 0 | **principal cash received** — This is a component of cashReceived.total (which already nets principal + interest + fee/credit components). Do NOT add cashReceived.principal to cashReceived.total or sum the children alongside the parent — that double-counts. Pick the parent OR the components, never both. |
| `cashReceived.total` | money | 157,500 | **cash received total (net)** — Net of fee/credit components; use .principal for an interest basis, not .total |
| `cashReceived.totalFees` | money | 0 | fees received |
| `cashReceived.totalPenalties` | money | 0 | penalties received |
| `cashReceived.totalTaxes` | money | 0 | taxes received |
| `cashReceived.totalWithTaxes` | money | 157,500 | cash received incl. taxes — Gross-of-tax variant of cashReceived.total |

### `compoundingInterestRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `compoundingInterestRatesData[].baseRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].effectiveDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].finalRate` | rate | (empty_list) | compounding rate history - final rate — Percent not fraction; PIK rate history (empty here) |
| `compoundingInterestRatesData[].floatingRateDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].fromDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].margin` | money | (empty_list) |  |
| `compoundingInterestRatesData[].maxRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].minRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].ratePer` | enum | (empty_list) |  |
| `compoundingInterestRatesData[].updateEndDate` | date | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMargin` | money | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMaxRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].updatedMinRate` | rate | (empty_list) |  |
| `compoundingInterestRatesData[].updatedRate` | rate | (empty_list) |  |

### `deal`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `deal.chatMessages[].role` | enum | (absent) |  |
| `deal.chatMessages[].timestamp` | date | (absent) |  |
| `deal.createdAt` | date | (absent) |  |
| `deal.facilitySize` | money | (absent) | deal facility size — On parent deal (absent for this funding); whole-loan, not the funder's share |
| `deal.files[].createdAt` | date | (absent) |  |
| `deal.files[].deletedAt` | date | (absent) |  |
| `deal.files[].entityType` | enum | (absent) |  |
| `deal.files[].extraction.extractionStatus` | enum | (absent) |  |
| `deal.files[].sizeInBytes` | count | (absent) |  |
| `deal.files[].updatedAt` | date | (absent) |  |
| `deal.status` | enum | (absent) | deal status — Enum; on parent deal |
| `deal.updatedAt` | date | (absent) |  |

### `debtSell[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `debtSell[].amount` | money | (empty_list) | debt sale amount |
| `debtSell[].currency` | enum | (empty_list) |  |
| `debtSell[].date` | date | (empty_list) | debt sale date — empty for this entity; array of secondary sales |
| `debtSell[].effectiveDate` | date | (empty_list) | debt sale effective date |
| `debtSell[].sellComponents[].buyerPostSell` | money | (empty_list) | buyer post-sale balance (component) — Per-component |
| `debtSell[].sellComponents[].name` | enum | (empty_list) |  |
| `debtSell[].sellComponents[].sellerPostSell` | money | (empty_list) | seller post-sale balance (component) — Per-component (principal/interest/etc.) |
| `debtSell[].sellComponents[].sellerPreSell` | money | (empty_list) |  |
| `debtSell[].sellPercentage` | rate | (empty_list) | debt sale percent — Percent not fraction |
| `debtSell[].status` | enum | (empty_list) | debt sale status — Enum |

### `fees[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `fees[].allocationPercentage` | rate | None | fee allocation percent to funder — Percent not fraction; funder's share of the fee |
| `fees[].assetFee.accrualFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].assetFee.accrualFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].assetFee.accrualFrequency.daysOffset` | count | None |  |
| `fees[].assetFee.accrualFrequency.endDate` | date | None |  |
| `fees[].assetFee.accrualFrequency.every` | enum | None |  |
| `fees[].assetFee.accrualFrequency.everyMultiplier` | count | None |  |
| `fees[].assetFee.accrualFrequency.on` | enum | None |  |
| `fees[].assetFee.accrualFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].assetFee.accrualFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].assetFee.accrualFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].assetFee.accrualFrequency.repetitions` | count | None |  |
| `fees[].assetFee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].assetFee.accrualFrequency.startDate` | date | None |  |
| `fees[].assetFee.calculationType` | enum | Flat | fee calculation type — Tells whether assetFee.value is money or a percent |
| `fees[].assetFee.chargeDate` | date | 2026-05-14 | fee charge date |
| `fees[].assetFee.chargeFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].assetFee.chargeFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].assetFee.chargeFrequency.daysOffset` | count | None |  |
| `fees[].assetFee.chargeFrequency.endDate` | date | None |  |
| `fees[].assetFee.chargeFrequency.every` | enum | None |  |
| `fees[].assetFee.chargeFrequency.everyMultiplier` | count | None |  |
| `fees[].assetFee.chargeFrequency.on` | enum | None |  |
| `fees[].assetFee.chargeFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].assetFee.chargeFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].assetFee.chargeFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].assetFee.chargeFrequency.repetitions` | count | None |  |
| `fees[].assetFee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].assetFee.chargeFrequency.startDate` | date | None |  |
| `fees[].assetFee.chargePeriod.endDate` | date | None |  |
| `fees[].assetFee.chargePeriod.relativeStartDate.amount` | count | None |  |
| `fees[].assetFee.chargePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].assetFee.chargePeriod.relativeStartDate.type` | enum | None |  |
| `fees[].assetFee.chargePeriod.startDate` | date | None |  |
| `fees[].assetFee.chargePeriod.timeInterval` | enum | None |  |
| `fees[].assetFee.chargePeriod.timeIntervalMultiplier` | count | None |  |
| `fees[].assetFee.chargeTiming` | enum | SpecificDate |  |
| `fees[].assetFee.compoundingFeeCapitalizationComponent` | enum | None |  |
| `fees[].assetFee.compoundingFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].assetFee.compoundingFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].assetFee.compoundingFrequency.daysOffset` | count | None |  |
| `fees[].assetFee.compoundingFrequency.endDate` | date | None |  |
| `fees[].assetFee.compoundingFrequency.every` | enum | None |  |
| `fees[].assetFee.compoundingFrequency.everyMultiplier` | count | None |  |
| `fees[].assetFee.compoundingFrequency.on` | enum | None |  |
| `fees[].assetFee.compoundingFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].assetFee.compoundingFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].assetFee.compoundingFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].assetFee.compoundingFrequency.repetitions` | count | None |  |
| `fees[].assetFee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].assetFee.compoundingFrequency.startDate` | date | None |  |
| `fees[].assetFee.depositConditions` | enum | None |  |
| `fees[].assetFee.depositNumberOfRepayments` | count | None |  |
| `fees[].assetFee.depositPaysFor` | enum | None |  |
| `fees[].assetFee.dueDate` | date | None | fee due date |
| `fees[].assetFee.duesCalculationMethod` | enum | None |  |
| `fees[].assetFee.feePeriod.endDate` | date | None |  |
| `fees[].assetFee.feePeriod.relativeStartDate.amount` | count | None |  |
| `fees[].assetFee.feePeriod.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].assetFee.feePeriod.relativeStartDate.type` | enum | None |  |
| `fees[].assetFee.feePeriod.startDate` | date | None |  |
| `fees[].assetFee.feePeriod.timeInterval` | enum | None |  |
| `fees[].assetFee.feePeriod.timeIntervalMultiplier` | count | None |  |
| `fees[].assetFee.fixedRepaymentAmount` | money | None |  |
| `fees[].assetFee.minAmount` | money | None | fee minimum amount — null when no floor |
| `fees[].assetFee.oidRecognitionStartDate` | date | None |  |
| `fees[].assetFee.outstanding` | money | 0 | fee outstanding |
| `fees[].assetFee.penaltyGrace.endDate` | date | None |  |
| `fees[].assetFee.penaltyGrace.relativeStartDate.amount` | count | None |  |
| `fees[].assetFee.penaltyGrace.relativeStartDate.timeUnit` | enum | None |  |
| `fees[].assetFee.penaltyGrace.relativeStartDate.type` | enum | None |  |
| `fees[].assetFee.penaltyGrace.startDate` | date | None |  |
| `fees[].assetFee.penaltyGrace.timeInterval` | enum | None |  |
| `fees[].assetFee.penaltyGrace.timeIntervalMultiplier` | count | None |  |
| `fees[].assetFee.ratePer` | enum | None |  |
| `fees[].assetFee.repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `fees[].assetFee.repaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `fees[].assetFee.repaymentFrequency.daysOffset` | count | None |  |
| `fees[].assetFee.repaymentFrequency.endDate` | date | None |  |
| `fees[].assetFee.repaymentFrequency.every` | enum | None |  |
| `fees[].assetFee.repaymentFrequency.everyMultiplier` | count | None |  |
| `fees[].assetFee.repaymentFrequency.on` | enum | None |  |
| `fees[].assetFee.repaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `fees[].assetFee.repaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `fees[].assetFee.repaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `fees[].assetFee.repaymentFrequency.repetitions` | count | None |  |
| `fees[].assetFee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `fees[].assetFee.repaymentFrequency.startDate` | date | None |  |
| `fees[].assetFee.repaymentTiming` | enum | OnRepayment | fee repayment timing — Enum |
| `fees[].assetFee.secondaryValue` | money | None |  |
| `fees[].assetFee.timeIntervalToEffectiveValue.timeInterval` | enum | None |  |
| `fees[].assetFee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | None |  |
| `fees[].assetFee.timing` | enum | OnRepayment |  |
| `fees[].assetFee.totalDue` | money | 85,921.64 | fee total due |
| `fees[].assetFee.value` | money | 85,921.64 | **fee value** — For Flat calc this is a money amount; for Percentage calc it is a percent — check calculationType \| Polymorphic by calculationType: Flat => a money amount; Percentage => a percent (not a fraction, and not dollars). MUST branch on calculationType before using or summing — never aggregate Flat and Percentage values together, and never treat a Percentage value as a dollar fee. |
| `fees[].fixedAmountToAllocate` | money | None | fixed fee amount to funder — Alternative to allocationPercentage |
| `fees[].value` | money | None |  |

### `interestRatesData[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `interestRatesData[].baseRate` | rate | (empty_list) | interest rate history - base rate — Percent not fraction |
| `interestRatesData[].effectiveDate` | date | (empty_list) | rate change effective date |
| `interestRatesData[].finalRate` | rate | (empty_list) | interest rate history - final rate — Percent not fraction; versioned rate history (empty for this entity) |
| `interestRatesData[].floatingRateDate` | date | (empty_list) |  |
| `interestRatesData[].fromDate` | date | (empty_list) |  |
| `interestRatesData[].margin` | money | (empty_list) | interest rate history - margin — Spread over base; typed money but is a rate component (percent) \| Margin is a rate spread (percent, e.g. 3.5 = 3.50%) carried in a money type. NEVER treat as a dollar amount or sum; combine with baseRate to reconstruct finalRate. Confirm it is not already a fraction by cross-checking baseRate + margin ≈ finalRate. |
| `interestRatesData[].maxRate` | rate | (empty_list) |  |
| `interestRatesData[].minRate` | rate | (empty_list) |  |
| `interestRatesData[].ratePer` | enum | (empty_list) |  |
| `interestRatesData[].updateEndDate` | date | (empty_list) |  |
| `interestRatesData[].updatedMargin` | money | (empty_list) |  |
| `interestRatesData[].updatedMaxRate` | rate | (empty_list) |  |
| `interestRatesData[].updatedMinRate` | rate | (empty_list) |  |
| `interestRatesData[].updatedRate` | rate | (empty_list) |  |

### `loanFundingTerms[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `loanFundingTerms[].amortizationType` | enum | None | amortization type — Enum |
| `loanFundingTerms[].approvedPrincipal` | money | None | **approved principal** |
| `loanFundingTerms[].approvedPrincipalInBaseCurrency` | money | None | approved principal (base currency) — FX twin of approvedPrincipal |
| `loanFundingTerms[].capitalizationComponent` | enum | None | capitalization component — Enum config |
| `loanFundingTerms[].commitmentExpirationDate` | date | None | commitment expiration date |
| `loanFundingTerms[].compoundingInterestFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.daysOffset` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.endDate` | date | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.every` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.everyMultiplier` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.on` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.relativeStartDate.amount` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.relativeStartDate.type` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.repetitions` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.specificDates[]` | date | (absent) |  |
| `loanFundingTerms[].compoundingInterestFrequency.startDate` | date | (absent) |  |
| `loanFundingTerms[].compoundingInterestGrace[].endDate` | date | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].startDate` | date | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.daysOffset` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.endDate` | date | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.every` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.everyMultiplier` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.on` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.repetitions` | count | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.specificDates[]` | date | (absent) |  |
| `loanFundingTerms[].compoundingInterestRepaymentFrequency.startDate` | date | (absent) |  |
| `loanFundingTerms[].customPrincipalAmortization[].amortizationType` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].date` | date | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].fixedRepaymentAmount` | money | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].percentageOfAmountToAmortize` | rate | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.every` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.on` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.repetitions` | count | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].repaymentFrequency.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].customPrincipalAmortization[].type` | enum | (empty_list) |  |
| `loanFundingTerms[].date` | date | 2025-06-26 | funding terms effective-as-of date — loanFundingTerms is a versioned array; latest row = current terms |
| `loanFundingTerms[].decreasedCompoundingPaymentLimit` | money | None | decreased compounding payment limit — Niche PIK config |
| `loanFundingTerms[].decreasedCompoundingPaymentPercentage` | rate | None | decreased compounding payment percent — Percent not fraction; niche PIK config |
| `loanFundingTerms[].disbursementDayInMonthForRepaymentsDelay` | count | None |  |
| `loanFundingTerms[].effectiveDate` | date | None |  |
| `loanFundingTerms[].expectedScheduleEndDate` | date | None | expected schedule end date — Projected, may differ from maturityDate |
| `loanFundingTerms[].fees[].accrualFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.daysOffset` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.every` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.on` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.repetitions` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].accrualFrequency.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].calculationType` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.daysOffset` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.every` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.on` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.repetitions` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeFrequency.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].chargeTiming` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.every` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.on` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.repetitions` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].compoundingFrequency.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].depositConditions` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].depositNumberOfRepayments` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].depositPaysFor` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].dueDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].duesCalculationMethod` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].fixedRepaymentAmount` | money | (empty_list) |  |
| `loanFundingTerms[].fees[].minAmount` | money | (empty_list) |  |
| `loanFundingTerms[].fees[].oidRecognitionStartDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].outstanding` | money | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].ratePer` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.daysInEvery.daysInEveryNumber` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.daysInEvery.daysInEveryType` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.endDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.every` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.on` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.repetitions` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentFrequency.startDate` | date | (empty_list) |  |
| `loanFundingTerms[].fees[].repaymentTiming` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].secondaryValue` | money | (empty_list) |  |
| `loanFundingTerms[].fees[].timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].fees[].timing` | enum | (empty_list) |  |
| `loanFundingTerms[].fees[].totalDue` | money | (empty_list) |  |
| `loanFundingTerms[].fees[].value` | money | (empty_list) |  |
| `loanFundingTerms[].fixedRepaymentAmount` | money | None | fixed repayment amount — null unless fixed/level amortization |
| `loanFundingTerms[].fundingSourcesNumberOfDelayedPrincipalRepayments` | count | None |  |
| `loanFundingTerms[].fundingSourcesPrincipalRepaymentDelay.timeInterval` | enum | None |  |
| `loanFundingTerms[].fundingSourcesPrincipalRepaymentDelay.timeIntervalMultiplier` | count | None |  |
| `loanFundingTerms[].fundingTerms.commitmentAmount` | money | 3,000,000 | funding terms commitment amount — Mirrors top-level commitmentAmount |
| `loanFundingTerms[].fundingTerms.seniority` | count | None | seniority rank — Integer rank, not money |
| `loanFundingTerms[].interestAccrualFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `loanFundingTerms[].interestAccrualFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `loanFundingTerms[].interestAccrualFrequency.daysOffset` | count | None |  |
| `loanFundingTerms[].interestAccrualFrequency.endDate` | date | None |  |
| `loanFundingTerms[].interestAccrualFrequency.every` | enum | None |  |
| `loanFundingTerms[].interestAccrualFrequency.everyMultiplier` | count | None |  |
| `loanFundingTerms[].interestAccrualFrequency.on` | enum | None |  |
| `loanFundingTerms[].interestAccrualFrequency.relativeStartDate.amount` | count | (absent) |  |
| `loanFundingTerms[].interestAccrualFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `loanFundingTerms[].interestAccrualFrequency.relativeStartDate.type` | enum | (absent) |  |
| `loanFundingTerms[].interestAccrualFrequency.repetitions` | count | None |  |
| `loanFundingTerms[].interestAccrualFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].interestAccrualFrequency.startDate` | date | None |  |
| `loanFundingTerms[].interestCalculationPeriodType` | enum | None | interest calc period type — Enum config |
| `loanFundingTerms[].interestFloatDays` | count | None | interest float days — Day count, not money |
| `loanFundingTerms[].interestGrace[].endDate` | date | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].startDate` | date | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].interestGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].interestRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.daysOffset` | count | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.endDate` | date | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.every` | enum | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.everyMultiplier` | count | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.on` | enum | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.repetitions` | count | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.specificDates[]` | date | (absent) |  |
| `loanFundingTerms[].interestRepaymentFrequency.startDate` | date | (absent) |  |
| `loanFundingTerms[].interestType` | enum | DecliningBalance | interest type — Enum (e.g. DecliningBalance) |
| `loanFundingTerms[].maturityDate` | date | None | **maturity date** — On the terms array; take the current/latest terms row |
| `loanFundingTerms[].minDaysToFirstRepayment` | count | None | min days to first repayment — Count |
| `loanFundingTerms[].minimumBalanceForInterestAccrual` | money | None | minimum balance for interest accrual |
| `loanFundingTerms[].netPrincipal` | money | None | net principal — Net of OID/upfront deductions |
| `loanFundingTerms[].partialPeriodDaysInYear` | count | None | day-count days-in-year — Day-count config; affects per-diem |
| `loanFundingTerms[].principalAmortizationDeterminationEvent` | enum | None |  |
| `loanFundingTerms[].principalGrace[].endDate` | date | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].relativeStartDate.amount` | count | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].relativeStartDate.type` | enum | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].startDate` | date | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].timeInterval` | enum | (empty_list) |  |
| `loanFundingTerms[].principalGrace[].timeIntervalMultiplier` | count | (empty_list) |  |
| `loanFundingTerms[].principalRepaymentFrequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `loanFundingTerms[].principalRepaymentFrequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `loanFundingTerms[].principalRepaymentFrequency.daysOffset` | count | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.endDate` | date | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.every` | enum | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.everyMultiplier` | count | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.on` | enum | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.relativeStartDate.amount` | count | (absent) |  |
| `loanFundingTerms[].principalRepaymentFrequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `loanFundingTerms[].principalRepaymentFrequency.relativeStartDate.type` | enum | (absent) |  |
| `loanFundingTerms[].principalRepaymentFrequency.repetitions` | count | None |  |
| `loanFundingTerms[].principalRepaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `loanFundingTerms[].principalRepaymentFrequency.startDate` | date | None |  |
| `loanFundingTerms[].proposedPrincipal` | money | None | proposed principal — Pre-approval figure |
| `loanFundingTerms[].revolvingPeriod.endDate` | date | None | revolving period end |
| `loanFundingTerms[].revolvingPeriod.relativeStartDate.amount` | count | None |  |
| `loanFundingTerms[].revolvingPeriod.relativeStartDate.timeUnit` | enum | None |  |
| `loanFundingTerms[].revolvingPeriod.relativeStartDate.type` | enum | None |  |
| `loanFundingTerms[].revolvingPeriod.startDate` | date | None | revolving period start |
| `loanFundingTerms[].revolvingPeriod.timeInterval` | enum | None |  |
| `loanFundingTerms[].revolvingPeriod.timeIntervalMultiplier` | count | None |  |

### `oidTerms`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `oidTerms.components[].createdAt` | date | (empty_list) |  |
| `oidTerms.components[].date` | date | (empty_list) |  |
| `oidTerms.components[].initialAmortizedAmount` | money | (empty_list) |  |
| `oidTerms.components[].type` | enum | (empty_list) |  |
| `oidTerms.components[].value` | money | (empty_list) | OID component value — Per-component OID amount (empty here) |
| `oidTerms.date` | date | None | OID terms date |
| `oidTerms.daysInMonth` | enum | Actual |  |
| `oidTerms.daysInYear` | enum | Actual | OID days-in-year basis — Enum (e.g. Actual) |
| `oidTerms.frequency.daysInEvery.daysInEveryNumber` | count | (absent) |  |
| `oidTerms.frequency.daysInEvery.daysInEveryType` | enum | (absent) |  |
| `oidTerms.frequency.daysOffset` | count | None |  |
| `oidTerms.frequency.endDate` | date | None |  |
| `oidTerms.frequency.every` | enum | None |  |
| `oidTerms.frequency.everyMultiplier` | count | None |  |
| `oidTerms.frequency.on` | enum | None |  |
| `oidTerms.frequency.relativeStartDate.amount` | count | (absent) |  |
| `oidTerms.frequency.relativeStartDate.timeUnit` | enum | (absent) |  |
| `oidTerms.frequency.relativeStartDate.type` | enum | (absent) |  |
| `oidTerms.frequency.repetitions` | count | None |  |
| `oidTerms.frequency.specificDates[]` | date | (empty_list) |  |
| `oidTerms.frequency.startDate` | date | None |  |
| `oidTerms.fundingTerms.components[].allocationType` | enum | (empty_list) |  |
| `oidTerms.fundingTerms.components[].allocationValue` | money | (empty_list) |  |
| `oidTerms.fundingTerms.components[].assetComponent.createdAt` | date | (empty_list) |  |
| `oidTerms.fundingTerms.components[].assetComponent.date` | date | (empty_list) |  |
| `oidTerms.fundingTerms.components[].assetComponent.initialAmortizedAmount` | money | (empty_list) |  |
| `oidTerms.fundingTerms.components[].assetComponent.type` | enum | (empty_list) |  |
| `oidTerms.fundingTerms.components[].assetComponent.value` | money | (empty_list) |  |
| `oidTerms.method` | enum | None | OID amortization method — Enum config |
| `oidTerms.nonAccrualPeriods[].endDate` | date | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.amount` | count | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.timeUnit` | enum | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].relativeStartDate.type` | enum | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].startDate` | date | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].timeInterval` | enum | (empty_list) |  |
| `oidTerms.nonAccrualPeriods[].timeIntervalMultiplier` | count | (empty_list) |  |

### `receivables`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `receivables.accruedCompoundingInterest` | money | None | accrued compounding interest receivable — null when no PIK component |
| `receivables.compoundingInterest` | money | 0 | compounding interest receivable |
| `receivables.fees[].amount` | money | (empty_list) |  |
| `receivables.fees[].compoundingAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.calculationType` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `receivables.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `receivables.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `receivables.fees[].fee.dueDate` | date | (empty_list) |  |
| `receivables.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.minAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `receivables.fees[].fee.outstanding` | money | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.ratePer` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `receivables.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `receivables.fees[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.timing` | enum | (empty_list) |  |
| `receivables.fees[].fee.totalDue` | money | (empty_list) |  |
| `receivables.fees[].fee.value` | money | (empty_list) |  |
| `receivables.fees[].periodCharge` | money | (empty_list) |  |
| `receivables.indexedPrincipal` | money | None | indexed principal receivable — null unless index-linked |
| `receivables.interest` | money | 260,890.51 | **interest receivable** |
| `receivables.penalties[].amount` | money | (empty_list) |  |
| `receivables.penalties[].compoundingAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `receivables.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `receivables.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `receivables.penalties[].fee.dueDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.minAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.outstanding` | money | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `receivables.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `receivables.penalties[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.timing` | enum | (empty_list) |  |
| `receivables.penalties[].fee.totalDue` | money | (empty_list) |  |
| `receivables.penalties[].fee.value` | money | (empty_list) |  |
| `receivables.penalties[].periodCharge` | money | (empty_list) |  |
| `receivables.principal` | money | 353,390.77 | **principal receivable** — Use this as the interest basis, not receivables.total \| Mapped to two different figures across the catalog: receivables.principal=funding_outstanding here, while repaymentSchedule.summary.totalDisbursed and outstandingPrincipalBeforeAmortization are also tagged funding_outstanding/principal_outstanding. These are different bases (gross disbursed vs. before-amortization vs. current net principal receivable) and must not be summed or treated as interchangeable. receivables.principal is also a child of receivables.total — never add it to the parent. |
| `receivables.total` | money | 854,281.28 | **total receivable (net)** — Net of fee/credit components; for an interest basis use .principal not .total |
| `receivables.totalFees` | money | 240,000 | fees receivable |
| `receivables.totalPenalties` | money | 0 | penalties receivable |
| `receivables.totalTaxes` | money | 0 | taxes receivable |
| `receivables.totalWithTaxes` | money | 854,281.28 | total receivable incl. taxes — Gross-of-tax variant of receivables.total |

### `repaymentSchedule`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `repaymentSchedule.agingAnalysis.cohorts[].numberOfDays` | count | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.accruedCompoundingInterest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.compoundingInterest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.indexedPrincipal` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.interest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.principal` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.total` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalFees` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalPenalties` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalTaxes` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.cohorts[].total.totalWithTaxes` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.accruedCompoundingInterest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.compoundingInterest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.fees[].amount` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.fees[].compoundingAmount` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.fees[].periodCharge` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.indexedPrincipal` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.interest` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].amount` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].compoundingAmount` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.penalties[].periodCharge` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.principal` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.total` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.totalFees` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.totalPenalties` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.totalTaxes` | money | (absent) |  |
| `repaymentSchedule.agingAnalysis.total.totalWithTaxes` | money | (absent) |  |
| `repaymentSchedule.expectedDeployments[].commitment` | money | (empty_list) |  |
| `repaymentSchedule.expectedDeployments[].date` | date | (empty_list) |  |
| `repaymentSchedule.expectedDeployments[].deployment` | money | (empty_list) |  |
| `repaymentSchedule.loanKPIs.dpi` | money | 0.3372604261 | **DPI** — Ratio/multiple, not money despite money type \| DPI is a dimensionless multiple (e.g. 1.25x) carried in a money type. NEVER format as currency or sum across fundings; aggregating requires recomputing from distributions/paid-in, not adding DPIs. |
| `repaymentSchedule.loanKPIs.dpiIncludingEquity` | money | 0.3372604261 | DPI including equity — Ratio; equity permutation |
| `repaymentSchedule.loanKPIs.expectedDpi` | money | 1.22 | expected DPI — Ratio; projection |
| `repaymentSchedule.loanKPIs.expectedDpiIncludingEquity` | money | 1.22 | expected DPI including equity — Ratio; projection + equity permutation |
| `repaymentSchedule.loanKPIs.expectedIrr` | money | -29.96 | expected IRR — Percent not fraction; projection, can be negative |
| `repaymentSchedule.loanKPIs.expectedIrrIncludingEquity` | money | -29.96 | expected IRR including equity — Percent; projection + equity permutation |
| `repaymentSchedule.loanKPIs.expectedTvpi` | money | 1.22 | expected TVPI — Ratio; projection |
| `repaymentSchedule.loanKPIs.expectedTvpiIncludingEquity` | money | 1.22 | expected TVPI including equity — Ratio; projection + equity permutation |
| `repaymentSchedule.loanKPIs.irr` | money | 13.69 | **IRR (funder)** — Percent not fraction (13.69 = 13.69%); a money-typed KPI but it is a rate \| IRR is a percent (13.69 = 13.69%) carried in a money-typed field. NEVER sum, average unweighted, or roll it up across fundings as if it were currency, and never format with a currency symbol. It is a per-funding rate. |
| `repaymentSchedule.loanKPIs.irrIncludingEquity` | money | 13.69 | IRR including equity — Percent not fraction; equity-inclusive permutation |
| `repaymentSchedule.loanKPIs.tvpi` | money | 0.6315051115 | **TVPI** — Ratio/multiple, not money despite money type \| TVPI is a dimensionless multiple (e.g. 1.40x) carried in a money type. NEVER format as currency or sum across fundings; aggregate by recomputing (distributed+residual)/paid-in, not by adding TVPIs. |
| `repaymentSchedule.loanKPIs.tvpiIncludingEquity` | money | 0.6315051115 | TVPI including equity — Ratio; equity permutation |
| `repaymentSchedule.scheduleTable[].baseCurrencyExchangeRate` | rate | None |  |
| `repaymentSchedule.scheduleTable[].compoundingChargedOnPeriod` | money | None | compounding charged in period — null when no PIK |
| `repaymentSchedule.scheduleTable[].compoundingInterestRate` | rate | None |  |
| `repaymentSchedule.scheduleTable[].compoundingRatePer` | enum | Year |  |
| `repaymentSchedule.scheduleTable[].date` | date | 2025-06-26 | schedule row date — Per-row in the amortization schedule array |
| `repaymentSchedule.scheduleTable[].disbursedAmount` | money | None | row disbursed amount — Only populated on disbursement rows |
| `repaymentSchedule.scheduleTable[].due.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.compoundingInterest` | money | 0 | compounding due (row) — null/0 when no PIK |
| `repaymentSchedule.scheduleTable[].due.fees[].amount` | money | 150,000 | due fee amount (row) — Itemized fee within the row's due |
| `repaymentSchedule.scheduleTable[].due.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].due.interest` | money | 0 | **interest due (row) / per-diem** — On an accrual row this 'due' interest is the per-diem (daily accrual); not cumulative \| On an accrual row 'due interest' is the PER-DIEM (daily accrual rate), but on a payment/installment row the same field is the interest actually due that period. The meaning flips by row type — do not treat all rows uniformly, and never sum per-diem rows with payment-due rows. |
| `repaymentSchedule.scheduleTable[].due.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].due.principal` | money | 3,000,000 | principal due (row) |
| `repaymentSchedule.scheduleTable[].due.total` | money | 3,150,000 | amount due (row, net) — Net of fee/credit components; an accrual row's 'due' on a daily row is the per-diem |
| `repaymentSchedule.scheduleTable[].due.totalFees` | money | 150,000 | fees due (row) |
| `repaymentSchedule.scheduleTable[].due.totalPenalties` | money | 0 | penalties due (row) |
| `repaymentSchedule.scheduleTable[].due.totalTaxes` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].due.totalWithTaxes` | money | 3,150,000 |  |
| `repaymentSchedule.scheduleTable[].effectiveDate` | date | 2025-06-26 | schedule row effective date |
| `repaymentSchedule.scheduleTable[].index` | count | 0 |  |
| `repaymentSchedule.scheduleTable[].interestChargedOnPeriod` | money | None | interest charged in period — Per-row period interest; not cumulative |
| `repaymentSchedule.scheduleTable[].interestRate` | rate | 14 | row interest rate — Percent not fraction (14 = 14%) |
| `repaymentSchedule.scheduleTable[].nonCapitalizedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.amount` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].amortized` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.breakdown[].unamortized` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].oid.indexedRemainingCost` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.rate` | rate | None |  |
| `repaymentSchedule.scheduleTable[].oid.remainingCost` | money | None |  |
| `repaymentSchedule.scheduleTable[].oid.totalWithInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.capitalizedBalance` | money | 3,000,000 | capitalized balance memo (row) — NON-additive memo field; equals principal — do not add to other balances |
| `repaymentSchedule.scheduleTable[].outstanding.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].amount` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].outstanding.interest` | money | 1,166.67 | outstanding interest (row) |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].outstanding.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].outstanding.principal` | money | 3,000,000 | outstanding principal (row) |
| `repaymentSchedule.scheduleTable[].outstanding.total` | money | 3,001,166.67 | outstanding (row, net) — Net of fee/credit components; use .principal for interest basis |
| `repaymentSchedule.scheduleTable[].outstanding.totalCompoundingInterest` | money | 0 | outstanding compounding interest (row) |
| `repaymentSchedule.scheduleTable[].outstanding.totalFees` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalPenalties` | money | 0 | outstanding penalties (row) |
| `repaymentSchedule.scheduleTable[].outstanding.totalTaxes` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].outstanding.totalWithTaxes` | money | 3,001,166.67 |  |
| `repaymentSchedule.scheduleTable[].paid.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].amount` | money | 150,000 |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].compoundingAmount` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.fees[].periodCharge` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].paid.interest` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].paid.principal` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.total` | money | 150,000 |  |
| `repaymentSchedule.scheduleTable[].paid.totalFees` | money | 150,000 |  |
| `repaymentSchedule.scheduleTable[].paid.totalPenalties` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.totalTaxes` | money | 0 |  |
| `repaymentSchedule.scheduleTable[].paid.totalWithTaxes` | money | 150,000 |  |
| `repaymentSchedule.scheduleTable[].principalRealizedBalance` | money | 3,000,000 | principal realized balance (row) — Snapshot balance at that schedule row |
| `repaymentSchedule.scheduleTable[].ratePer` | enum | Year |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.date` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.effectiveDate` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.effectiveFrom` | date | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.accruedCompoundingInterest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.compoundingInterest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.indexedPrincipal` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.interest` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.principal` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.total` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalFees` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalPenalties` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalTaxes` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.repaymentComponents.totalWithTaxes` | money | (absent) |  |
| `repaymentSchedule.scheduleTable[].relatedExpectedRepaymentUpdate.type` | enum | (absent) |  |
| `repaymentSchedule.scheduleTable[].type` | enum | Disbursement | schedule row type — Enum (Disbursement/Repayment/Accrual etc.); filter to find the right row |
| `repaymentSchedule.scheduleTable[].waived.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.compoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.interest` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].waived.principal` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.total` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalFees` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalPenalties` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].waived.totalWithTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.compoundingInterest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.indexedPrincipal` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.interest` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.scheduleTable[].writtenOff.principal` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.total` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalFees` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalPenalties` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalTaxes` | money | None |  |
| `repaymentSchedule.scheduleTable[].writtenOff.totalWithTaxes` | money | None |  |
| `repaymentSchedule.summary.compoundingInterestRate` | rate | None | schedule compounding rate — Percent not fraction; null when no PIK |
| `repaymentSchedule.summary.distributedPrincipal` | money | 353,390.77 | **distributed principal** |
| `repaymentSchedule.summary.exchangeRateImpact.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.exchangeRateImpact.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.exchangeRateImpact.interest` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.exchangeRateImpact.principal` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.total` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.exchangeRateImpact.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.expectedPaidInCapital` | money | 3,000,000 | expected paid-in capital — Projection, not actual |
| `repaymentSchedule.summary.interestRate` | rate | 14 | schedule interest rate — Percent not fraction (14 = 14%) |
| `repaymentSchedule.summary.oidRate` | rate | None | OID rate — Percent not fraction; null when no OID |
| `repaymentSchedule.summary.oidRemainingCost` | money | None | OID remaining cost (summary) — null when no OID |
| `repaymentSchedule.summary.outstandingPrincipalBeforeAmortization` | money | 2,646,609.23 | **outstanding principal before amortization** — Before amortization/paydown; differs from receivables.principal |
| `repaymentSchedule.summary.overdue.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.overdue.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.overdue.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.overdue.interest` | money | -208.36 |  |
| `repaymentSchedule.summary.overdue.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.overdue.principal` | money | 0 |  |
| `repaymentSchedule.summary.overdue.total` | money | -240,208.36 |  |
| `repaymentSchedule.summary.overdue.totalFees` | money | -240,000 |  |
| `repaymentSchedule.summary.overdue.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.overdue.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.overdue.totalWithTaxes` | money | -240,208.36 |  |
| `repaymentSchedule.summary.paidInCapital` | money | 3,000,000 | **paid-in capital** |
| `repaymentSchedule.summary.totalDisbursed` | money | 3,000,000 | **total disbursed (funder)** |
| `repaymentSchedule.summary.totalDue.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalDue.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalDue.interest` | money | -208.36 |  |
| `repaymentSchedule.summary.totalDue.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalDue.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.total` | money | -240,208.36 |  |
| `repaymentSchedule.summary.totalDue.totalFees` | money | -240,000 |  |
| `repaymentSchedule.summary.totalDue.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalDue.totalWithTaxes` | money | -240,208.36 |  |
| `repaymentSchedule.summary.totalExpected.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalExpected.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalExpected.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalExpected.interest` | money | 418,709.97 |  |
| `repaymentSchedule.summary.totalExpected.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpected.principal` | money | 3,000,000 |  |
| `repaymentSchedule.summary.totalExpected.total` | money | 3,663,432.19 |  |
| `repaymentSchedule.summary.totalExpected.totalFees` | money | 244,722.21 |  |
| `repaymentSchedule.summary.totalExpected.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalExpected.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalExpected.totalWithTaxes` | money | 3,663,432.19 |  |
| `repaymentSchedule.summary.totalExpectedDisbursements` | money | 3,000,000 | total expected disbursements — Projected/planned, not actuals |
| `repaymentSchedule.summary.totalExpectedToDate.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalExpectedToDate.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalExpectedToDate.interest` | money | 418,709.97 |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalExpectedToDate.principal` | money | 3,000,000 |  |
| `repaymentSchedule.summary.totalExpectedToDate.total` | money | 3,663,432.19 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalFees` | money | 244,722.21 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalExpectedToDate.totalWithTaxes` | money | 3,663,432.19 |  |
| `repaymentSchedule.summary.totalOID.amount` | money | 0 |  |
| `repaymentSchedule.summary.totalOID.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.capitalizedBalance` | money | 2,646,609.23 |  |
| `repaymentSchedule.summary.totalOutstanding.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalOutstanding.interest` | money | 319.46 |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalOutstanding.principal` | money | 2,646,609.23 |  |
| `repaymentSchedule.summary.totalOutstanding.total` | money | 882,734.06 |  |
| `repaymentSchedule.summary.totalOutstanding.totalCompoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.totalFees` | money | -1,764,194.64 |  |
| `repaymentSchedule.summary.totalOutstanding.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalOutstanding.totalWithTaxes` | money | 882,734.06 |  |
| `repaymentSchedule.summary.totalPaid.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalPaid.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalPaid.interest` | money | 418,390.51 |  |
| `repaymentSchedule.summary.totalPaid.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalPaid.principal` | money | 353,390.77 |  |
| `repaymentSchedule.summary.totalPaid.total` | money | 1,011,781.28 |  |
| `repaymentSchedule.summary.totalPaid.totalFees` | money | 240,000 |  |
| `repaymentSchedule.summary.totalPaid.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalPaid.totalWithTaxes` | money | 1,011,781.28 |  |
| `repaymentSchedule.summary.totalWaived.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalWaived.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalWaived.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWaived.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.total` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWaived.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.accruedCompoundingInterest` | money | None |  |
| `repaymentSchedule.summary.totalWrittenOff.compoundingInterest` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.fees[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.indexedPrincipal` | money | None |  |
| `repaymentSchedule.summary.totalWrittenOff.interest` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].amount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `repaymentSchedule.summary.totalWrittenOff.principal` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.total` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalFees` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalPenalties` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalTaxes` | money | 0 |  |
| `repaymentSchedule.summary.totalWrittenOff.totalWithTaxes` | money | 0 |  |
| `repaymentSchedule.summary.unutilizedPrincipal` | money | 353,390.77 | **unutilized principal** |
| `repaymentSchedule.updatedAt` | date | 2026-06-26T03:42:52.000Z | schedule last-updated timestamp — DateTime of last schedule recompute; use as the as-of/freshness stamp |

### `valuations[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `valuations[].currency` | enum | (empty_list) |  |
| `valuations[].date` | date | (empty_list) | valuation date |
| `valuations[].valuation` | money | (empty_list) | valuation amount — Array of valuations over time; empty for this entity |

## Funding entity / investor (portfolio)

- Root: `FundingEntity` · RELIABLE — fundingEntities(filter:{searchString}){ pageItems{…} }
- Probe entity: `{"id": "3", "name": "XL"}`
- 824 askable value fields shown (405 bool/text fields in YAML only)

### `_direct`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `activeLoansCount` | count | 7 | **active loans count** |
| `baseCurrency` | enum | USD | base currency |
| `contributed` | money | 0 | **contributed capital** |
| `currentAverageInterestRate` | rate | 9.35 | **current average interest rate** — Rate is a PERCENT not a fraction (e.g. 9.35 means 9.35%). |
| `expectedTotalValue` | money | 94,235,471.92 | **expected total value** |
| `fileEntriesCount` | count | 0 | file entries count |
| `lastScheduleUpdate` | date | 2026-06-26T03:44:53.000Z | last schedule update — As-of timestamp for the computed figures, not a loan date. |
| `totalCommitment` | money | 66,447,274.13 | **total commitment** |
| `totalDisbursement` | money | 70,948,768.30 | **total disbursement** |
| `totalReturned` | money | 73,519,721.54 | **total returned** |
| `utilizationRate` | rate | 106.77 | **utilization rate** — Percent not fraction; can exceed 100 (example 106.77) when disbursed > commitment. \| Percent, NOT a fraction (example 106.77 = 106.77%). Can exceed 100 when disbursed > commitment — do NOT clamp to 100% and do NOT divide by 100 expecting a 0-1 ratio without confirming the consumer wants a fraction. |

### `cashReceived`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `cashReceived.accruedCompoundingInterest` | money | None |  |
| `cashReceived.compoundingInterest` | money | 0 | cash received - compounding interest |
| `cashReceived.fees[].amount` | money | (empty_list) | cash-received fee line amount — Per-fee breakdown row; empty on this entity. |
| `cashReceived.fees[].compoundingAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.calculationType` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `cashReceived.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.dueDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.minAmount` | money | (empty_list) |  |
| `cashReceived.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.outstanding` | money | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.ratePer` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `cashReceived.fees[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.fees[].fee.timing` | enum | (empty_list) |  |
| `cashReceived.fees[].fee.totalDue` | money | (empty_list) |  |
| `cashReceived.fees[].fee.value` | money | (empty_list) |  |
| `cashReceived.fees[].periodCharge` | money | (empty_list) |  |
| `cashReceived.indexedPrincipal` | money | None | cash received - indexed principal |
| `cashReceived.interest` | money | 9,341,312.63 | **cash received - interest** |
| `cashReceived.penalties[].amount` | money | (empty_list) | cash-received penalty line amount — Per-penalty breakdown row; empty on this entity. |
| `cashReceived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.dueDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.minAmount` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.outstanding` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `cashReceived.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `cashReceived.penalties[].fee.timing` | enum | (empty_list) |  |
| `cashReceived.penalties[].fee.totalDue` | money | (empty_list) |  |
| `cashReceived.penalties[].fee.value` | money | (empty_list) |  |
| `cashReceived.penalties[].periodCharge` | money | (empty_list) |  |
| `cashReceived.principal` | money | 42,057,958.77 | **cash received - principal** |
| `cashReceived.total` | money | 51,963,383.66 | **cash received total** — Roll-up of cashReceived.principal + .interest + .compoundingInterest. Non-additive memo — do NOT sum it together with its component fields, and do NOT add it to other entities' .total unless de-duped. |
| `cashReceived.totalFees` | money | 564,112.26 | cash received - fees |
| `cashReceived.totalPenalties` | money | 0 | cash received - penalties |
| `cashReceived.totalTaxes` | money | 0 | cash received - taxes |
| `cashReceived.totalWithTaxes` | money | 51,963,383.66 | cash received incl. taxes — Memo total including tax line; equals .total here when taxes are 0. |

### `commitmentBreakdown`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `commitmentBreakdown.active.amount` | money | 15,825,000 | **active commitment amount** |
| `commitmentBreakdown.active.count` | count | 7 | active commitment loan count |
| `commitmentBreakdown.active.percentage` | rate | 23.82 | active commitment share — Percent of total commitment, not a fraction. |
| `commitmentBreakdown.closed.amount` | money | 50,622,274.13 | closed commitment amount |
| `commitmentBreakdown.closed.count` | count | 10 | closed commitment loan count |
| `commitmentBreakdown.closed.percentage` | rate | 76.18 | closed commitment share — Percent not fraction. |
| `commitmentBreakdown.pending.amount` | money | 0 | pending commitment amount |
| `commitmentBreakdown.pending.count` | count | 0 | pending commitment loan count |
| `commitmentBreakdown.pending.percentage` | rate | 0 | pending commitment share — Percent not fraction. |

### `kpis`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `kpis.dpi` | money | 1.04 | **DPI** — A multiple (x), not money/percent despite kind=money. \| DPI is a MULTIPLE (x), not money — value_kind=money is wrong. Example 0.6 means 0.6x distributed-to-paid-in, NOT $0.60. Never sum, never currency-format, never aggregate across entities. |
| `kpis.dpiIncludingEquity` | money | 1.04 | DPI incl. equity — Multiple (x). |
| `kpis.expectedDpi` | money | 1.04 | expected DPI — Multiple (x). |
| `kpis.expectedDpiIncludingEquity` | money | 1.04 | expected DPI incl. equity — Multiple (x). |
| `kpis.expectedIrr` | money | 18.45 | expected IRR — Percent despite money kind. |
| `kpis.expectedIrrIncludingEquity` | money | 18.45 | expected IRR incl. equity — Percent despite money kind. |
| `kpis.expectedTvpi` | money | 1.30 | expected TVPI — Multiple (x). |
| `kpis.expectedTvpiIncludingEquity` | money | 1.30 | expected TVPI incl. equity — Multiple (x). |
| `kpis.irr` | money | 18.45 | **IRR** — value_kind tagged money but this is a PERCENT (example 18.45 = 18.45%). \| IRR is a PERCENT mis-tagged value_kind=money. Example 18.45 = 18.45% (not $18.45, not 0.1845). Never currency-format; if charting as fraction divide by 100. |
| `kpis.irrIncludingEquity` | money | 18.45 | IRR incl. equity — Percent despite money kind. |
| `kpis.tvpi` | money | 1.30 | **TVPI** — A multiple (x), not money despite kind=money. \| TVPI is a MULTIPLE (x), not money — value_kind=money is wrong. Example 1.18 means 1.18x total-value-to-paid-in. Never currency-format or sum across entities. |
| `kpis.tvpiIncludingEquity` | money | 1.30 | TVPI incl. equity — Multiple (x). |

### `mergedLoanFundingsSummary`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `mergedLoanFundingsSummary.compoundingInterestRate` | rate | None | compounding interest rate — Percent not fraction. |
| `mergedLoanFundingsSummary.distributedPrincipal` | money | 56,082,618.96 | **distributed principal** |
| `mergedLoanFundingsSummary.exchangeRateImpact.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.interest` | money | 0 | FX impact - interest |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.principal` | money | 0 | FX impact - principal |
| `mergedLoanFundingsSummary.exchangeRateImpact.total` | money | 0 | FX impact total — Only meaningful for multi-currency; 0 for USD entities. |
| `mergedLoanFundingsSummary.exchangeRateImpact.totalFees` | money | 0 |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.totalPenalties` | money | 0 |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.exchangeRateImpact.totalWithTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.expectedPaidInCapital` | money | 70,806,239.40 | expected paid-in capital |
| `mergedLoanFundingsSummary.interestRate` | rate | None | summary interest rate — Percent not fraction when populated; null on this entity. |
| `mergedLoanFundingsSummary.oidRate` | rate | None | OID rate — Percent not fraction. |
| `mergedLoanFundingsSummary.oidRemainingCost` | money | None | OID remaining cost |
| `mergedLoanFundingsSummary.outstandingPrincipalBeforeAmortization` | money | 41,078,514.06 | **outstanding principal before amortization** — Before amortization adjustments; differs from totalOutstanding.principal. \| Pre-amortization figure tagged portfolio_outstanding, but it differs from totalOutstanding.principal (the post-amortization, true current basis). Do NOT use this as the interest/current-outstanding basis and do NOT sum it with totalOutstanding.principal — they are the same loans before vs after amortization. |
| `mergedLoanFundingsSummary.overdue.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.overdue.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.overdue.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.overdue.interest` | money | -9,965,587.31 | **overdue interest** |
| `mergedLoanFundingsSummary.overdue.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.overdue.principal` | money | -29,393,863.47 | **overdue principal** |
| `mergedLoanFundingsSummary.overdue.total` | money | -40,934,595.30 | **total overdue** — Sign convention: example is negative; interpret magnitude as overdue exposure. \| Sign convention: example is NEGATIVE; overdue exposure is the magnitude (abs value). Do NOT deliver the raw negative as 'overdue amount' and do NOT sum signed values across loans without normalizing sign first. |
| `mergedLoanFundingsSummary.overdue.totalFees` | money | -2,135,703.13 | overdue fees |
| `mergedLoanFundingsSummary.overdue.totalPenalties` | money | -12,460 | overdue penalties |
| `mergedLoanFundingsSummary.overdue.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.overdue.totalWithTaxes` | money | -40,934,595.30 |  |
| `mergedLoanFundingsSummary.paidInCapital` | money | 70,806,239.40 | **paid-in capital** — Carries the same portfolio_contributed figure as the top-level contributed field. Same dollars from two paths — do NOT sum paidInCapital with contributed; they are duplicate representations of paid-in capital. |
| `mergedLoanFundingsSummary.totalDisbursed` | money | 70,948,768.30 | **total disbursed (summary)** — Same basis as top-level totalDisbursement / portfolio_disbursement. These are two views of the SAME disbursed dollars — do NOT add mergedLoanFundingsSummary.totalDisbursed to totalDisbursement; pick one source. |
| `mergedLoanFundingsSummary.totalDue.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalDue.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.totalDue.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalDue.interest` | money | -5,039,385.66 | interest due |
| `mergedLoanFundingsSummary.totalDue.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalDue.principal` | money | -12,428,641 | principal due — Sign convention as above. |
| `mergedLoanFundingsSummary.totalDue.total` | money | -17,772,546.74 | **total due** — Sign convention: negative example means a credit/not-yet-due position, not money owed. \| Sign convention: a NEGATIVE example is a credit / not-yet-due position, not money owed. Do NOT report magnitude as 'amount due'; check sign first — positive = owed, negative = credit balance. Mislabeling sign flips the meaning. |
| `mergedLoanFundingsSummary.totalDue.totalFees` | money | -292,060.08 | fees due |
| `mergedLoanFundingsSummary.totalDue.totalPenalties` | money | -12,460 | penalties due |
| `mergedLoanFundingsSummary.totalDue.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.totalDue.totalWithTaxes` | money | -17,772,546.74 |  |
| `mergedLoanFundingsSummary.totalExpected.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalExpected.compoundingInterest` | money | 0 | total expected compounding interest |
| `mergedLoanFundingsSummary.totalExpected.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalExpected.interest` | money | 20,220,913.46 | **total expected interest** |
| `mergedLoanFundingsSummary.totalExpected.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpected.principal` | money | 71,422,752.86 | **total expected principal** |
| `mergedLoanFundingsSummary.totalExpected.total` | money | 94,235,471.92 | **total expected (all components)** — Net total across components. \| Net total across components (principal + interest + compounding, net of fee/credit lines which can be negative). Do NOT treat as a simple gross sum of the component fields, and do NOT add it to component figures — it already aggregates them (non-additive memo). |
| `mergedLoanFundingsSummary.totalExpected.totalFees` | money | 2,005,115.37 | total expected fees |
| `mergedLoanFundingsSummary.totalExpected.totalPenalties` | money | 586,690.22 | total expected penalties |
| `mergedLoanFundingsSummary.totalExpected.totalTaxes` | money | 0 | total expected taxes |
| `mergedLoanFundingsSummary.totalExpected.totalWithTaxes` | money | 94,235,471.92 | total expected incl. taxes |
| `mergedLoanFundingsSummary.totalExpectedDisbursements` | money | 70,948,768.30 | total expected disbursements |
| `mergedLoanFundingsSummary.totalExpectedToDate.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.interest` | money | 20,220,913.46 | expected-to-date interest |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.principal` | money | 71,422,752.86 | expected-to-date principal |
| `mergedLoanFundingsSummary.totalExpectedToDate.total` | money | 94,235,471.92 | total expected to date — As-of-today slice of expected; equals lifetime expected here. |
| `mergedLoanFundingsSummary.totalExpectedToDate.totalFees` | money | 2,005,115.37 | expected-to-date fees |
| `mergedLoanFundingsSummary.totalExpectedToDate.totalPenalties` | money | 586,690.22 | expected-to-date penalties |
| `mergedLoanFundingsSummary.totalExpectedToDate.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.totalExpectedToDate.totalWithTaxes` | money | 94,235,471.92 |  |
| `mergedLoanFundingsSummary.totalOID.amount` | money | 0 | total OID amount |
| `mergedLoanFundingsSummary.totalOID.interest` | money | 0 | OID interest |
| `mergedLoanFundingsSummary.totalOutstanding.capitalizedBalance` | money | 14,392,605.00 | capitalized balance — NON-additive memo; do not add to principal/interest (tracks capitalized component). |
| `mergedLoanFundingsSummary.totalOutstanding.compoundingInterest` | money | 0 | outstanding compounding interest |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.outstanding` | money | (empty_list) | outstanding fee line - outstanding — Deep per-fee permutation; empty on this entity. |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.totalDue` | money | (empty_list) | outstanding fee line - total due — Deep per-fee permutation; empty on this entity. |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].fee.value` | money | (empty_list) | outstanding fee line - value/rate — Could be a percent or money depending on calculationType; deep niche, empty here. |
| `mergedLoanFundingsSummary.totalOutstanding.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalOutstanding.interest` | money | 4,337,396.40 | **outstanding interest** |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalOutstanding.principal` | money | 15,197,605.00 | **outstanding principal** — Use this (not .total) as the interest basis; .total is net of fee/credit lines. |
| `mergedLoanFundingsSummary.totalOutstanding.total` | money | 18,740,039.44 | **total outstanding** — NET of fee/credit components (totalFees here is negative); use .principal for an interest basis. \| NET of fee/credit components (totalFees here is negative), so it is LOWER than gross principal owed. Wrong basis for interest accrual or 'amount outstanding' headline — use .principal for the principal basis; only use .total for a net-of-credits balance. |
| `mergedLoanFundingsSummary.totalOutstanding.totalCompoundingInterest` | money | 0 | outstanding total compounding interest |
| `mergedLoanFundingsSummary.totalOutstanding.totalFees` | money | -1,369,192.18 | outstanding fees — Can be negative (credit); example -1.37M. Folds into totalOutstanding.total. |
| `mergedLoanFundingsSummary.totalOutstanding.totalPenalties` | money | 574,230.22 | outstanding penalties |
| `mergedLoanFundingsSummary.totalOutstanding.totalTaxes` | money | 0 | outstanding taxes |
| `mergedLoanFundingsSummary.totalOutstanding.totalWithTaxes` | money | 18,740,039.44 | total outstanding incl. taxes |
| `mergedLoanFundingsSummary.totalPaid.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalPaid.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalPaid.interest` | money | 15,858,311.87 | **interest paid** |
| `mergedLoanFundingsSummary.totalPaid.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalPaid.principal` | money | 56,225,147.86 | **principal paid** |
| `mergedLoanFundingsSummary.totalPaid.total` | money | 73,519,721.54 | **total paid** |
| `mergedLoanFundingsSummary.totalPaid.totalFees` | money | 1,423,801.81 | fees paid |
| `mergedLoanFundingsSummary.totalPaid.totalPenalties` | money | 12,460 | penalties paid |
| `mergedLoanFundingsSummary.totalPaid.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.totalPaid.totalWithTaxes` | money | 73,519,721.54 |  |
| `mergedLoanFundingsSummary.totalWaived.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalWaived.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalWaived.interest` | money | 14,092.33 | interest waived |
| `mergedLoanFundingsSummary.totalWaived.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWaived.principal` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWaived.total` | money | 102,967.33 | total waived |
| `mergedLoanFundingsSummary.totalWaived.totalFees` | money | 875 | fees waived |
| `mergedLoanFundingsSummary.totalWaived.totalPenalties` | money | 88,000 | penalties waived |
| `mergedLoanFundingsSummary.totalWaived.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWaived.totalWithTaxes` | money | 102,967.33 |  |
| `mergedLoanFundingsSummary.totalWrittenOff.accruedCompoundingInterest` | money | None |  |
| `mergedLoanFundingsSummary.totalWrittenOff.compoundingInterest` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.fees[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.indexedPrincipal` | money | None |  |
| `mergedLoanFundingsSummary.totalWrittenOff.interest` | money | 0 | interest written off |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].amount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].compoundingAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.dueDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.minAmount` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.outstanding` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.timing` | enum | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.totalDue` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].fee.value` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.penalties[].periodCharge` | money | (empty_list) |  |
| `mergedLoanFundingsSummary.totalWrittenOff.principal` | money | 0 | principal written off |
| `mergedLoanFundingsSummary.totalWrittenOff.total` | money | 0 | **total written off** |
| `mergedLoanFundingsSummary.totalWrittenOff.totalFees` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWrittenOff.totalPenalties` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWrittenOff.totalTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.totalWrittenOff.totalWithTaxes` | money | 0 |  |
| `mergedLoanFundingsSummary.unutilizedPrincipal` | money | 384,723.17 | **unutilized principal** |

### `receivables`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `receivables.accruedCompoundingInterest` | money | None |  |
| `receivables.compoundingInterest` | money | 0 | receivable compounding interest |
| `receivables.fees[].amount` | money | (empty_list) |  |
| `receivables.fees[].compoundingAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.calculationType` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.chargeTiming` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.depositConditions` | enum | (empty_list) |  |
| `receivables.fees[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `receivables.fees[].fee.depositPaysFor` | enum | (empty_list) |  |
| `receivables.fees[].fee.dueDate` | date | (empty_list) |  |
| `receivables.fees[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.minAmount` | money | (empty_list) |  |
| `receivables.fees[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `receivables.fees[].fee.outstanding` | money | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.ratePer` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `receivables.fees[].fee.repaymentTiming` | enum | (empty_list) |  |
| `receivables.fees[].fee.secondaryValue` | money | (empty_list) |  |
| `receivables.fees[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `receivables.fees[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.fees[].fee.timing` | enum | (empty_list) |  |
| `receivables.fees[].fee.totalDue` | money | (empty_list) |  |
| `receivables.fees[].fee.value` | money | (empty_list) |  |
| `receivables.fees[].periodCharge` | money | (empty_list) |  |
| `receivables.indexedPrincipal` | money | None |  |
| `receivables.interest` | money | 10,879,600.83 | **receivable interest** |
| `receivables.penalties[].amount` | money | (empty_list) |  |
| `receivables.penalties[].compoundingAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.accrualFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.calculationType` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargeFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.chargePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.chargeTiming` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFeeCapitalizationComponent` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.compoundingFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.depositConditions` | enum | (empty_list) |  |
| `receivables.penalties[].fee.depositNumberOfRepayments` | count | (empty_list) |  |
| `receivables.penalties[].fee.depositPaysFor` | enum | (empty_list) |  |
| `receivables.penalties[].fee.dueDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.duesCalculationMethod` | enum | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.feePeriod.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.fixedRepaymentAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.minAmount` | money | (empty_list) |  |
| `receivables.penalties[].fee.oidRecognitionStartDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.outstanding` | money | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.penaltyGrace.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.ratePer` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.daysOffset` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.endDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.every` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.everyMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.on` | enum | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.repetitions` | count | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.specificDates[]` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentFrequency.startDate` | date | (empty_list) |  |
| `receivables.penalties[].fee.repaymentTiming` | enum | (empty_list) |  |
| `receivables.penalties[].fee.secondaryValue` | money | (empty_list) |  |
| `receivables.penalties[].fee.timeIntervalToEffectiveValue.timeInterval` | enum | (empty_list) |  |
| `receivables.penalties[].fee.timeIntervalToEffectiveValue.timeIntervalMultiplier` | count | (empty_list) |  |
| `receivables.penalties[].fee.timing` | enum | (empty_list) |  |
| `receivables.penalties[].fee.totalDue` | money | (empty_list) |  |
| `receivables.penalties[].fee.value` | money | (empty_list) |  |
| `receivables.penalties[].periodCharge` | money | (empty_list) |  |
| `receivables.principal` | money | 14,167,189.09 | **receivable principal** |
| `receivables.total` | money | 27,074,483.25 | **receivables total** — Net total across components. \| Net total across components (net of fee/credit lines that may be negative). Non-additive with its own .principal/.interest children — summing total + components double-counts. Use .principal alone for a principal basis. |
| `receivables.totalFees` | money | 1,441,003.11 | receivable fees |
| `receivables.totalPenalties` | money | 586,690.22 | receivable penalties |
| `receivables.totalTaxes` | money | 0 | receivable taxes |
| `receivables.totalWithTaxes` | money | 27,074,483.25 | receivables incl. taxes |

## Borrower (ClientExtended)

- Root: `ClientExtended` · DEGRADED — clients resolver HTTP 500 (2026-06-26); schema-mapped, probe deferred
- 33 askable value fields shown (66 bool/text fields in YAML only)

### `_direct`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `createdAt` | date | (fetch_error) | borrower onboarding date |
| `currentCommitment` | money | (fetch_error) | **borrower total commitment** — Sum of commitment across this borrower's loans; borrower-level roll-up, not a single-loan commitment. |
| `fileEntriesCount` | count | (fetch_error) | borrower document count |
| `lastPayment` | date | (fetch_error) | borrower last payment date — Date, not amount. |
| `nextPayment` | date | (fetch_error) | **borrower next payment date** — Date, not amount. |
| `numOfActiveLoans` | count | (fetch_error) | **borrower active loan count** — Borrower-level count across all of this client's loans, not portfolio-wide; do not confuse with portfolio_active_loans. |
| `numOfPendingLoans` | count | (fetch_error) | **borrower pending loan count** — Pending (not yet funded) loans for this borrower only. |
| `outstandingBalance` | money | (fetch_error) | **borrower outstanding balance** — Borrower-level aggregate across loans; may be NET of fee/credit components like loan-level totalOutstanding.total — confirm vs loan principalOutstanding for an interest basis. \| Borrower-level outstandingBalance is an aggregate that, like loan-level totalOutstanding.total, may be NET of fee/credit components. It is the WRONG basis for interest accrual or principal-exposure questions. For an interest/principal basis, sum the loan-level principalOutstanding across this borrower's loans rather than using this net roll-up; reconcile the two before delivering an exposure figure. |
| `sharesValue` | money | (fetch_error) | borrower shares value — Equity holding value, not part of debt outstanding. |
| `totalOverdue` | money | (fetch_error) | **borrower total overdue** — Borrower-level overdue across all loans, not a single loan. |
| `type` | enum | (fetch_error) | borrower type |
| `warrantsValue` | money | (fetch_error) | borrower warrants value — Equity-kicker memo value, not part of debt outstanding. |

### `dataApplications`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `dataApplications.pageItems[].createdAt` | date | (fetch_error) | application created date |
| `dataApplications.pageItems[].createdFromGeneralApplication.createdAt` | date | (fetch_error) |  |
| `dataApplications.pageItems[].expiredAfterDays` | count | (fetch_error) |  |
| `dataApplications.pageItems[].progress.completedInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].progress.completedRequiredInputs` | count | (fetch_error) | application required-fields completed — Niche progress metric. |
| `dataApplications.pageItems[].progress.totalInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].progress.totalRequiredInputs` | count | (fetch_error) | application required-fields total — Niche progress metric. |
| `dataApplications.pageItems[].relatedEmails[].attachments[].size` | count | (fetch_error) |  |
| `dataApplications.pageItems[].responseData[].type` | enum | (fetch_error) |  |
| `dataApplications.pageItems[].reviewedAt` | date | (fetch_error) | application reviewed date |
| `dataApplications.pageItems[].secondsToCompletion` | count | (fetch_error) | application completion time — Duration in seconds, not a money value. |
| `dataApplications.pageItems[].sections[].position` | count | (fetch_error) |  |
| `dataApplications.pageItems[].sections[].progress.completedInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].sections[].progress.completedRequiredInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].sections[].progress.totalInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].sections[].progress.totalRequiredInputs` | count | (fetch_error) |  |
| `dataApplications.pageItems[].status` | enum | (fetch_error) | application status — DataApplicationStatus enum, application workflow only — not loan status. |
| `dataApplications.pageItems[].submittedAt` | date | (fetch_error) | application submitted date |
| `dataApplications.totalFilteredRecords` | count | (fetch_error) | borrower application count — Counts intake/data applications, not loans. |

### `equities`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `equities.totalFilteredRecords` | count | (fetch_error) | borrower equity-position count |

### `loans`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `loans.totalFilteredRecords` | count | (fetch_error) | **borrower loan count** — Count of all loans (any status) for this borrower. |

## Equity

- Root: `Equity` · FORBIDDEN — equities resolver HTTP 403 (out of read-scope); schema-mapped only
- 170 askable value fields shown (82 bool/text fields in YAML only)

### `_direct`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `acquisitionDate` | date | (fetch_error) | **acquisition date** |
| `createdAt` | date | (fetch_error) | equity created date |
| `currency` | enum | (fetch_error) | equity currency |
| `exercisePricePerUnit` | money | (fetch_error) | **exercise price per unit** |
| `expectedExerciseDate` | date | (fetch_error) | expected exercise date |
| `expirationDate` | date | (fetch_error) | **expiration date** |
| `fileEntriesCount` | count | (fetch_error) | document count |
| `status` | enum | (fetch_error) | **equity status** |
| `type` | enum | (fetch_error) | **equity type** |

### `allocations[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `allocations[].currency` | enum | (fetch_error) |  |
| `allocations[].date` | date | (fetch_error) | allocation date |
| `allocations[].fmv` | money | (fetch_error) | **allocation fair market value** |
| `allocations[].numberOfUnits` | money | (fetch_error) | **allocated units** — value_kind is money but this is a unit/share count, not a dollar amount \| value_kind=money but this is a unit/SHARE COUNT, not dollars. Never format as currency or sum into a money total. |
| `allocations[].pricePerUnit` | money | (fetch_error) | **allocation price per unit** |

### `equityKPIs`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `equityKPIs.bvToCost` | money | (fetch_error) | **book value to cost** — a multiple, not money despite value_kind money \| Book-value-to-cost is a MULTIPLE (ratio), not money despite value_kind=money. Do not currency-format or sum. |
| `equityKPIs.tvpi` | money | (fetch_error) | **TVPI** — a multiple (e.g. 1.8x), not money despite value_kind money; not a percent \| TVPI is a MULTIPLE (e.g. 1.8x), not money despite value_kind=money and not a percent. Do not currency-format, do not multiply by 100, do not sum. |

### `exerciseEntries[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `exerciseEntries[].date` | date | (fetch_error) | exercise date |
| `exerciseEntries[].numberOfExercisedUnits` | money | (fetch_error) | **exercised units** — value_kind money but this is a unit/share count \| value_kind=money but this is a unit/SHARE COUNT, not dollars. Do not treat as currency or roll into money aggregates. |

### `expectedTransactions[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `expectedTransactions[].currency` | enum | (fetch_error) |  |
| `expectedTransactions[].date` | date | (fetch_error) | expected transaction date |
| `expectedTransactions[].loanTransaction.cancellationDate` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.capitalizationComponent` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.currency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.date` | date | (fetch_error) | linked-loan transaction date |
| `expectedTransactions[].loanTransaction.distribution.accruedCompoundingInterest` | money | (fetch_error) | linked-loan accrued compounding interest |
| `expectedTransactions[].loanTransaction.distribution.compoundingInterest` | money | (fetch_error) | linked-loan compounding interest |
| `expectedTransactions[].loanTransaction.distribution.fees[].amount` | money | (fetch_error) | linked-loan fee amount |
| `expectedTransactions[].loanTransaction.distribution.fees[].compoundingAmount` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.distribution.fees[].periodCharge` | money | (fetch_error) | linked-loan fee period charge |
| `expectedTransactions[].loanTransaction.distribution.indexedPrincipal` | money | (fetch_error) | linked-loan indexed principal |
| `expectedTransactions[].loanTransaction.distribution.interest` | money | (fetch_error) | linked-loan distribution interest |
| `expectedTransactions[].loanTransaction.distribution.penalties[].amount` | money | (fetch_error) | linked-loan penalty amount |
| `expectedTransactions[].loanTransaction.distribution.penalties[].compoundingAmount` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.distribution.penalties[].periodCharge` | money | (fetch_error) | linked-loan penalty period charge |
| `expectedTransactions[].loanTransaction.distribution.principal` | money | (fetch_error) | linked-loan distribution principal |
| `expectedTransactions[].loanTransaction.distribution.total` | money | (fetch_error) | linked-loan distribution total — NET of fee/credit components; use .principal for an interest basis |
| `expectedTransactions[].loanTransaction.distribution.totalFees` | money | (fetch_error) | linked-loan total fees |
| `expectedTransactions[].loanTransaction.distribution.totalPenalties` | money | (fetch_error) | linked-loan total penalties |
| `expectedTransactions[].loanTransaction.distribution.totalTaxes` | money | (fetch_error) | linked-loan total taxes |
| `expectedTransactions[].loanTransaction.distribution.totalWithTaxes` | money | (fetch_error) | linked-loan distribution incl. taxes |
| `expectedTransactions[].loanTransaction.duesCalculationMethod` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.effectiveDate` | date | (fetch_error) | linked-loan effective date |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.amount` | money | (fetch_error) | linked debt-sale amount |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.currency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.date` | date | (fetch_error) | linked debt-sale date |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.effectiveDate` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.sellComponents[].buyerPostSell` | money | (fetch_error) | debt-sale buyer post-sell |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.sellComponents[].name` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.sellComponents[].sellerPostSell` | money | (fetch_error) | debt-sale seller post-sell |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.sellComponents[].sellerPreSell` | money | (fetch_error) | debt-sale seller pre-sell |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.sellPercentage` | rate | (fetch_error) | linked debt-sale percentage — a percentage share sold |
| `expectedTransactions[].loanTransaction.loanFundingDebtSell.status` | enum | (fetch_error) | linked debt-sale status |
| `expectedTransactions[].loanTransaction.oidOverride.amount` | money | (fetch_error) | OID override amount (alt) |
| `expectedTransactions[].loanTransaction.oidOverride.breakdown[].amortized` | money | (fetch_error) | OID amortized |
| `expectedTransactions[].loanTransaction.oidOverride.breakdown[].amount` | money | (fetch_error) | OID breakdown amount |
| `expectedTransactions[].loanTransaction.oidOverride.breakdown[].unamortized` | money | (fetch_error) | OID unamortized |
| `expectedTransactions[].loanTransaction.oidOverride.indexedRemainingCost` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.oidOverride.rate` | rate | (fetch_error) | OID override rate (alt) — PERCENT not fraction \| Alt OID override rate is a PERCENT, not a fraction (e.g. 14 means 14%). Mirror handling of override.oid.rate; pick one canonical path to avoid double-counting two override fields for the same loan. |
| `expectedTransactions[].loanTransaction.oidOverride.remainingCost` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.oidOverride.totalWithInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.outstandingLoanBalance` | money | (fetch_error) | linked-loan outstanding balance — snapshot tied to this linked-loan txn, not the equity itself |
| `expectedTransactions[].loanTransaction.override.compoundingChargedOnPeriodOverride` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.accruedCompoundingInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.compoundingInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.indexedPrincipal` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.interest` | money | (fetch_error) | override interest due |
| `expectedTransactions[].loanTransaction.override.due.principal` | money | (fetch_error) | override principal due |
| `expectedTransactions[].loanTransaction.override.due.total` | money | (fetch_error) | override amount due total — NET total; use components for breakdown |
| `expectedTransactions[].loanTransaction.override.due.totalFees` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.totalPenalties` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.totalTaxes` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.due.totalWithTaxes` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.interestChargedOnPeriodOverride` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.oid.amount` | money | (fetch_error) | OID override amount |
| `expectedTransactions[].loanTransaction.override.oid.indexedRemainingCost` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.oid.rate` | rate | (fetch_error) | OID override rate — PERCENT not fraction (e.g. 14 means 14%) \| OID override rate is a PERCENT, not a fraction (e.g. 14 means 14%, not 0.14). Do not divide by 100 a second time or treat as a 0..1 fraction in interest math. |
| `expectedTransactions[].loanTransaction.override.oid.remainingCost` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.oid.totalWithInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.accruedCompoundingInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.compoundingInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.indexedPrincipal` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.interest` | money | (fetch_error) | override outstanding interest |
| `expectedTransactions[].loanTransaction.override.outstanding.principal` | money | (fetch_error) | override outstanding principal |
| `expectedTransactions[].loanTransaction.override.outstanding.total` | money | (fetch_error) | override outstanding total — NET of fee/credit components; use .principal for interest basis |
| `expectedTransactions[].loanTransaction.override.outstanding.totalFees` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.totalPenalties` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.totalTaxes` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.outstanding.totalWithTaxes` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.override.realizedPrincipal` | money | (fetch_error) | override realized principal |
| `expectedTransactions[].loanTransaction.rateToBaseCurrency` | rate | (fetch_error) | linked-loan FX rate — FX rate, not an interest rate \| FX conversion rate on the linked loan transaction, not an interest rate or money. Do not misread as a yield. |
| `expectedTransactions[].loanTransaction.transactionInput.baseNominalPrincipal` | money | (fetch_error) | input base nominal principal |
| `expectedTransactions[].loanTransaction.transactionInput.capitalizationComponent` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.currency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.date` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.deductedPrincipal` | money | (fetch_error) | input deducted principal |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.compoundingInterest` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.indexedPrincipal` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.interest` | money | (fetch_error) | input distribution interest |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.principal` | money | (fetch_error) | input distribution principal |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.totalFees` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.totalPenalties` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.distribution.totalTaxes` | money | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.duesCalculationMethod` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.effectiveDate` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.rateToBaseCurrency` | rate | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.currency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.date` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.equityCurrency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.equityType` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.numberOfUnits` | money | (fetch_error) | linked equity-txn units — value_kind money but this is a unit/share count |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.pricePerUnit` | money | (fetch_error) | linked equity-txn price per unit |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.rateToBaseCurrency` | rate | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedEquityTransaction.type` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.cancellationDate` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.currency` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.date` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.effectiveDate` | date | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.rateToBaseCurrency` | rate | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.relatedFundingEntityTransaction.type` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.transactionInput.totalDistribution` | money | (fetch_error) | input total distribution |
| `expectedTransactions[].loanTransaction.transactionInput.type` | enum | (fetch_error) |  |
| `expectedTransactions[].loanTransaction.type` | enum | (fetch_error) | linked-loan transaction type |
| `expectedTransactions[].numberOfUnits` | money | (fetch_error) | expected units — value_kind money but this is a unit/share count |
| `expectedTransactions[].pricePerUnit` | money | (fetch_error) | expected price per unit |
| `expectedTransactions[].rateToBaseCurrency` | rate | (fetch_error) | FX rate to base currency — an FX conversion rate, not an interest rate \| This is an FX CONVERSION RATE, not an interest rate and not money. Do not treat as a yield/percent; it is the multiplier used to convert the transaction currency to base currency. |
| `expectedTransactions[].total` | money | (fetch_error) | expected transaction total |
| `expectedTransactions[].type` | enum | (fetch_error) | expected transaction type |

### `fundingSources[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `fundingSources[].cancellationDate` | date | (fetch_error) |  |
| `fundingSources[].commitment` | money | (fetch_error) | **funding-source commitment** |
| `fundingSources[].commitmentInOriginalCurrency` | money | (fetch_error) | commitment in original currency — pre-FX-conversion amount; pair with originalCurrency |
| `fundingSources[].commitmentPercentage` | rate | (fetch_error) | **funding-source commitment percentage** — a percentage share of total commitment \| Percentage share of total commitment (funding_participation). Confirm percent (e.g. 25 = 25%) vs fraction (0.25) before deriving a dollar amount; do not sum across sources unless reconciling to 100%. |
| `fundingSources[].currency` | enum | (fetch_error) |  |
| `fundingSources[].date` | date | (fetch_error) | funding-source date |
| `fundingSources[].distributionTransactions[].amount` | money | (fetch_error) | **distribution amount** |
| `fundingSources[].distributionTransactions[].cancellationDate` | date | (fetch_error) |  |
| `fundingSources[].distributionTransactions[].currency` | enum | (fetch_error) |  |
| `fundingSources[].distributionTransactions[].date` | date | (fetch_error) | distribution date |
| `fundingSources[].investmentTransactions[].amount` | money | (fetch_error) | **investment contribution amount** |
| `fundingSources[].investmentTransactions[].cancellationDate` | date | (fetch_error) |  |
| `fundingSources[].investmentTransactions[].currency` | enum | (fetch_error) |  |
| `fundingSources[].investmentTransactions[].date` | date | (fetch_error) | investment date |
| `fundingSources[].investor.balance` | money | (fetch_error) | **investor balance** |
| `fundingSources[].investor.cashAvailabilityChart[].balance` | money | (fetch_error) | investor cash availability balance — time-series point; expected flag marks forecast vs actual |
| `fundingSources[].investor.cashAvailabilityChart[].date` | date | (fetch_error) | investor cash availability date |
| `fundingSources[].investor.closeDate` | date | (fetch_error) |  |
| `fundingSources[].investor.creationDate` | date | (fetch_error) |  |
| `fundingSources[].investor.currency` | enum | (fetch_error) | investor currency |
| `fundingSources[].investor.kpis.dpi` | money | (fetch_error) | **investor DPI** — a multiple, not money despite value_kind money \| DPI is a MULTIPLE (distributions/paid-in), not money despite value_kind=money. Do not currency-format or sum across investors. |
| `fundingSources[].investor.kpis.irr` | money | (fetch_error) | **investor IRR** — likely a percent/rate despite value_kind money; an example >1 means percent \| IRR is a PERCENT/rate, not money despite value_kind money. Confirm whether the raw value is already in percent (e.g. 18 = 18%) or a fraction (0.18). An example >1 means it is delivered as a percent and must NOT be multiplied by 100 again, nor summed as a dollar amount. |
| `fundingSources[].investor.totalCommitmentByEntity` | money | (fetch_error) | commitment by entity — directional opposite |
| `fundingSources[].investor.totalCommitmentToEntity` | money | (fetch_error) | **investor commitment to entity** — directional: investor's commitment into this entity \| Directional figure: investor's commitment INTO this entity. Do not conflate with funding-source-level commitment or with amounts the entity owes out; ensure direction (investor->entity) matches the question before summing. |
| `fundingSources[].investor.totalDistributedByEntity` | money | (fetch_error) | **distributed by entity to investor** — directional: amount the entity paid to this investor \| Directional: amount the ENTITY PAID OUT to this investor. Do not confuse with distributions received from a target; verify direction before netting against contributions. |
| `fundingSources[].investor.totalDistributedToEntity` | money | (fetch_error) | distributed to entity by investor — directional opposite of totalDistributedByEntity |
| `fundingSources[].investor.totalInvestedByEntity` | money | (fetch_error) | invested by entity — directional opposite |
| `fundingSources[].investor.totalInvestedInEntity` | money | (fetch_error) | **invested in entity** — directional: invested into this entity \| Directional: amount invested INTO this entity (portfolio_contributed). Distinct from commitment (may be unfunded) and from totalInvestedInTarget at the funding-source level; do not double-count both the investor-level and funding-source-level invested figures. |
| `fundingSources[].originalCurrency` | enum | (fetch_error) |  |
| `fundingSources[].totalDistributedToInvestor` | money | (fetch_error) | **total distributed to investor** |
| `fundingSources[].totalInvestedInTarget` | money | (fetch_error) | **total invested in target** |

### `summary`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `summary.cost` | money | (fetch_error) | **cost basis** |
| `summary.currentHoldingsValue` | money | (fetch_error) | **current holdings value** |
| `summary.numberOfUnallocatedUnits` | money | (fetch_error) | unallocated units — value_kind money but this is a unit/share count |
| `summary.numberOfUnitsHeld` | money | (fetch_error) | **units held** — value_kind money but this is a unit/share count \| value_kind=money but this is a unit/SHARE COUNT, not dollars. Multiply by valuations[].pricePerUnit to get value; do not currency-format directly. |
| `summary.shareholding` | money | (fetch_error) | **shareholding percentage** — a percentage stake despite value_kind money \| value_kind=money but this is a PERCENTAGE ownership stake. Confirm percent vs fraction encoding; never deliver as a dollar figure or sum across positions. |
| `summary.totalExercisePrice` | money | (fetch_error) | total exercise price |
| `summary.totalExercisedUnits` | money | (fetch_error) | total exercised units — value_kind money but this is a unit/share count |
| `summary.unrealizedGains` | money | (fetch_error) | **unrealized gains** |

### `valuations[]`

| Field | Kind | Example | Name / notes |
|---|---|---|---|
| `valuations[].currency` | enum | (fetch_error) |  |
| `valuations[].date` | date | (fetch_error) | **valuation date** |
| `valuations[].pricePerUnit` | money | (fetch_error) | **valuation price per unit** |
| `valuations[].totalIssuedUnits` | money | (fetch_error) | total issued units — value_kind money but this is a unit/share count; use to compute fully-diluted value |

