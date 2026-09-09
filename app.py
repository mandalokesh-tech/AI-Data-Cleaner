import streamlit as st
import pandas as pd
from io import BytesIO
from cleaner import clean_data


# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="CleanData",
    page_icon="📊",
    layout="wide"
)


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------
st.title("📊 CleanData")
st.subheader("Clean. Validate. Standardize.")

st.write(
    "Turn messy customer and lead spreadsheets into "
    "clean, reliable business data."
)


# ---------------------------------------------------------
# WHAT CLEANDATA DOES
# ---------------------------------------------------------
st.markdown("### What CleanData does")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 🧹 Clean")
    st.write(
        "Remove duplicate records and standardize "
        "names, locations, and other fields."
    )

with col2:
    st.markdown("### 🔍 Validate")
    st.write(
        "Identify invalid emails, phone numbers, "
        "and missing information."
    )

with col3:
    st.markdown("### 📊 Report")
    st.write(
        "Generate a professional Excel report showing "
        "data-quality results and detected issues."
    )


st.divider()


# ---------------------------------------------------------
# FILE UPLOAD
# ---------------------------------------------------------
st.markdown("### Upload your data")

uploaded_file = st.file_uploader(
    "Upload a CSV or Excel file",
    type=["csv", "xlsx"]
)


if uploaded_file is not None:

    # -----------------------------------------------------
    # PREVIEW
    # -----------------------------------------------------
    st.markdown("### Data Preview")

    try:
        uploaded_file.seek(0)

        if uploaded_file.name.lower().endswith(".csv"):
            preview_df = pd.read_csv(uploaded_file)
        else:
            preview_df = pd.read_excel(uploaded_file)

        st.dataframe(
            preview_df.head(10),
            width="stretch"
        )

        st.caption(
            f"Showing first 10 rows of {len(preview_df):,} records."
        )

    except pd.errors.EmptyDataError:
        st.error("The uploaded CSV file is empty.")

    except Exception as e:
        st.error(f"Unable to preview the file: {e}")


    # -----------------------------------------------------
    # CLEAN BUTTON
    # -----------------------------------------------------
    if st.button(
        "🚀 Clean & Validate Data",
        width="stretch"
    ):

        try:
            # Reset file pointer before cleaning
            uploaded_file.seek(0)

            cleaned_df, report = clean_data(uploaded_file)

            st.success("Data cleaning and validation completed successfully!")

            # -------------------------------------------------
            # DETECTED COLUMNS
            # -------------------------------------------------
            st.markdown("### Detected Columns")

            detected_columns = report.get(
                "detected_columns",
                {}
            )

            if detected_columns:

                detected_data = []

                for field, column in detected_columns.items():
                    detected_data.append(
                        {
                            "Field": field,
                            "Detected Column": column
                        }
                    )

                detected_df = pd.DataFrame(detected_data)

                st.dataframe(
                    detected_df,
                    width="stretch",
                    hide_index=True
                )


            # -------------------------------------------------
            # QUALITY METRICS
            # -------------------------------------------------
            st.markdown("### Data Quality")

            metric1, metric2, metric3, metric4 = st.columns(4)

            with metric1:
                st.metric(
                    "Original Records",
                    f"{report['original_records']:,}"
                )

            with metric2:
                st.metric(
                    "Duplicates Removed",
                    f"{report['exact_duplicates_removed']:,}"
                )

            with metric3:
                st.metric(
                    "Missing Values",
                    f"{report['missing_values']:,}"
                )

            with metric4:
                st.metric(
                    "Clean Records",
                    f"{report['cleaned_records']:,}"
                )


            # -------------------------------------------------
            # VALIDATION METRICS
            # -------------------------------------------------
            st.markdown("### Validation Results")

            metric5, metric6, metric7 = st.columns(3)

            with metric5:
                st.metric(
                    "Invalid Emails",
                    f"{report['invalid_emails']:,}"
                )

            with metric6:
                st.metric(
                    "Invalid Phones",
                    f"{report['invalid_phones']:,}"
                )

            with metric7:
                st.metric(
                    "Potential Duplicates",
                    f"{report['potential_duplicates']:,}"
                )


                        # -------------------------------------------------
            # BEFORE / AFTER
            # -------------------------------------------------
            st.markdown("### Before & After")

            st.write(
                "See how CleanData transforms your original data "
                "into a cleaner and more standardized dataset."
            )

            before_col, after_col = st.columns(2)

            with before_col:

                st.markdown("#### 🔴 Before Cleaning")

                uploaded_file.seek(0)

                if uploaded_file.name.lower().endswith(".csv"):
                    before_df = pd.read_csv(uploaded_file)
                else:
                    before_df = pd.read_excel(uploaded_file)

                st.dataframe(
                    before_df.head(10),
                    width="stretch",
                    height=300
                )

            with after_col:

                st.markdown("#### 🟢 After Cleaning")

                st.dataframe(
                    cleaned_df.head(10),
                    width="stretch",
                    height=300
                )


            # -------------------------------------------------
            # COMPLETE CLEANED DATA
            # -------------------------------------------------
            st.markdown("### Complete Cleaned Data")

            st.dataframe(
                cleaned_df,
                width="stretch",
                height=400
            )
            st.markdown("### Validation Issues")

            issues_df = report.get(
                "issues_df",
                pd.DataFrame()
            )

            if not issues_df.empty:

                st.dataframe(
                    issues_df,
                    width="stretch",
                    height=350
                )

            else:

                st.success(
                    "No validation issues were detected."
                )


            # -------------------------------------------------
            # CREATE EXCEL REPORT
            # -------------------------------------------------
            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:

                # Sheet 1
                cleaned_df.to_excel(
                    writer,
                    sheet_name="Cleaned Data",
                    index=False
                )

                # Sheet 2
                if not issues_df.empty:

                    issues_df.to_excel(
                        writer,
                        sheet_name="Validation Issues",
                        index=False
                    )

                else:

                    pd.DataFrame(
                        {
                            "Message": [
                                "No validation issues detected."
                            ]
                        }
                    ).to_excel(
                        writer,
                        sheet_name="Validation Issues",
                        index=False
                    )

                # Sheet 3
                summary_df = pd.DataFrame(
                    {
                        "Metric": [
                            "Original Records",
                            "Clean Records",
                            "Duplicates Removed",
                            "Missing Values",
                            "Invalid Emails",
                            "Invalid Phones",
                            "Potential Duplicates"
                        ],
                        "Value": [
                            report["original_records"],
                            report["cleaned_records"],
                            report["exact_duplicates_removed"],
                            report["missing_values"],
                            report["invalid_emails"],
                            report["invalid_phones"],
                            report["potential_duplicates"]
                        ]
                    }
                )

                summary_df.to_excel(
                    writer,
                    sheet_name="Summary",
                    index=False
                )


            output.seek(0)


            # -------------------------------------------------
            # DOWNLOAD
            # -------------------------------------------------
            st.markdown("### Download Report")

            st.download_button(
                label="⬇️ Download Complete Excel Report",
                data=output,
                file_name="CleanData_Report.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                ),
                width="stretch"
            )


        except Exception as e:

            st.error(
                f"An error occurred while processing the file: {e}"
            )


# ---------------------------------------------------------
# FOOTER / INFORMATION
# ---------------------------------------------------------
st.divider()

st.markdown("### Why use CleanData?")

st.write(
    "CleanData helps businesses save time by automatically "
    "identifying common data-quality problems in customer "
    "and lead spreadsheets."
)

st.info(
    "Demo tip: Upload a messy CSV or Excel file and review "
    "the cleaning results before downloading the report."
)

st.caption(
    "Demo environment — do not upload confidential or sensitive data."
)