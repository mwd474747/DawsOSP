# Critical Decisions Framework
**Date**: October 21, 2025
**Purpose**: Make strategic decisions based on product intentions and vision
**Approach**: Evidence-based recommendations from vision analysis

---

## DECISION FRAMEWORK: Product Vision as North Star

Your product vision documents reveal clear intentions. Let me extract the decision drivers:

### Core Product Intentions (From Your Documents)

**1. From Master Vision**:
> "Trinity aims to become a **portfolio‑first intelligence platform** that goes **far beyond traditional stock research sites**. The goal is to give investors a **single source of truth** for everything that affects their portfolio."

**2. From Product Vision**:
> "DawsOS is a **transparent intelligence platform** where understanding HOW decisions are made is as important as the decisions themselves."

**3. From Macro Analysis**:
> "**Sophisticated portfolio intelligence** that goes beyond Seeking Alpha"

**Key Themes in YOUR Vision**:
- ✅ **Portfolio-first** (not stock-first)
- ✅ **Transparent intelligence** (show HOW, not just WHAT)
- ✅ **Professional/sophisticated** (not amateur/casual)
- ✅ **Single source of truth** (integrated, not bolted-on)

---

## DECISION 1: Target User (Who Are We Building For?)

### The Evidence from Your Vision

**Master Vision explicitly states**:
> "Users think in terms of portfolios (positions, weights, risk budget), not isolated charts."
> "Multi‑currency attribution is critical: investors need to see local return, FX return and the interaction term separately."
> "A Beancount ledger anchored by daily 'pricing packs' provides **auditable accounting**."

**Keywords**: "auditable accounting", "multi-currency", "portfolio risk budget"

**This describes**: Professional/sophisticated investors, NOT casual retail

**Your Product Vision comparison table**:
| Feature | Seeking Alpha | **DawsOS (Target)** |
|---------|---------------|---------------------|
| Portfolio Upload | Basic tracking | ✅ **Upload CSV, auto-sync, position sizing** |
| Risk Models | Beta, volatility | ✅ **Concentration + Correlation + Macro sensitivity** |
| Custom Ratings | Community-driven | ✅ **Quantitative models** |
| Data Quality | Standard | ✅ **Transparent sourcing, confidence scores** |

**This compares to**: Bloomberg ($2,000/mo) and Morningstar ($250/mo), NOT Seeking Alpha ($30/mo)

### RECOMMENDATION: Target User

**Primary Target**: 🎯 **Professional and Sophisticated INDIVIDUAL Investors**

**Profile**:
- **Individual investors** (NOT institutions, NOT advisors managing client money)
- Portfolio size: $250K-$10M (too small for Bloomberg, too sophisticated for Seeking Alpha)
- Holdings: 15-50 positions across multiple currencies
- Needs: Multi-currency attribution, auditable results, macro analysis
- Willing to pay: $100-500/mo (between Seeking Alpha and Morningstar)

**Why This Makes Sense**:
1. ✅ Master Vision explicitly calls out "multi-currency attribution is **critical**"
2. ✅ Beancount ledger = professional accounting (not needed for casual users)
3. ✅ "Auditable accounting" and "pricing packs" = compliance/tax requirements
4. ✅ Competitive comparison targets Bloomberg/Morningstar (not Seeking Alpha)

**Secondary Target**: Canadian/European investors (CAD/EUR base currency)
- Master Vision uses CAD examples throughout
- Multi-currency is table-stakes for this segment

### Implication for Roadmap

**DECISION**: ✅ **Include multi-currency in MVP (Week 2, +2-3 days)**

**Rationale**: Your vision document explicitly states "multi-currency attribution is **critical**". If we exclude this, we're building a different product than intended.

**Timeline Impact**: 7-8 weeks (not 6 weeks)

---

## DECISION 2: Business Model (How Do We Monetize?)

### The Evidence from Your Vision

**From competitive analysis**:
> "DawsOS vs Seeking Alpha: Transparent intelligence + **Portfolio-centric** + Macro integration"

**From Master Vision**:
> "**Professional portfolio intelligence platform**"
> "Reports exported to PDF or Excel must include timestamps, **methodology links** and source attributions."

**Keywords**: "professional", "PDF reports", "methodology", "auditable"

**This suggests**: B2B or Professional B2C, NOT free consumer

**Price Points (from competitive analysis)**:
- Seeking Alpha: $30/mo (casual retail)
- Morningstar: $250/mo (professional retail)
- Bloomberg: $2,000/mo (institutional)

### RECOMMENDATION: Business Model

**Primary Model**: 🎯 **B2C Professional (Freemium with Professional Tier)**

**Pricing Structure**:

**Free Tier** (Acquisition):
- 1 portfolio (max 10 holdings)
- Basic dashboards (Market Overview, Economic Dashboard)
- Pattern execution (limited to 10/day)
- Transparency visible (hook to show value)
- **Purpose**: Demonstrate transparency differentiator

**Professional Tier** ($149/mo or $1,490/yr):
- Unlimited portfolios
- Multi-currency support
- Full macro analysis (factor exposures, scenario analysis)
- Custom ratings (dividend safety, moat, recession resilience)
- PDF/Excel exports with methodology
- API access
- **Purpose**: Revenue from sophisticated investors

**Enterprise/Advisor Tier** ($499/mo) - FUTURE, NOT MVP:
- Multi-client management
- White-label reports
- Bulk portfolio analysis
- Priority support
- **Purpose**: Serve financial advisors with multiple clients (deferred to post-PMF)

**Why This Makes Sense**:
1. ✅ Aligns with "professional platform" positioning
2. ✅ Free tier showcases transparency differentiator (competitive advantage)
3. ✅ Professional tier captures value from sophisticated users ($250K+ portfolios)
4. ✅ Price point between Morningstar ($250) and Bloomberg ($2,000) has room
5. ✅ Freemium allows viral growth while monetizing serious users

### Implication for Roadmap

**DECISION**: ✅ **Build for Professional tier features from start**

**Rationale**: Freemium doesn't mean "build free first". Build professional features (multi-currency, Beancount, pricing packs), then gate them.

**Week 0 (Beancount + Pricing Packs)**: REQUIRED for professional tier
- Free tier can use JSON files
- Professional tier gets Beancount ledger + reproducibility

**MVP Target**: Free tier + Professional tier (both functional)

---

## DECISION 3: MVP Definition (What's "Minimum Viable"?)

### The Evidence from Your Vision

**Master Vision explicitly defines phases**:
> "Phase 1 – Core Infrastructure (2 weeks): Beancount ledger, Pricing Pack service"
> "Phase 2 – Portfolio Foundation (2 weeks): TWR/MWR, currency attribution"
> "Phase 3 – Macro & Risk Integration (2 weeks): Factor exposures, DAR, scenarios"

**This is clear**: Infrastructure FIRST, then features

**Your Product Vision says**:
> "Transparency is THE Core Differentiator"
> "Portfolio-Centric Analysis (Contextual Intelligence)"
> "Dashboard ↔ Chat ↔ Portfolio Integration"

**Three pillars**: Transparency + Portfolio + Macro

### RECOMMENDATION: MVP Definition

**MVP = "Demonstrable Professional Platform" (8 Weeks)**

**Must-Have (Non-Negotiable)**:
1. ✅ **Beancount ledger** (Week 0) - Ledger-of-record for professional users
2. ✅ **Pricing packs** (Week 0) - Reproducible valuations
3. ✅ **Multi-currency** (Week 2) - CAD/EUR/USD support
4. ✅ **Macro integration** (Weeks 1-3) - Factor exposures, scenarios, causal KG
5. ✅ **Transparency UI** (Week 4) - Execution trace with provenance
6. ✅ **Portfolio-centric dashboards** (Week 3) - Portfolio as PRIMARY view

**Nice-to-Have (Can Defer)**:
- ⏸️ Advanced ratings (Week 5) - Can launch with basic ratings
- ⏸️ News impact analysis (Week 5) - Can add post-launch
- ⏸️ PDF exports (Week 6) - Can add when advisors sign up
- ⏸️ Service layer + Database (Weeks 7-14) - Only if >1000 users at launch

**Why This Definition**:
1. ✅ Matches Master Vision Phases 1-4 (infrastructure → portfolio → macro → transparency)
2. ✅ All three pillars delivered (transparency + portfolio + macro)
3. ✅ Professional features (multi-currency, ledger, pricing) included
4. ✅ Can charge $149/mo (not just free tier)

### Implication for Roadmap

**DECISION**: ✅ **Adopt "Foundation+" 8-Week Roadmap**

**Rationale**: Master Vision is correct - infrastructure BEFORE features. Your vision explicitly prioritizes professional capabilities.

**NOT**: 6-week feature-first plan (missing foundations)

---

## DECISION 4: Scale Target (How Many Users at Launch?)

### The Evidence from Your Vision

**From Master Vision**:
> "Trinity should be built as a set of **well‑defined services** that can **scale independently**."

**But also**:
> "Phase 1 – Core Infrastructure" comes BEFORE "Phase 6 – Continuous Improvement & Extensions"

**This suggests**: Plan for scale, but build iteratively

**Your current architecture** (from CURRENT_STATE.md):
- JSON files for storage
- NetworkX in-memory graph
- Streamlit single-threaded
- No database, no caching

**Capacity**: ~100 users maximum

### RECOMMENDATION: Scale Target

**Launch Target**: 🎯 **100-500 Beta Users** (Not 10,000+)

**Strategy**: "Professional Beta → Scale After PMF"

**Phase 1 (Weeks 1-8)**: Beta Architecture
- Beancount ledger (scales to 1000s of portfolios)
- Pricing packs (scales - just files)
- JSON files for knowledge datasets (acceptable for beta)
- NetworkX in-memory (fine for <500 users)
- Streamlit (fine for beta feedback loops)

**Phase 2 (Weeks 9-12)**: Beta Launch
- Recruit 50-100 sophisticated investors
- Freemium: 80% free tier, 20% professional tier ($149/mo)
- Target: $15K MRR (100 professional tier users × $150)
- Focus: Product-market fit, not scale

**Phase 3 (Weeks 13-20)**: Scale Infrastructure (IF PMF validated)
- Migrate to Postgres + TimescaleDB
- Add service layer (FastAPI)
- Add background workers (Celery)
- Add Redis caching
- Target: 1,000-5,000 users

**Why This Makes Sense**:
1. ✅ Master Vision acknowledges phases (infrastructure → features → scale)
2. ✅ Premature optimization wastes time (YAGNI principle)
3. ✅ Beta with 100 users validates PMF before investing in scale
4. ✅ Current architecture (+ Beancount + pricing packs) handles 100-500 users fine

### Implication for Roadmap

**DECISION**: ✅ **Build for Beta (100-500 users), Plan for Scale**

**Week 0-8**: Beta architecture (Beancount + Pricing packs + Current stack)
**Week 9-12**: Beta launch (focus on PMF, not scale)
**Week 13+**: Scale infrastructure (ONLY if PMF validated and growth demands it)

**NOT**: Build for 10,000 users on Day 1 (over-engineering)

---

## DECISION 5: Launch Timeline (When to Ship?)

### The Evidence from Your Vision

**Master Vision phases**:
- Phases 1-5: 10 weeks (infrastructure → features)
- Phase 6: Ongoing (continuous improvement)

**Your competitive positioning**:
> "DawsOS vs Seeking Alpha: Transparent intelligence + Portfolio-centric + Macro integration"

**Question**: Can we ship a competitive product in 6 weeks? Or do we need 8-10 weeks?

### RECOMMENDATION: Launch Timeline

**Target Launch**: 🎯 **8 Weeks from Start (Foundation+ Roadmap)**

**Why 8 Weeks (Not 6, Not 10)**:

**Why NOT 6 Weeks** (Current Plan):
- ❌ Missing Beancount (not professional)
- ❌ Missing pricing packs (not auditable)
- ❌ Missing multi-currency (excludes international users)
- ❌ Feature-first (weak foundations)
- **Result**: Impressive demo, but can't charge $149/mo

**Why NOT 10 Weeks** (Full Master Vision):
- ✅ Includes everything above
- ❌ Includes service layer + database (over-engineering for beta)
- ❌ Delays PMF validation by 2 extra weeks
- **Result**: Perfect architecture, but delayed market feedback

**Why 8 Weeks** (Foundation+ Hybrid):
- ✅ Includes Beancount + Pricing packs (professional)
- ✅ Includes multi-currency (international)
- ✅ Includes macro integration (sophisticated)
- ✅ Includes transparency UI (differentiator)
- ⏸️ Defers service layer + database (add when scaling)
- **Result**: Professional platform, can charge $149/mo, fast PMF validation

### Implication for Roadmap

**DECISION**: ✅ **8-Week Launch Timeline (Foundation+ Roadmap)**

**Milestones**:
- **Week 0**: Beancount + Pricing packs (infrastructure)
- **Week 4**: Transparency UI with provenance (differentiator)
- **Week 6**: Advanced features (ratings, news)
- **Week 8**: Beta launch (50-100 users)
- **Week 12**: PMF validation (100+ professional tier users? $15K+ MRR?)

---

## SYNTHESIZED RECOMMENDATIONS

Based on your product vision and intentions, here are the **evidence-based decisions**:

### 1. Target User
**DECISION**: 🎯 **Professional and Sophisticated INDIVIDUAL Investors**
- **Individual investors** (NOT institutions, NOT advisors)
- Portfolio: $250K-$10M
- Holdings: 15-50 positions, multi-currency
- Needs: Auditable, reproducible, macro-aware
- Willingness to pay: $100-500/mo

**Rationale**: Master Vision explicitly calls out multi-currency as "critical" and uses professional features (Beancount, pricing packs, PDF reports). Focus on individual investors managing their own portfolios.

---

### 2. Business Model
**DECISION**: 🎯 **B2C Professional Freemium**
- Free Tier: 1 portfolio, basic dashboards, 10 patterns/day
- Professional Tier: $149/mo (unlimited portfolios, multi-currency, PDF exports)
- Enterprise/Advisor Tier: $499/mo (multi-client, white-label)

**Rationale**: Positions between Morningstar ($250) and Seeking Alpha ($30), leverages transparency as free tier hook

---

### 3. MVP Definition
**DECISION**: 🎯 **"Demonstrable Professional Platform" (8 Weeks)**
- Must-Have: Beancount + Pricing packs + Multi-currency + Macro integration + Transparency UI
- Nice-to-Have (defer): Advanced ratings, News impact, PDF exports, Service layer

**Rationale**: Master Vision Phases 1-4 = infrastructure + portfolio + macro + transparency. This IS the MVP.

---

### 4. Scale Target
**DECISION**: 🎯 **Beta Launch (100-500 Users)**
- Phase 1 (Weeks 1-8): Beta architecture (current stack + Beancount + pricing)
- Phase 2 (Weeks 9-12): Beta launch (50-100 users, validate PMF)
- Phase 3 (Weeks 13-20): Scale infrastructure (ONLY if PMF validated)

**Rationale**: Premature optimization wastes time. Validate PMF with 100 users before investing in scale.

---

### 5. Launch Timeline
**DECISION**: 🎯 **8 Weeks (Foundation+ Roadmap)**
- Week 0: Beancount + Pricing packs
- Weeks 1-3: Macro integration + Portfolio-centric UI
- Week 4: Transparency UI
- Weeks 5-6: Advanced features
- Week 8: Beta launch

**Rationale**: 6 weeks = weak foundations (can't charge $149). 10 weeks = over-engineering (delays PMF). 8 weeks = professional platform + fast PMF validation.

---

## REVISED ROADMAP (8 Weeks) - FINAL

### WEEK 0: Ledger & Pricing Infrastructure ⚡
**Days 1-3**: Beancount integration
**Days 4-5**: Pricing pack service
**Deliverable**: ✅ Professional accounting foundation

### WEEK 1: Macro Exposures + Causal KG ⚡
**Days 1-2**: Macro exposures dataset (duration, inflation, FX, commodity)
**Days 3-4**: Causal knowledge graph (Oil Price ↑ → Energy Profits ↑)
**Day 5**: Test macro queries
**Deliverable**: ✅ Macro → fundamentals connected

### WEEK 2: Pattern Integration + Multi-Currency ⚡
**Days 1-2**: Macro-fundamental patterns (macro_impact_stock, portfolio_scenario, regime_risk)
**Day 3**: Pattern chaining (output of pattern A → input of pattern B)
**Days 4-5**: Multi-currency support (local + FX + interaction returns)
**Deliverable**: ✅ Sophisticated analysis + International-ready

### WEEK 3: Portfolio-Centric UI ⚡
**Days 1-2**: Portfolio Overview as PRIMARY dashboard (macro integrated, holdings with betas)
**Day 3**: Macro-annotated Stock Analysis ("Recession exposure: HIGH")
**Day 4**: Scenario analysis widget ("What if rates rise 1%?")
**Day 5**: Dashboard integration (Economic Dashboard → Portfolio exposure)
**Deliverable**: ✅ Portfolio-first architecture

### WEEK 4: Transparency UI with Provenance ⚡
**Days 1-2**: Execution trace panel (pattern → agent → capability → data + KG causal paths)
**Day 3**: Provenance display (pricing pack ID, ledger commit hash)
**Day 4**: Click-to-explain (all metrics show calculation)
**Day 5**: Test full transparency (reproducibility validation)
**Deliverable**: ✅ FULLY auditable transparency

### WEEK 5: Custom Ratings + News Impact ⚡
**Days 1-2**: Rating engine (dividend safety, moat, recession resilience)
**Day 3**: Rating display (badges, click → breakdown)
**Days 4-5**: News impact analysis (portfolio-weighted sentiment)
**Deliverable**: ✅ Professional analytics

### WEEK 6: Advanced Features + Polish ⚡
**Days 1-2**: Factor exposure analysis (value, growth, momentum)
**Day 3**: Correlation matrix (holdings heatmap)
**Day 4**: Performance attribution (stock selection vs sector)
**Day 5**: Final polish (UI, error handling, edge cases)
**Deliverable**: ✅ Bloomberg-level analytics

### WEEKS 7-8: Beta Launch Prep ⚡
**Week 7**: Testing, bug fixes, documentation
**Week 8**: Beta launch (recruit 50-100 users, onboarding)

---

## CRITICAL SUCCESS METRICS (PMF Validation)

### Week 8 (Beta Launch):
- ✅ 50-100 users signed up
- ✅ 20% conversion to professional tier ($149/mo)
- ✅ $3K-15K MRR

### Week 12 (PMF Validation):
- ✅ 100-200 users (80% retention)
- ✅ 25% conversion to professional tier
- ✅ $15K-30K MRR
- ✅ NPS > 40 (professionals love it)

### If PMF Validated → Week 13+:
- Raise seed round ($500K-1M)
- Build scale infrastructure (Postgres, service layer, workers)
- Grow to 1,000-5,000 users

### If PMF NOT Validated → Pivot:
- Interview users: What's missing?
- Adjust positioning or features
- Iterate rapidly (benefit of beta architecture)

---

## FINAL RECOMMENDATION

**Your product vision is CLEAR and CORRECT**:
1. Portfolio-first (not stock-first)
2. Transparent intelligence (show HOW)
3. Professional/sophisticated (not casual)
4. Multi-currency (international)

**The 6-week feature-first plan contradicts this vision**.

**The 8-week Foundation+ plan ALIGNS with your vision**:
- Week 0: Professional foundations (Beancount, pricing packs)
- Weeks 1-3: Sophisticated analysis (macro integration, multi-currency)
- Week 4: Transparency (with FULL provenance)
- Weeks 5-6: Professional features (ratings, news, factors)
- Week 8: Launch to 50-100 sophisticated users @ $149/mo

**Expected Outcome**:
- $3K-15K MRR by Week 8 (20 professional tier users × $150)
- PMF validation by Week 12 ($15K-30K MRR)
- Scale decision by Week 13 (invest in infrastructure if PMF strong)

**Timeline**: +2 weeks vs current plan (8 weeks vs 6 weeks)
**Benefit**: Professional platform that can charge $149/mo (not just free tier)
**ROI**: 2 extra weeks = 4-6 weeks saved on refactoring + ability to monetize

---

## NEXT STEPS

1. ✅ **APPROVE** these decisions (target user, business model, MVP, scale, timeline)
2. ✅ **ADOPT** 8-week Foundation+ roadmap
3. ✅ **UPDATE** MASTER_TASK_LIST.md with revised plan
4. ✅ **BEGIN** Week 0 Day 1: Beancount integration research
5. ✅ **COMMUNICATE** to team: "We're building a professional platform, not a toy"

**Status**: 🎯 **Evidence-based decisions aligned with product vision**
