# Udyam Verification Test for FDA Green List Firms

## Overview
This document logs the results of a manual verification test performed on a sample of 4 firms from the FDA Import Alert "Green List". The objective was to determine if public Udyam portal search is a feasible mechanism for identifying MSME status in the FDA dataset, and to assess whether the "Green List" correlates with MSME scale.

## Firms Tested
The following 4 Green-List firms were manually queried on udyamregistration.gov.in using name-based searches:

### 1. ANJANEYA SEA FOODS
- **Status**: No conclusive Udyam Registration Number is publicly indexable via name search alone.
- **Note**: General web searches may reveal entities with similar names in various districts (e.g., Nellore/Prakasam), but verifying exact URNs without the principal's PAN/Aadhaar is not supported by the Udyam portal's security model.

### 2. ALPHA MARINE LIMITED / ALPHA MARINE
- **Status**: No Udyam Registration Number is publicly indexed for this exact entity.
- **Note**: This company operates as a large enterprise with a paid-up capital of INR 63,75,60,310. It heavily exceeds the statutory financial thresholds required to hold a valid MSME classification.

### 3. APEX FROZEN FOODS LIMITED
- **Status**: No Udyam Registration Number is publicly indexed.
- **Note**: This entity appears in major corporate and stock registries, indicating it operates as a large corporate enterprise rather than an MSME.

### 4. AQUATECH FEED & SEAFOODS PRIVATE LIMITED
- **Status**: No Udyam Registration Number is publicly indexed.
- **Note**: The entity either is not registered as an MSME, or its URN has not been published on any open-source platforms, public tenders, or corporate filings.

## Conclusion
1. **Infeasibility of Automated Search**: The Udyam portal's structure (CAPTCHA walls, exact-URN search requirements, lack of public name index) prevents automated, script-based resolution of firm size. We cannot independently scrape the registry.
2. **Structural Bias**: The FDA "Green List" (firms exempted from Detention Without Physical Examination due to demonstrated compliance capacity) skews heavily toward large, well-resourced corporate enterprises (e.g., Apex Frozen Foods, Alpha Marine). 
3. **Implications**: Conflating Green List firms with MSMEs simply because they appear in an FDA alert introduces a critical bias away from the target MSME population. Green List hit logic must be isolated from MSME scale logic.
