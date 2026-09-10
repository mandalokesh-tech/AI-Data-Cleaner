import pandas as pd
import re
from pandas.errors import EmptyDataError


# ==========================================
# TEXT NORMALIZATION
# ==========================================

def normalize_text(value):
    """Normalize text for comparison."""

    if pd.isna(value):
        return ""

    value = str(value).strip().lower()

    value = re.sub(r"\s+", " ", value)

    return value


# ==========================================
# EMAIL VALIDATION
# ==========================================

def validate_email(email):
    """Basic email validation."""

    if pd.isna(email):
        return False

    email = str(email).strip()

    if not email:
        return False

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    return bool(re.match(pattern, email))


# ==========================================
# PHONE VALIDATION
# ==========================================

def validate_phone(phone):
    """Basic phone validation."""

    if pd.isna(phone):
        return False

    phone = str(phone).strip()

    if not phone:
        return False

    digits = re.sub(r"\D", "", phone)

    return 10 <= len(digits) <= 15


# ==========================================
# COLUMN DETECTION
# ==========================================

def standardize_columns(df):
    """Detect common business column names."""

    column_mapping = {}

    aliases = {

        "name": [
            "name",
            "full name",
            "customer name",
            "client name",
            "customer",
            "client",
            "customer_name",
            "full_name"
        ],

        "email": [
            "email",
            "email address",
            "email id",
            "e-mail",
            "e-mail address",
            "contact email",
            "contact_email"
        ],

        "phone": [
            "phone",
            "phone number",
            "mobile",
            "mobile number",
            "contact",
            "contact number",
            "mobile no",
            "phone no",
            "mobile_number",
            "phone_number"
        ],

        "city": [
            "city",
            "location",
            "town",
            "city name",
            "city_name"
        ]
    }

    for original_column in df.columns:

        normalized = (
            str(original_column)
            .strip()
            .lower()
            .replace("_", " ")
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized
        )

        for standard_name, possible_names in aliases.items():

            if normalized in possible_names:

                column_mapping[original_column] = standard_name

                break

    df = df.rename(
        columns=column_mapping
    )

    return df, column_mapping


# ==========================================
# READ FILE
# ==========================================

def read_file(file):

    try:

        file.seek(0)

        if file.name.lower().endswith(".csv"):

            df = pd.read_csv(file)

        elif file.name.lower().endswith(".xlsx"):

            df = pd.read_excel(file)

        else:

            raise ValueError(
                "Only CSV and XLSX files are supported."
            )

    except EmptyDataError:

        raise ValueError(
            "The uploaded file is empty. "
            "Please upload a CSV file containing "
            "column headers and data."
        )

    except pd.errors.ParserError:

        raise ValueError(
            "The CSV file could not be read. "
            "Please check the CSV format."
        )

    except Exception as e:

        raise ValueError(
            f"Unable to read the file: {e}"
        )

    if df.empty:

        raise ValueError(
            "The uploaded file contains no data."
        )

    if len(df.columns) == 0:

        raise ValueError(
            "The uploaded file contains no columns."
        )

    return df


# ==========================================
# MAIN CLEANING FUNCTION
# ==========================================

def clean_data(file):

    # --------------------------------------
    # 1. READ FILE
    # --------------------------------------

    df = read_file(file)

    original_records = len(df)


    # --------------------------------------
    # 2. REMOVE COMPLETELY EMPTY ROWS
    # --------------------------------------

    df = df.dropna(how="all")

    if df.empty:

        raise ValueError(
            "The uploaded file contains only empty rows."
        )


    # --------------------------------------
    # 3. STANDARDIZE COLUMN NAMES
    # --------------------------------------

    df, detected_columns = standardize_columns(df)


    # --------------------------------------
    # 4. CLEAN EMPTY STRINGS
    # --------------------------------------

    for column in df.select_dtypes(
        include="object"
    ).columns:

        df[column] = (
            df[column]
            .apply(
                lambda value:
                value.strip()
                if isinstance(value, str)
                else value
            )
        )

        df[column] = df[column].replace(
            {
                "": pd.NA,
                "none": pd.NA,
                "null": pd.NA,
                "nan": pd.NA
            }
        )


    # --------------------------------------
    # 5. STANDARDIZE NAMES
    # --------------------------------------

    if "name" in df.columns:

        df["name"] = (
            df["name"]
            .apply(
                lambda value:
                value.title()
                if isinstance(value, str)
                else value
            )
        )


    # --------------------------------------
    # 6. STANDARDIZE CITIES
    # --------------------------------------

    if "city" in df.columns:

        city_mapping = {

            "hyd": "Hyderabad",
            "hyderabad": "Hyderabad",

            "blr": "Bengaluru",
            "bangalore": "Bengaluru",
            "bengaluru": "Bengaluru",

            "madras": "Chennai",
            "chennai": "Chennai",

            "bombay": "Mumbai",
            "mumbai": "Mumbai",

            "new delhi": "Delhi",
            "delhi": "Delhi",

            "pune": "Pune"
        }

        df["city"] = (
            df["city"]
            .apply(
                lambda value:
                city_mapping.get(
                    str(value).lower().strip(),
                    value
                )
                if pd.notna(value)
                else value
            )
        )


    # ======================================
    # VALIDATION ISSUES
    # ======================================

    issues = []


    # --------------------------------------
    # 7. MISSING VALUES
    # --------------------------------------

    for index, row in df.iterrows():

        for column in df.columns:

            if pd.isna(row[column]):

                issues.append(
                    {
                        "row": index + 2,
                        "field": column,
                        "issue": "Missing value",
                        "value": ""
                    }
                )


    # --------------------------------------
    # 8. EMAIL VALIDATION
    # --------------------------------------

    invalid_emails = 0

    if "email" in df.columns:

        for index, value in df["email"].items():

            if pd.isna(value):

                continue

            if not validate_email(value):

                invalid_emails += 1

                issues.append(
                    {
                        "row": index + 2,
                        "field": "email",
                        "issue": "Invalid email",
                        "value": str(value)
                    }
                )


    # --------------------------------------
    # 9. PHONE VALIDATION
    # --------------------------------------

    invalid_phones = 0

    if "phone" in df.columns:

        for index, value in df["phone"].items():

            if pd.isna(value):

                continue

            if not validate_phone(value):

                invalid_phones += 1

                issues.append(
                    {
                        "row": index + 2,
                        "field": "phone",
                        "issue": "Invalid phone",
                        "value": str(value)
                    }
                )


    # ======================================
    # 10. EXACT DUPLICATES
    # ======================================

    before_duplicates = len(df)

    duplicate_mask = df.duplicated(
        keep="first"
    )

    duplicate_rows = df[
        duplicate_mask
    ].copy()

    exact_duplicates_removed = (
        before_duplicates - len(df.drop_duplicates())
    )

    for index in duplicate_rows.index:

        issues.append(
            {
                "row": index + 2,
                "field": "record",
                "issue": "Exact duplicate",
                "value": ""
            }
        )


    df = df.drop_duplicates()


    # ======================================
    # 11. POTENTIAL DUPLICATES
    # ======================================

    potential_duplicates = 0

    if "name" in df.columns:

        normalized_names = (
            df["name"]
            .apply(normalize_text)
        )

        duplicate_mask = (
            normalized_names
            .duplicated(keep=False)
            & (normalized_names != "")
        )

        potential_duplicates = int(
            duplicate_mask.sum()
        )

        for index in df[
            duplicate_mask
        ].index:

            issues.append(
                {
                    "row": index + 2,
                    "field": "name",
                    "issue": "Potential duplicate",
                    "value": str(
                        df.loc[index, "name"]
                    )
                }
            )


    # ======================================
    # 12. FINAL RECORD COUNT
    # ======================================

    cleaned_records = len(df)


    # ======================================
    # 13. CREATE ISSUES DATAFRAME
    # ======================================

    if issues:

        issues_df = pd.DataFrame(
            issues,
            columns=[
                "row",
                "field",
                "issue",
                "value"
            ]
        )

    else:

        issues_df = pd.DataFrame(
            columns=[
                "row",
                "field",
                "issue",
                "value"
            ]
        )


    # ======================================
    # 14. REMOVE TECHNICAL VALIDATION
    # COLUMNS FROM CUSTOMER DATA
    # ======================================

    # We intentionally do NOT add
    # email_valid or phone_valid columns
    # to the customer's cleaned dataset.


    # ======================================
    # 15. SUMMARY
    # ======================================

    summary = {

        "original_records":
            original_records,

        "cleaned_records":
            cleaned_records,

        "exact_duplicates_removed":
            exact_duplicates_removed,

        "potential_duplicates":
            potential_duplicates,

        "missing_values":
            int(
                df.isnull().sum().sum()
            ),

        "invalid_emails":
            invalid_emails,

        "invalid_phones":
            invalid_phones
    }


    # ======================================
    # 16. REPORT
    # ======================================

    report = {

        "original_records":
            original_records,

        "exact_duplicates_removed":
            exact_duplicates_removed,

        "potential_duplicates":
            potential_duplicates,

        "missing_values":
            summary["missing_values"],

        "invalid_emails":
            invalid_emails,

        "invalid_phones":
            invalid_phones,

        "cleaned_records":
            cleaned_records,

        "detected_columns":
            detected_columns,

        "issues_df":
            issues_df,

        "summary":
            summary
    }


    return df, report