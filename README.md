# Data-Cleaning-and-Preprocessing-Pipeline-Development
Beauty & Wellness Analytics

A Python-based data cleaning and preprocessing project developed as part of the Data Science with Python Analyst Internship.

This project demonstrates how messy beauty and wellness data can be transformed into a clean, consistent, validated dataset that is ready for analysis and machine learning.

📌 Project Overview

Publicly available beauty and wellness datasets often contain:

Missing ratings, prices, skin types, and review text

Duplicate product listings

Inconsistent brand names such as L'Oréal, Loreal, and LOREAL

Mixed currencies such as INR and USD

Different product-size units such as ml, oz, and g

Invalid ratings outside the 1–5 range

Extreme price values and skewed review counts

Inconsistent date formats

Noisy customer review text

Ingredient naming inconsistencies

This project develops a reproducible preprocessing pipeline to identify and resolve these issues.

The pipeline was tested using a simulated dataset of 1,050 product records with intentionally injected data-quality problems (random seed 42). The results documented in the project are therefore simulated and should not be interpreted as real market statistics.

🎯 Objectives

The main objectives are to:

Profile raw beauty and wellness data.

Identify missing, duplicate, invalid, and inconsistent records.

Standardize text, prices, sizes, categories, ingredients, and dates.

Remove duplicate product listings.

Handle missing and invalid values using justified methods.

Detect and treat outliers.

Normalize numerical features.

Encode categorical variables.

Validate the cleaned dataset automatically.

Maintain a reproducible cleaning log and documentation.

🔄 Data Preprocessing Pipeline

The overall workflow is:

Raw Dataset
     ↓
Data Profiling
     ↓
Format & Text Standardization
     ↓
Duplicate Removal
     ↓
Invalid Value Detection
     ↓
Missing Value Handling
     ↓
Outlier Detection & Treatment
     ↓
Normalization & Encoding
     ↓
Automated Validation
     ↓
Clean Dataset
     ↓
Analysis / Machine Learning

Each stage is performed in a fixed order because earlier transformations can affect later operations. For example, standardizing brand names before deduplication helps identify near-duplicate products.

🧹 Cleaning Methods

1. Data Profiling

The raw dataset is examined for:

Number of rows and columns

Data types

Missing-value percentages

Duplicate records

Unique categorical labels

Summary statistics

The original raw data is preserved and never overwritten.

2. Text and Format Standardization

Examples:

Brand names are normalized and mapped to canonical names.

Currency symbols and commas are removed from prices.

Prices are converted to INR.

Product sizes are converted to a common unit.

Category and skin-type labels are standardized.

Ingredient names are normalized.

HTML and unnecessary characters are removed from reviews.

Dates are converted to a common datetime format.

3. Duplicate Removal

Duplicate product IDs are removed after standardization.

This is important because standardization can reveal duplicates that would otherwise appear different.

4. Missing Values

Different columns use different strategies:

Column

Method

Rating

Category-wise median

Price

Category-wise median

Size

Overall median

Skin Type

Unspecified

Review Text

Empty string + missing flag

Missing-value indicator columns are also created where useful so that the original missingness is not hidden.

5. Outlier Treatment

Price values are highly skewed, so the pipeline uses:

log1p() transformation

IQR-based detection

Category-wise thresholds

Winsorization/capping instead of blindly deleting records

Outlier flag columns

A high price is not automatically considered an error because premium beauty products can legitimately be expensive.

6. Normalization and Encoding

The project uses:

Min-Max Scaling for selected numerical features

Z-score Standardization for ratings

One-hot Encoding for categorical variables

These transformations make the data more suitable for machine learning algorithms.

🛠️ Technologies and Libraries

Tool / Library

Purpose

Python

Main programming language

pandas

Data loading, cleaning, transformation, grouping

NumPy

Numerical operations and transformations

scikit-learn

Scaling and encoding

re

Regular expressions and text cleaning

difflib / RapidFuzz

Brand-name matching

unicodedata

Accent normalization

Matplotlib

Data visualization

Seaborn

Exploratory visual checks

Jupyter Notebook

Interactive analysis

Git

Version control

GitHub

Project hosting and reproducibility

📊 Dataset Schema

The simulated dataset represents skincare product listings and customer review information.

Important fields include:

product_id

brand

category

price

size

rating

review_count

skin_type

ingredients

review_text

review_date

Additional columns are generated during preprocessing, including missing-value flags, outlier flags, scaled features, and encoded categorical variables.

📈 Results

The pipeline was executed on the simulated dataset.

Measure

Before Cleaning

After Cleaning

Rows

1,050

1,000

Duplicate Product IDs

50

0

Brand Spellings

32

6

Skin-Type Labels

10

5

Ratings Outside 1–5

12

0

Price Representation

5 mixed formats/currencies

1 INR numeric column

Size Representation

Mixed ml/oz/g text

Numeric ml column

Date Representation

3 formats

1 datetime format

Price Outliers

Maximum ₹37,411

24 flagged; maximum capped at ₹2,484

Validation

Not applicable

All checks passed

Note: These results come from the simulated dataset used for this internship task. They are not real beauty-market statistics.

🧪 Validation

Automated validation checks are used before the cleaned dataset is accepted.

Examples:

assert df["product_id"].is_unique
assert df["rating"].between(1, 5).all()
assert (df["price_inr"] > 0).all()

Validation ensures that incorrect data does not silently continue into analysis or modeling.

📁 Recommended GitHub Project Structure

week3-data-cleaning-preprocessing/
│
├── README.md
├── beauty_cleaning_pipeline.py
├── beauty_raw.csv
├── beauty_clean.csv
├── cleaning_log.json
├── requirements.txt
│
├── notebooks/
│   └── exploratory_analysis.ipynb
│
├── reports/
│   └── Week3_Data_Cleaning_Preprocessing.docx
│
└── tests/
    └── test_pipeline.py

▶️ How to Run

1. Clone the repository

git clone <YOUR_GITHUB_REPOSITORY_URL>
cd week3-data-cleaning-preprocessing

2. Install dependencies

pip install pandas numpy scikit-learn matplotlib seaborn

Or, if a requirements.txt file is included:

pip install -r requirements.txt

3. Run the pipeline

python beauty_cleaning_pipeline.py

The pipeline processes the raw data and generates the cleaned dataset and cleaning log.

🔁 Reproducibility

The project follows reproducible data-engineering practices:

Raw data is preserved.

Cleaning operations are modular.

A fixed random seed (42) is used for simulation.

Cleaning decisions are documented.

A cleaning log records changes.

Data assumptions are explicitly documented.

Validation checks stop the pipeline when rules fail.

Git/GitHub is used for version control.

💡 Beauty & Wellness Specific Solutions

This project includes domain-specific approaches such as:

Category-wise Imputation

Different product categories have different price ranges. Therefore, category-wise medians are preferred over one global median.

Ingredient Synonym Mapping

Ingredient names such as Ascorbic Acid and Vitamin C can be mapped to a common representation.

Cost per ml

After standardizing price and size, cost-per-ml can be calculated for fair comparison across different package sizes.

Review Quality Checks

Repeated or promotional reviews can be flagged as potential spam before sentiment analysis.

Missing Skin Type

Unknown skin type is represented as Unspecified instead of guessing the customer's skin type.

📌 How Clean Data Supports Future Analysis

The cleaned dataset can support:

Trend analysis

Product comparison

Customer segmentation

Recommendation systems

Sentiment analysis

Price analysis

Product-demand analysis

Machine learning models

For example, standardized ingredients and skin types can improve product similarity and recommendation models.

🔐 Ethics and Privacy

The project follows responsible data-handling principles:

Personal identifiers should be removed or anonymized.

Public data should only be collected according to applicable terms of use.

Sensitive wellness-related information should be analyzed in aggregate.

Data should not be used to identify individual users.

The project uses simulated data for demonstration.

⚠️ Limitations

The current results are based on simulated data.

Real datasets may contain additional quality problems.

Median imputation is a simple baseline and can be compared with KNN or iterative imputation.

Fuzzy brand matching can be improved using a larger canonical brand database.

Multilingual reviews require proper language detection and translation.

Ingredient normalization can be improved using official INCI naming.

Tools such as Great Expectations or Pandera can provide additional data validation.

🚀 Future Improvements

Future versions can include:

Automated data ingestion from approved public datasets or APIs.

Scheduled preprocessing pipelines.

Advanced schema validation with Pandera or Great Expectations.

Multilingual NLP preprocessing.

Official INCI-based ingredient normalization.

Automated data-quality monitoring.

Unit and integration testing.

Docker-based reproducible execution.

CI/CD validation using GitHub Actions.

Integration with downstream machine-learning models.

👩‍💻 Internship Information

Internship: Data Science with Python Analyst Internship
Task: Week 3 – Data Cleaning and Preprocessing Pipeline Development
Domain: Beauty & Wellness Analytics
Student: D Sree Chaitanya
Branch: B.Tech Computer Science & Engineering

📄 Project Documentation

The complete technical explanation, cleaning methodology, pseudo-code, results, flowchart, reproducibility practices, ethics, limitations, and future improvements are documented in the Week 3 internship report.

⭐ Key Takeaway

This project demonstrates how a structured Python preprocessing pipeline can convert messy beauty and wellness data into a clean, validated, reproducible, analysis-ready dataset.

The most important principle is:

Clean data should be transformed systematically, validated automatically, and documented so that the same result can be reproduced.
