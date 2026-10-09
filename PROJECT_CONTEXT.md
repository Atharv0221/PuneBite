# PROJECT_CONTEXT.md — PuneBite Analyzer

> **How to use:** Paste this whole file at the start of every new Claude chat (yours or your friend's).
> After finishing any task, update the **Progress** section and commit it to GitHub.

## 1. Project summary
- **Course:** ITE01301 Data Science & Machine Learning, TY B.Tech IT (2024 Pattern), PES's Modern College of Engineering
- **Topic:** Restaurant Customer Review & Ratings Analysis in a Locality (Zomato, Pune)
- **Project name:** PuneBite Analyzer
- **Team:** 2 students. Person A = Data/ML. Person B = Backend/Frontend/DB.
- **Deadline:** _(fill in)_
- **Chatbot (optional, query-based):** _(yes / no — decide after Phase 5)_

## 2. Tech stack (restricted)
- Python: pandas, numpy, scikit-learn, mlxtend, scipy, statsmodels, matplotlib, seaborn
- Backend: Flask or FastAPI (Python)
- Database: MongoDB (no Cassandra, XML optional/skip)
- Frontend: React + HTML + CSS
- Tools: VS Code, Jupyter, Git/GitHub

## 3. Dataset facts (file: `zomato_pune_V002.csv`)
- 12,189 rows x 104 columns; 99 localities (39 have >=100 restaurants)
- Columns: Restaurant_Name, Web_Link, Locality, Sponsored (**actually restaurant type**), Ratings_out_of_5, Number of votes (text like "7029  votes"), Phone_number, Cuisines (comma-separated), Charges_for_two (text like "₹1,400"), payment_modes, Rest_timming, Detail_address, 5/4/3/2/1_star_review_percentage (text like "79%"), 86 binary amenity columns, spam_review (numeric; meaning undocumented — verify)
- **No latitude/longitude. No dining/delivery rating split. No review text.**

### Known data issues
| Issue | Detail | Plan |
|---|---|---|
| Unrated | 3,269 rows have rating "-" | Keep for EDA; exclude from rating models |
| Rating 0.0 | 1,208 rows; ALL have 0 votes, so it is a placeholder, not a score | Converted to NaN (done in Phase 1) |
| Zero votes | 4,494 rows | Ratings unreliable; use votes threshold |
| Price missing | 2,117 "Not Present" | Impute by locality+type median, or drop for price models |
| Price outlier | max ₹200,250 vs median ₹400 | Detect with IQR, cap or remove |
| Duplicates | 55 duplicate rows/links | Dropped (12,189 -> 12,134 rows) |
| Imbalance | after cleaning: 7,669 rated, median 3.4, only ~11% are >=4.0 | class_weight / SMOTE; judge by F1 & ROC-AUC, not accuracy |
| Sparse amenities | many binary columns ~all zeros | Drop near-constant; feature selection / PCA |
| **Leakage** | star-percentage columns are what the rating is built from | **Never use as model features**; analysis only |

## 4. Rename map (cleaned column names)
| Original | Clean |
|---|---|
| Restaurant_Name | name |
| Web_Link | url |
| Locality | locality |
| Sponsored | establishment_type |
| Ratings_out_of_5 | rating |
| Number of votes | votes (int) |
| Cuisines | cuisines (list) |
| Charges_for_two | cost_for_two (int) |
| Rest_timming | timings |
| Detail_address | address |
| payment_modes | payment_modes |
| 5_star..1_star_review_percentage | star5_pct .. star1_pct (float) |
| spam_review | spam_review_count |
| 86 binary columns | snake_case binary columns in the ML CSV, plus pipe-joined `amenities` string (split on `\|` for MongoDB) |

### Cleaned file notes (`restaurants_clean.csv`)
- Lists are pipe-separated strings: `cuisines`, `amenities`. Also: `primary_cuisine`, `primary_type`, `n_cuisines`, `n_amenities`
- `rating` is NaN for unrated; `has_rating` flag; `votes` is int
- `cost_for_two` = raw (NaN if missing); `cost_capped` = imputed + capped at 99th pct (use this for models); `cost_missing` flag
- Star columns: `star5_pct..star1_pct` (NaN if no reviews) + `positive_pct`, `extreme_pct`, `polarization_pct` (analysis only, NOT model inputs)
- `accepts_cards`, `accepts_digital`, 86 amenity binary columns

## 5. Folder structure
```
punebite-analyzer/
├── PROJECT_CONTEXT.md
├── README.md
├── .gitignore
├── data/
│   ├── raw/zomato_pune_V002.csv
│   └── processed/restaurants_clean.csv
├── notebooks/
│   ├── 01_cleaning.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_statistics.ipynb
│   ├── 04_classification.ipynb
│   ├── 05_regression.ipynb
│   ├── 06_feature_selection_pca.ipynb
│   ├── 07_clustering.ipynb
│   └── 08_association_rules.ipynb
├── ml/
│   ├── cleaning.py          # reusable cleaning functions
│   ├── features.py          # builds model inputs (used by notebooks AND the API)
│   ├── scoring.py           # trust-adjusted rating, hidden gems
│   └── models/              # saved .joblib models
├── backend/
│   ├── app.py
│   ├── db.py                # MongoDB connection
│   ├── load_data.py         # CSV -> MongoDB
│   └── requirements.txt
├── frontend/                # React app
│   └── src/
├── report/
└── docs/
```

## 6. Phases (do in order; * = can be cut if short on time)
| # | Phase | Owner | Output |
|---|---|---|---|
| 0 | Setup: repo, venv, folders, MongoDB, agree API contract | Both | Working repo |
| 1 | Cleaning (`01_cleaning`) | A | `restaurants_clean.csv` |
| 2 | EDA (`02_eda`) | A | Charts, pivot tables, findings |
| 3 | Statistics (`03_statistics`): t-test, ANOVA, chi-square | A | Hypotheses + results |
| 4 | Classification + Regression (`04`, `05`) | A | Model comparison, saved best model |
| 5 | Feature selection/PCA, Clustering, Apriori (`06`-`08`) | A | Segments, rules |
| 6 | MongoDB load + REST API | B | Running API |
| 7 | React dashboard | B | Filters, charts, explorer, locality report card |
| 8* | Trust-adjusted rating + Hidden Gems | A then B | Score + UI page |
| 9* | Query-based chatbot | B (A helps) | "best cheap biryani in Kothrud" |
| 10 | Report, PPT, viva prep | Both | Final submission |

Phase 6-7 can start in parallel once Phase 1 produces the clean CSV.

## 7. Planned statistical tests (Phase 3)
- t-test: rating of restaurants with vs. without Outdoor Seating (also Vegetarian Only)
- ANOVA: rating across establishment types
- Chi-square: locality (top localities) vs. high/low rating

## 8. ML plan
- **Classification target:** `high_rated` = rating >= 4.0 (rated restaurants only, votes >= threshold, e.g. 20)
- **Features:** cost_for_two, votes, establishment_type, locality (encoded), selected amenities, number of cuisines. **No star_pct columns.**
- **Models:** Decision Tree, Random Forest, SVM, KNN, Logistic Regression. Metrics: confusion matrix, precision, recall, F1, ROC-AUC. Use K-Fold CV.
- **Regression:** Linear, Ridge, Lasso -> predict rating. Metrics: MSE, RMSE, R².
- **Clustering:** K-Means on cost, rating, votes, polarity (star5_pct vs star1_pct). Pick k with elbow/silhouette.
- **Apriori:** transactions = cuisines and/or amenities per restaurant; report support, confidence, lift.
- **Trust-adjusted rating:** `(v/(v+m))*R + (m/(v+m))*C`, with R = restaurant rating, v = votes, m = min votes threshold, C = mean rating.

## 9. API contract (draft — agree and freeze early)
- `GET /api/restaurants?locality=&cuisine=&min_rating=&max_cost=&type=&page=`
- `GET /api/localities` -> list with avg rating, avg cost, count, top cuisines
- `GET /api/localities/{name}` -> locality report card
- `GET /api/hidden-gems?locality=`
- `GET /api/stats/overview` -> chart data
- `POST /api/predict` -> body: cost, votes, type, locality, amenities -> predicted high_rated probability
- Restaurant JSON: `{ name, url, locality, establishment_type, rating, votes, trust_rating, cost_for_two, cuisines[], amenities[], star_pct{5,4,3,2,1}, timings, address }`

## 10. Conventions
- Python 3.10+, virtual environment `.venv` (not committed)
- Git: branch per person (`ml-work`, `app-work`), merge to `main` via pull request
- Never commit large/secret files; keep `.env` for the MongoDB URI
- Set `random_state=42` everywhere
- Every notebook starts with a markdown cell: objective, input, output

## 11. Progress (update after each task)
- [ ] Phase 0 Setup
- [x] Phase 1 Cleaning (`ml/cleaning.py` + `notebooks/01_cleaning.ipynb` -> `data/processed/restaurants_clean.csv`, 12,134 x 116)
- [x] Phase 2 EDA (`02_eda.ipynb`)
- [x] Phase 3 Statistics (`03_statistics.ipynb`)
- [x] Phase 4 Classification + Regression (`04_classification.ipynb`, `05_regression.ipynb`)
- [ ] Phase 5 Feature selection / Clustering / Apriori (06 feature selection + PCA DONE; 07 clustering and 08 Apriori pending)
- [ ] Phase 6 MongoDB + API
- [ ] Phase 7 React dashboard
- [ ] Phase 8 Hidden Gems
- [ ] Phase 9 Chatbot
- [ ] Phase 10 Report / PPT

**Last completed:** Phases 0-4, plus `06_feature_selection_pca.ipynb`
**Next task:** `07_clustering.ipynb`, or Phase 6 (MongoDB + API) in parallel
**Decisions / notes:**
- Rating 0.0 = placeholder for no reviews (all have 0 votes) -> NaN. 7,669 rated restaurants.
- Votes strongly tied to rating (Spearman ~0.73; <5 votes avg 3.04, 500+ votes avg 4.07). Define `popular` = votes >= 50 (3,012 rows) for robustness checks.
- Stats finding: outdoor_seating / vegetarian_only look significant overall but NOT among popular restaurants (confounded by votes). table_booking_recommended and premium amenities stay significant. Type explains ~8% of rating variance (eta^2 0.076); locality vs rating tier Cramer's V ~0.19.
- Classification (target rating >= 4.0, 11.2% positive): Random Forest best. Scenario A (with votes) test AUC ~0.94, F1 ~0.67. Scenario B (no votes, for Opening Advisor) AUC ~0.82, F1 ~0.50. Saved: `ml/models/high_rating_classifier.joblib` + `_meta.json` (Scenario B, includes feature spec and threshold ~0.5). The API must build inputs with `ml/features.py` `make_features(df, spec)`.
- Regression (target rating): Scenario A R2 ~0.55, RMSE ~0.28; Scenario B (no votes) R2 ~0.28, RMSE ~0.36 (baseline 0.43). Regularisation made little difference (large n, few features); Lasso zeroed 27 of 95 encoded features. Saved: `ml/models/rating_regressor.joblib` + `_meta.json` (Scenario B, Polynomial deg2 + Ridge). Residuals show regression to the mean (over-predicts low, under-predicts high ratings).
- Feature selection (06): 14 consensus features (price, n_amenities, n_cuisines, accepts_cards, table_booking_recommended, full_bar_available, brunch, valet_parking_available, live_music, smoking_are, cuisines desserts/continental/italian, type Quick Bites) saved to `ml/models/selected_features.json`. More features = higher AUC (0.74 @5, 0.77 @20, 0.825 @150), so selection is for interpretation, not accuracy. PCA: 24 comps = 90% of amenity variance; ~50 comps on all features matches raw AUC.
- Modelling caution: votes is a very strong predictor but partly reflects popularity; compare models with and without votes.

## 12. Starter prompt for a new chat
> I'm working on the PuneBite Analyzer mini-project (context above). Please continue from "Next task" in the Progress section. Give me complete, runnable code, explain it briefly in viva-friendly language, and tell me exactly what to update in PROJECT_CONTEXT.md when we finish.
