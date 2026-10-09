# PROJECT_CONTEXT.md — PuneBite Analyzer

> **How to use:** Paste this whole file at the start of every new Claude chat (yours or your friend's).
> After finishing any task, update the **Progress** section and commit it to GitHub.
>
> **HANDOFF STATUS (read first):** Phases 0-5a are finished and tested on the real data (cleaning, EDA, statistics,
> classification, regression, feature selection + PCA). The previous Claude account reached its limit.
> The next Claude chat continues from **Section 13 (task specs)**. Work one task at a time, test code on the real data, and
> keep the same style as the finished notebooks (see Section 12).

## 1. Project summary
- **Course:** ITE01301 Data Science & Machine Learning, TY B.Tech IT (2024 Pattern), PES's Modern College of Engineering
- **Topic:** Restaurant Customer Review & Ratings Analysis in a Locality (Zomato, Pune)
- **Project name:** PuneBite Analyzer
- **GitHub repo:** https://github.com/Atharv0221/PuneBite (public, default branch `master`)
- **Team:** 2 students. Person A = Data/ML (done through Phase 5a). Person B (friend) = continues with Phase 5b onward, then Backend/Frontend/DB.
- **Deadline:** _(fill in)_
- **Chatbot (optional, query-based, NOT LLM):** _(yes / no — still undecided)_
- **Open items:** deadline not yet filled in; chatbot decision; verify what `spam_review_count` means (Kaggle dataset page) before using it

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
- Git: default branch is `master`. One branch per person (`ml-work`, `app-work`), merge into `master` via pull request. Pull before you start, commit small, push often
- Never commit large/secret files; keep `.env` for the MongoDB URI
- Set `random_state=42` everywhere
- Every notebook starts with a markdown cell: objective, input, output

## 11. Progress (update after each task)
- [x] Phase 0 Setup (project at `A:\DSML\PuneBite`, `.venv`, VS Code, Git, MongoDB server run manually with `mongod`, Compass connects)
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

**Last completed:** Phases 0-4 and 5a (`06_feature_selection_pca.ipynb`)
**Next task:** 13.1 `07_clustering.ipynb`, then 13.2 `08_association_rules.ipynb`. Phase 6 (MongoDB + API, 13.3) can run in parallel because the cleaned CSV and both saved models exist.
**Decisions / notes:**
- Rating 0.0 = placeholder for no reviews (all have 0 votes) -> NaN. 7,669 rated restaurants.
- Votes strongly tied to rating (Spearman ~0.73; <5 votes avg 3.04, 500+ votes avg 4.07). Define `popular` = votes >= 50 (3,012 rows) for robustness checks.
- Stats finding: outdoor_seating / vegetarian_only look significant overall but NOT among popular restaurants (confounded by votes). table_booking_recommended and premium amenities stay significant. Type explains ~8% of rating variance (eta^2 0.076); locality vs rating tier Cramer's V ~0.19.
- Classification (target rating >= 4.0, 11.2% positive): Random Forest best. Scenario A (with votes) test AUC ~0.94, F1 ~0.67. Scenario B (no votes, for Opening Advisor) AUC ~0.82, F1 ~0.50. Saved: `ml/models/high_rating_classifier.joblib` + `_meta.json` (Scenario B, includes feature spec and threshold ~0.5). The API must build inputs with `ml/features.py` `make_features(df, spec)`.
- Regression (target rating): Scenario A R2 ~0.55, RMSE ~0.28; Scenario B (no votes) R2 ~0.28, RMSE ~0.36 (baseline 0.43). Regularisation made little difference (large n, few features); Lasso zeroed 27 of 95 encoded features. Saved: `ml/models/rating_regressor.joblib` + `_meta.json` (Scenario B, Polynomial deg2 + Ridge). Residuals show regression to the mean (over-predicts low, under-predicts high ratings).
- Feature selection (06): 14 consensus features (price, n_amenities, n_cuisines, accepts_cards, table_booking_recommended, full_bar_available, brunch, valet_parking_available, live_music, smoking_are, cuisines desserts/continental/italian, type Quick Bites) saved to `ml/models/selected_features.json`. More features = higher AUC (0.74 @5, 0.77 @20, 0.825 @150), so selection is for interpretation, not accuracy. PCA: 24 comps = 90% of amenity variance; ~50 comps on all features matches raw AUC.
- Modelling caution: votes is a very strong predictor but partly reflects popularity; compare models with and without votes.

## 12. How the finished notebooks were built (keep this style)
- Each notebook starts with a markdown cell: objective, input, output, syllabus link. Ends with a "Summary and findings" cell with real numbers.
- Notebooks live in `notebooks/` and use relative paths (`../data/processed/...`); they add the project root with `sys.path.append(os.path.abspath(".."))` so `from ml import cleaning, features` works. Run them with the `.venv` kernel.
- Reusable logic goes in `ml/*.py`; notebooks call it and explain each step.
- `random_state=42`; stratified splits; selection/scaling inside pipelines (no leakage); report effect sizes, not only p-values.
- Explain results in plain language, state limitations honestly (do not oversell weak results).
- Test every notebook end-to-end on the real data before giving it to the team.
- Metrics for the imbalanced target: F1, precision, recall, ROC-AUC, PR-AUC; never accuracy alone.

## 13. Task specs for the next Claude chat (do in this order; one at a time)
### 13.1 `notebooks/07_clustering.ipynb` (Phase 5b, syllabus Unit VI)
- Data: `restaurants_clean.csv`, rated restaurants with votes > 0.
- K-Means features (standardise): `rating`, `log1p(votes)`, `log(cost_capped)`, `polarization_pct`, `n_amenities`. Choose k with elbow + silhouette (k = 2..10), expected 4-5.
- Profile each cluster (size, means, top types, cuisines, localities) and give each a business name (for example: budget high-volume, premium, hidden gems = high rating but few votes, new/unproven, polarising).
- Compare with hierarchical (Ward, on a sample, with dendrogram), DBSCAN (eps from k-distance plot; noise points = outliers) and a Gaussian Mixture Model (choose components by BIC). Syllabus also lists histograms/density estimation.
- 2D PCA scatter coloured by cluster.
- **No latitude/longitude exists**, so no map-based clustering.
- Save `data/processed/restaurants_clusters.csv` with `url`, `cluster`, `cluster_name` (for the API/dashboard).

### 13.2 `notebooks/08_association_rules.ipynb` (Phase 5c, Unit VI, Lab 8)
- Transactions: (a) cuisines per restaurant (all ~12k restaurants), (b) amenities + restaurant type per restaurant.
- `mlxtend`: `TransactionEncoder`, `apriori(min_support ~0.01-0.02)`, compare with `fpgrowth` (runtime and same itemsets); `association_rules(metric="lift", min_threshold=1.2)`; also filter confidence >= 0.5.
- Explain support, confidence, lift in plain language; top rules by lift with plain-English interpretation; scatter plot support vs confidence coloured by lift.
- Convert frozensets to strings before saving `data/processed/association_rules.csv`.

### 13.3 Phase 6: MongoDB + Flask API (`backend/`)
- `backend/load_data.py`: read `restaurants_clean.csv`; split `cuisines` and `amenities` on `|` into arrays; build `star_pct` object; NaN -> null; merge cluster labels (13.1) and later `trust_rating`; insert into db `punebite`, collection `restaurants`; indexes on locality, rating, cost_capped, cuisines. Build a `localities` collection (count, average rating of rated restaurants, median price, top cuisines).
- `backend/app.py` (Flask + flask-cors, `.env` with `MONGO_URI`, default `mongodb://127.0.0.1:27017`): endpoints in Section 9.
- `POST /api/predict`: build a one-row DataFrame with `locality`, `primary_type`, `cuisines` (pipe string), `cost_capped`, `n_cuisines`, `n_amenities`, `accepts_cards`, `accepts_digital` and 0/1 amenity columns; call `features.make_features(df, meta["feature_spec"], with_votes=False)`; classifier -> `predict_proba[:,1]` compared with `meta["threshold"]`; regressor -> predicted rating. Models: `ml/models/high_rating_classifier.joblib`, `rating_regressor.joblib` (plus `_meta.json`). Use the same scikit-learn version as training (`pip freeze > backend/requirements.txt`).
- Test endpoints with Thunder Client.

### 13.4 Phase 7: React dashboard (`frontend/`, Vite + React + plain CSS)
- Pages: Overview (KPIs and charts), Locality explorer (report card), Restaurant explorer (filters + table), Hidden Gems, Opening Advisor (form -> `/api/predict`), optional chatbot panel.
- Use recharts (or chart.js) for charts; dev proxy to the Flask API.

### 13.5 Phase 8 (optional): trust-adjusted rating and Hidden Gems (`ml/scoring.py`)
- `trust_rating = (v/(v+m))*R + (m/(v+m))*C` with R = rating, v = votes, m = 50 (the "popular" threshold), C = mean rated rating (about 3.44). Justify m with notebook 02 section 7 (ratings with few votes are unstable).
- Hidden gem = high trust_rating within its locality (for example top 15%) but low visibility (for example 20-200 votes). Sanity-check with examples, add to MongoDB and the API.

### 13.6 Phase 9 (optional): query-based chatbot (not LLM)
- Rule-based parser: cuisine, locality (fuzzy match with `difflib`), "under Rs X", minimum rating, restaurant type, amenities ("outdoor seating"), "hidden gems". Build a MongoDB query, return top 5 by `trust_rating`; friendly fallback with example questions. Explain in the viva why it is rule-based (reliable, explainable, no API cost).

### 13.7 Phase 10: report, PPT, viva
- Report chapters follow the syllabus: Introduction, Data, Cleaning, EDA, Statistics, Classification, Regression, Feature selection/PCA, Clustering, Association rules, System design (MongoDB, API, React), Results, Limitations, Conclusion.
- Likely viva topics: class imbalance and why accuracy fails; the votes confound (outdoor seating effect disappeared once votes >= 50); data leakage (star percentages, selection inside CV); why Random Forest; regression to the mean; why feature selection did not raise accuracy; why no map (no lat/long).

## 14. Environment notes (Windows, PowerShell)
- Project folder: `A:\DSML\PuneBite`. MongoDB server was extracted from a zip (no Windows service), so start it by hand and keep the window open:
  `& "A:\DSML\mongodb-win32-x86_64-windows-9.0.2\bin\mongod.exe" --dbpath "A:\DSML\mongo-data"`
  (or a `start-mongo.bat` with the same line but without the leading `&`). Compass connects to `mongodb://127.0.0.1:27017`.
- Activate the environment: `.venv\Scripts\activate`. If scripts are blocked: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
- In PowerShell a quoted path needs `&` in front of it to run.
- Libraries installed: pandas numpy scikit-learn scipy statsmodels mlxtend matplotlib seaborn jupyter ipykernel flask pymongo joblib. Still to install when needed: `flask-cors`, `python-dotenv`, Node.js packages for React.
- Files the previous chat produced (all should be in the repo): `ml/cleaning.py`, `ml/features.py`, notebooks `01`-`06`, `ml/models/*.joblib` and `*_meta.json`, `data/processed/restaurants_clean.csv`.

## 15. Starter prompt for the next Claude chat
Attach these files to the first message: `PROJECT_CONTEXT.md`, `data/processed/restaurants_clean.csv`, `ml/cleaning.py`, `ml/features.py` (and the `_meta.json` files if working on the API). Then send:

> I'm continuing the PuneBite Analyzer mini-project (context file attached). Phases 0-5a are finished and tested. Please do the next task in Section 13 of the file, starting with 13.1 `07_clustering.ipynb`. Follow Section 12 (same style as the finished notebooks), test the code on the attached cleaned CSV, and give me the notebook plus a short summary of the real results. Do one task at a time. When done, tell me exactly what to update in PROJECT_CONTEXT.md.
