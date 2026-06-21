# Hypercore GraphQL — Read-Relevant Schema Digest

queryType=`Query`  mutationType=`Mutation`  total_types=599  query_fields=84

> READ-ONLY: this skill uses ONLY Query fields below. NEVER any Mutation.


## All Query field names (84)

`actualCurrencyRates`, `aiQuery`, `allocation`, `audits`, `broker`, `brokers`, `calculateLoanApplicationGrossAmount`, `calculatedAvailableDisbursementAmount`, `changeRequest`, `changeRequests`, `client`, `clientCustomDocuments`, `clients`, `clientsOverview`, `clientsTrend`, `dataApplication`, `dataApplicationByUrlKey`, `dataApplicationTemplate`, `dataApplicationTemplates`, `dataApplications`, `deal`, `deals`, `dynamicTable`, `dynamicTableRows`, `dynamicTables`, `dynamicTablesGroups`, `entityChangeRequest`, `equities`, `equity`, `fileEntries`, `floatingRate`, `floatingRates`, `fundingEntities`, `fundingEntity`, `fundingSourceTemplate`, `fundingSourceTemplates`, `genericDataApplication`, `genericDataApplications`, `getDraftSchedulePreview`, `getDraftSchedulePreviewDueRows`, `getFileEntryContent`, `getInterestRates`, `getLoanApplicationPreview`, `getLoanRepaymentDistribution`, `getLoanRepaymentDistributionFromNominalPrincipal`, `getLoanReschedulePreview`, `getLoanScheduleDueRows`, `getLoanScheduleGenerationInput`, `getLoanSchedulePreviewDueRows`, `getLoanTermsPreview`, `getLoanTransactionFundingSourcesDistribution`, `getLoanTransactionPreview`, `getMetabaseDashboardUrl`, `globalSettings`, `importInfo`, `importInfos`, `investment`, `investmentEntities`, `investmentEntity`, `investmentEntityTransactions`, `loan`, `loanFunding`, `loanFundingDebtSell`, `loanFundings`, `loanTemplates`, `loanTransaction`, `loans`, `me`, `outstanding`, `portfolioOverview`, `portfolioPerformanceMetabase`, `reportDashboards`, `search`, `statementTemplates`, `tenantCurrencies`, `userNotifications`, `users`, `verifyImportTransactions`, `views`, `workflowBoard`, `workflowBoards`, `workflowCard`, `workflowCards`, `workflowStages`


### query `loan(id: ID!)` -> `Loan`

### query `loans(filter: LoansFilterInput, skip: Int, limit: Int, sortBy: LoansSortByInput)` -> `PaginatedLoans`

### query `loanTransaction(id: ID!)` -> `LoanTransaction`

### query `loanTransactions` — (not present)


### query `loanFunding(id: ID!)` -> `LoanFunding`

### query `loanFundings(filter: LoanFundingsFilterInput, skip: Int, limit: Int)` -> `PaginatedLoanFundings`

### query `client(id: ID!)` -> `Client!`

### query `clients(skip: Int, limit: Int, filter: ClientsFilterInput, sortBy: ClientsSortByInput)` -> `PaginatedClients`

### query `clientsOverview()` -> `PieValues`

### query `clientsTrend(period: AggregationPeriod!)` -> `[ClientGraphValue!]!`

### query `equity(id: ID!)` -> `Equity`

### query `equities(filter: EquitiesFilterInput, skip: Int, limit: Int)` -> `PaginatedEquity`

### query `fundingEntity(id: ID!)` -> `FundingEntity`

### query `fundingEntities(filter: FundingEntitiesFilterInput, skip: Int, limit: Int, sortBy: FundingEntitiesSortByInput)` -> `PaginatedFundingEntities`

### query `statementTemplates(type: DocTemplateType)` -> `[DocumentTemplate!]`

### query `userNotifications(filter: NotificationsFilterInput!, skip: Int, limit: Int)` -> `PaginatedUserNotifications!`

### query `clientCustomDocuments()` -> `[CustomDocumentTemplate]`


## Returned object types (fields)


### `Loan`
- `id`: `ID!`
- `refId`: `ID`
- `name`: `String`
- `group`: `String`
- `description`: `String`
- `terms`: `[LoanTerms!]`
- `draftTerms`: `[LoanTerms!]`
- `owner`: `User`
- `owners`: `[User!]`
- `client`: `Client`
- `broker`: `Broker`
- `disbursements`: `[Disbursement]`
- `status`: `LoanStatusEnum!`
- `commitment`: `Float`
- `currency`: `Currency`
- `lifeCycle`: `LoanLifeCycle`
- `defaultEvents`: `[DefaultEvent!]`
- `startDate`: `Date`
- `endDate`: `Date`
- `scheduleExpectedEndDate`: `Date`
- `scheduleEndDate`: `Date`
- `approvalDate`: `Date`
- `contractClosingDate`: `Date`
- `closingDate`: `Date`
- `loanTypeName`: `String`
- `loanTemplateId`: `ID`
- `loanPurpose`: `String`
- `annualInterestRate`: `Float`
- `annualCompoundingInterestRate`: `Float`
- `interestRatesData`: `[InterestRateData!]`
- `compoundingInterestRatesData`: `[InterestRateData!]`
- `principalIndexRatesData`: `[InterestRateData!]`
- `exchangeRateRatesData`: `[InterestRateData!]`
- `baseCurrencyExchangeRate`: `[InterestRateData!]`
- `baseCurrency`: `Currency`
- `isLoanWithBaseCurrency`: `Boolean`
- `audit`: `LoanAudit`
- `repaymentSchedule`: `LoanSchedule`
- `summary`: `LoanSummary`
- `expectedSchedule`: `LoanSchedule`
- `originalExpectedSchedule`: `LoanSchedule`
- `transactions`: `[LoanTransaction!]`
- `lastTransaction`: `LoanTransaction`
- `scheduleRowByDate`: `LoanScheduleRow`
- `fees`: `[LoanFee!]`
- `oldFundingSources`: `[Investment!]`
- `fundingSources`: `[LoanFunding!]`
- `fundingSourcesAllocationDrafts`: `[FundingSourcesAllocationDraft!]`
- `fileEntriesCount`: `Int`
- `taxRules`: `[TaxRules!]`
- `oidTerms`: `OIDTerms`
- `oidRestructureEvents`: `[OIDRestructureEvent!]`
- `agingAnalysis`: `AgingAnalysis`
- `agingAnalysisHistory`: `AgingAnalysisHistory`
- `duesCalculationMethod`: `DuesCalculationMethod`
- `submittedOnDate`: `Date`
- `interestUpdates`: `[InterestUpdate!]`
- `compoundingInterestUpdates`: `[InterestUpdate!]`
- `principalIndexUpdates`: `[InterestUpdate!]`
- `exchangeRateUpdates`: `[InterestUpdate!]`
- `repaymentStrategy`: `[InstallmentComponentType!]`
- `notes`: `[Note!]`
- `multiLoan`: `Boolean`
- `isSubLoan`: `Boolean`
- `subLoans`: `[Loan!]`
- `parentLoan`: `Loan`
- `parentGroup`: `Loan`
- `groupSubLoans`: `[Loan!]`
- `groupLoan`: `Boolean`
- `importInfo`: `ImportInfo`
- `importValidation`: `ImportValidation`
- `workflowCards`: `[WorkflowCard]`
- `isRevolving`: `Boolean`
- `dailyRecalculateSchedule`: `Boolean`
- `expRepaymentsAffectOutstandingAfterLastTransaction`: `Boolean`
- `applyEarlyRedemptionFeesBeforeNegativeOutstanding`: `Boolean`
- `equities`: `[Equity!]`
- `equityAllocations`: `[LoanEquityAllocation!]`
- `valuations`: `[LoanValuation!]`
- `rejectReason`: `String`
- `statusNote`: `String`
- `fundingSourcesAsyncUpdate`: `AsyncUpdate`
- `groupLoanAsyncUpdate`: `AsyncUpdate`
- `dynamicTables`: `[DynamicTable!]`
- `showExpectedDisbursements`: `Boolean`
- `deductRepaymentOnDisbursementDate`: `Boolean`
- `skipOverdueCalculation`: `Boolean`
- `useExpectedLoanScheduleForFundingSources`: `Boolean`
- `changeRequest`: `ChangeRequest`
- `isTest`: `Boolean`
- `fundingSourcesReconciliationAccount`: `FundingSourcesReconciliationAccount`
- `rateDeterminationStartsBeforeLoanStartDate`: `Boolean`
- `addOutstandingCompoundingToUtilizedPrincipal`: `Boolean`
- `disableFsAllocationOfFutureRepaymentsPaidFromDeposit`: `Boolean`
- `treatOverdueCompoundingInterestAsPrincipal`: `Boolean`
- `useLastDayOfMonthForShortMonthsInFrequency`: `Boolean`
- `deal`: `Deal`

### `PaginatedLoans`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[Loan!]!`

### `LoanTransaction`
- `id`: `ID!`
- `canceled`: `Boolean`
- `cancellationDate`: `Date`
- `distribution`: `InstallmentComponents`
- `outstandingLoanBalance`: `Float`
- `date`: `Date!`
- `effectiveDate`: `Date`
- `type`: `TransactionType`
- `note`: `String`
- `accountNumber`: `String`
- `bankNumber`: `String`
- `checkNumber`: `String`
- `receiptNumber`: `String`
- `routingCode`: `String`
- `currency`: `Currency`
- `loan`: `Loan`
- `loanFunding`: `LoanFunding`
- `rateToBaseCurrency`: `Float`
- `earlyRedemption`: `Boolean`
- `duesCalculationMethod`: `DuesCalculationMethod`
- `isDataOverride`: `Boolean`
- `isOIDOverride`: `Boolean`
- `override`: `OverrideScheduleRow`
- `capitalizationComponent`: `CapitalizationComponent`
- `creationOpId`: `ID`
- `isDebtTransfer`: `Boolean`
- `equityTransaction`: `EquityTransaction`
- `loanFundingDebtSell`: `LoanFundingDebtSell`
- `transactionInput`: `LoanTransactionInputData`
- `oidOverride`: `OIDRow`
- `splittedLoanTransaction`: `LoanTransaction`
- `isPrepayment`: `Boolean`

### `LoanFunding`
- `id`: `ID!`
- `name`: `String`
- `fundingEntity`: `FundingEntity!`
- `fundingEntityIsServicer`: `Boolean`
- `fundingEntityReceivesMargins`: `Boolean`
- `loanFundingTerms`: `[LoanTerms!]!`
- `asset`: `Loan!`
- `description`: `String`
- `currency`: `Currency`
- `template`: `LoanFundingTemplate`
- `repaymentSchedule`: `LoanSchedule`
- `transactions`: `[LoanTransaction!]`
- `fees`: `[LoanFundingFee!]`
- `incomeFees`: `[LoanFee!]`
- `expenseFees`: `[LoanFee!]`
- `interestRatesData`: `[InterestRateData!]`
- `compoundingInterestRatesData`: `[InterestRateData!]`
- `interestUpdates`: `[InterestUpdate!]`
- `compoundingInterestUpdates`: `[InterestUpdate!]`
- `principalIndexUpdates`: `[InterestUpdate!]`
- `daysSettings`: `[DaysSettings!]`
- `duesCalculationMethod`: `DuesCalculationMethod`
- `dynamicTables`: `[DynamicTable!]`
- `notes`: `[Note!]`
- `fileEntriesCount`: `Int`
- `receivables`: `InstallmentComponents`
- `cashReceived`: `InstallmentComponents`
- `creationOpId`: `ID`
- `oidTerms`: `OIDTerms`
- `fundingSourcesManualAllocation`: `Boolean`
- `aggregateTranchesSchedules`: `Boolean`
- `debtSell`: `[LoanFundingDebtSell!]`
- `commitmentAmount`: `Float`
- `commitmentAmountInFundingEntityCurrency`: `Float`
- `participationPercentage`: `Float`
- `valuations`: `[LoanValuation!]`
- `matchLoanDaysSettings`: `Boolean`
- `currentInterestRate`: `Float`
- `currentCompoundingInterestRate`: `Float`
- `currentOidRemainingCost`: `Float`
- `deal`: `Deal`

### `PaginatedLoanFundings`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[LoanFunding!]!`

### `Client`
- `id`: `ID!`
- `type`: `ClientType!`
- `identificationNumber`: `String`
- `firstName`: `String`
- `lastName`: `String`
- `companyName`: `String`
- `displayName`: `String`
- `email`: `String`
- `mobileNumber`: `String`
- `isActive`: `Boolean`
- `createdAt`: `Date`
- `createdByUserId`: `ID`
- `description`: `String`
- `numOfActiveLoans`: `Int`
- `numOfPendingLoans`: `Int`
- `loans`: `PaginatedLoans`
- `equities`: `PaginatedEquities`
- `dataApplications`: `PaginatedDataApplications`
- `notes`: `[Note!]`
- `dynamicTables`: `[DynamicTable!]`
- `fileEntriesCount`: `Int`

### `PaginatedClients`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[ClientExtended!]!`

### `PieValues`
- `total`: `Float`
- `values`: `[GraphValue!]!`

### `ClientGraphValue`
- `date`: `Date!`
- `value`: `Float!`

### `Equity`
- `id`: `ID!`
- `refId`: `ID`
- `type`: `EquityType!`
- `status`: `AssetStatus!`
- `createdAt`: `Date`
- `name`: `String`
- `currency`: `Currency`
- `description`: `String`
- `acquisitionDate`: `Date`
- `expirationDate`: `Date`
- `expectedExerciseDate`: `Date`
- `exercisePricePerUnit`: `Float`
- `equityClass`: `String`
- `investmentRights`: `String`
- `summary`: `EquitySummary`
- `valuations`: `[EquityValuation!]`
- `allocations`: `[EquityAllocation!]`
- `transactions`: `[EquityTransaction!]`
- `expectedTransactions`: `[EquityTransaction!]`
- `fundingSources`: `[Investment!]`
- `notes`: `[Note!]`
- `fileEntriesCount`: `Int`
- `client`: `Client`
- `loan`: `Loan`
- `owners`: `[User!]`
- `audits`: `PaginatedAuditEntries`
- `dynamicTables`: `[DynamicTable!]`
- `exerciseEntries`: `[EquityExerciseEntry!]`
- `exercisedShare`: `Equity`
- `relatedWarrants`: `[Equity]`
- `equityKPIs`: `EquityKPIs`

### `PaginatedEquity`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[Equity!]!`

### `FundingEntity`
- `id`: `ID!`
- `name`: `String!`
- `logoUrl`: `String`
- `bankDetails`: `BankDetails`
- `baseCurrency`: `Currency!`
- `totalCommitment`: `Float`
- `totalDisbursement`: `Float`
- `contributed`: `Float`
- `currentAverageInterestRate`: `Float`
- `receivables`: `InstallmentComponents`
- `cashReceived`: `InstallmentComponents`
- `mergedLoanFundingsSummary`: `LoanSummary`
- `isInactive`: `Boolean`
- `fundedLoans`: `[LoanFunding!]`
- `dynamicTables`: `[DynamicTable!]`
- `notes`: `[Note!]`
- `fileEntriesCount`: `Int`
- `transactions`: `[FundingEntityTransaction!]`
- `kpis`: `LoanKPIs`
- `kpisAsyncUpdate`: `AsyncUpdate`
- `activeLoansCount`: `Int`
- `utilizationRate`: `Float`
- `totalReturned`: `Float`
- `expectedTotalValue`: `Float`
- `lastScheduleUpdate`: `DateTime`
- `commitmentBreakdown`: `CommitmentBreakdown`

### `PaginatedFundingEntities`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[FundingEntity!]!`

### `DocumentTemplate`
- `id`: `ID!`
- `label`: `String!`
- `type`: `DocTemplateType!`
- `docxTemplateUrl`: `String`

### `PaginatedUserNotifications`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[UserNotification!]!`

### `CustomDocumentTemplate`
- `id`: `ID`
- `name`: `String!`
- `mandatory`: `Boolean`
- `uploadedFileId`: `String`

### `PaginatedEquities`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[Equity!]!`

### `PaginatedDataApplications`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[DataApplication!]!`

### `PaginatedAuditEntries`
- `totalFilteredRecords`: `Int`
- `pageItems`: `[AuditEntry!]!`


## Query argument INPUT_OBJECT shapes (pagination / filter / sort)

> Pagination model is OFFSET-based: `skip` (Int) + `limit` (Int); `Paginated*` returns `{ totalFilteredRecords, pageItems }`. Walk pages by incrementing `skip` until accumulated count >= totalFilteredRecords.


### input `LoansFilterInput`
- `searchString`: `String`
- `hideTranches`: `Boolean`
- `hideMultiTrancheFacilities`: `Boolean`
- `submittedOnDate`: `PeriodInput`
- `startDate`: `PeriodInput`
- `endDate`: `PeriodInput`
- `loanStatus`: `[LoanStatusEnum!]`
- `lifeCycle`: `[LoanLifeCycle!]`
- `clientIds`: `[ID!]`
- `ownerIds`: `[ID!]`
- `productIds`: `[ID!]`
- `purpose`: `[String!]`
- `multiTrancheLoanIds`: `[ID!]`
- `fundingSourceIds`: `[ID!]`
- `commitmentGreaterThan`: `Float`
- `overdueGreaterThan`: `Float`
- `repaidGreaterThan`: `Float`
- `outstandingGreaterThan`: `Float`
- `distinctBy`: `LoansDistinctBy`
- `boardId`: `ID`
- `showGroupLoans`: `Boolean`
- `showOnlyGroupLoans`: `Boolean`
- `showOnlyMultiTrancheLoans`: `Boolean`

### input `LoansSortByInput`
- `field`: `LoanSortByFieldEnum!`
- `desc`: `Boolean!`

### input `LoanFundingsFilterInput`
- `searchString`: `String`
- `fundingEntityId`: `ID`
- `assetId`: `ID`
- `loanFundingId`: `ID`
- `excludeIds`: `[ID!]`

### input `ClientsFilterInput`
- `searchString`: `String`
- `inactiveOnly`: `Boolean`
- `currentCommitmentGreaterThan`: `Float`
- `outstandingBalanceGreaterThan`: `Float`
- `totalOverdueGreaterThan`: `Float`
- `nextPayment`: `PeriodInput`
- `lastPayment`: `PeriodInput`
- `submissionDate`: `PeriodInput`
- `distinctBy`: `ClientsDistinctBy`
- `boardId`: `ID`

### input `ClientsSortByInput`
- `field`: `ClientSortByFieldEnum!`
- `desc`: `Boolean!`

### input `EquitiesFilterInput`
- `searchString`: `String`
- `status`: `[AssetStatus!]`
- `clientIds`: `[ID!]`
- `equityClass`: `String`
- `type`: `[EquityType]`
- `acquisitionDate`: `PeriodInput`
- `holdingValueGreaterThan`: `Float`
- `costGreaterThan`: `Float`
- `totalExercisePriceGreaterThan`: `Float`
- `ownerIds`: `[ID]`

### input `FundingEntitiesFilterInput`
- `searchString`: `String`
- `excludeIds`: `[ID!]`
- `activeLoansGreaterThan`: `Int`
- `utilizationRateMin`: `Float`
- `utilizationRateMax`: `Float`
- `committedGreaterThan`: `Float`
- `deployedGreaterThan`: `Float`
- `totalReturnedGreaterThan`: `Float`
- `expectedTotalValueGreaterThan`: `Float`
- `irrGreaterThan`: `Float`
- `expectedIrrGreaterThan`: `Float`
- `tvpiGreaterThan`: `Float`
- `expectedTvpiGreaterThan`: `Float`
- `dpiGreaterThan`: `Float`
- `inactiveOnly`: `Boolean`

### input `FundingEntitiesSortByInput`
- `field`: `FundingEntitySortByFieldEnum!`
- `desc`: `Boolean!`

### input `NotificationsFilterInput`
- `unreadOnly`: `Boolean`
- `startDate`: `Date`
- `endDate`: `Date`
- `type`: `[NotificationType!]`
- `entityType`: `[NotificationEntityType!]`

### input `PeriodInput`
- `startDate`: `Date`
- `relativeStartDate`: `RelativeDateInput`
- `endDate`: `Date`
- `timeInterval`: `FrequencyEveryEnum`
- `timeIntervalMultiplier`: `Int`

### input `RelativeDateInput`
- `type`: `RelativeDateType`
- `timeUnit`: `FrequencyEveryEnum`
- `amount`: `Int`
