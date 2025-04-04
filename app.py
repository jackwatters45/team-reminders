import streamlit as st
import polars as pl
import os
from io import BytesIO  # Needed for reading uploaded file bytes with Polars
from typing import Mapping, Type, Union  # For type hinting schema

# --- Page Configuration ---
st.set_page_config(page_title="Team Reminder Sender", layout="wide")

st.title("⚙️ Team Reminder Configuration")
st.caption("Configure settings, schedule, and recipients for your Twilio reminders.")

# --- Placeholder Data/State ---
# In a real app, this would load from .env, settings.py, or a database
if "settings" not in st.session_state:
    st.session_state.settings = {
        "twilio_account_sid": "ACxxxxxxx (Loaded from .env)",  # Placeholder
        "twilio_auth_token": "********",  # Placeholder
        "twilio_phone_number": "+14155490279 (Loaded from .env)",  # Placeholder
    }

if "schedule" not in st.session_state:
    st.session_state.schedule = {
        "type": "End of Month",
        "days_before_end": 3,  # Example: Send 3 days before month end
    }

# --- Define Schema for Recipients DataFrame ---
# Ensures consistent column types
# Define the type hint more explicitly for the linter
PolarsDataType = Union[Type[pl.DataType], pl.DataType]
RecipientsSchemaType = Mapping[str, PolarsDataType]
recipients_schema: RecipientsSchemaType = {
    "Name": pl.Utf8,
    "PhoneNumber": pl.Utf8,
    "SendFlag": pl.Boolean,
}

if "recipients_df" not in st.session_state:
    # Try to load existing CSV, otherwise use empty DataFrame
    default_csv = "August Rent - Sheet1.csv"
    try:
        if os.path.exists(default_csv):
            # Read CSV using Polars, infer schema length 0 reads all as Utf8 initially
            # This makes column mapping/checking more robust before casting
            temp_df = pl.read_csv(default_csv, has_header=True, infer_schema_length=0)

            # --- Flexible Column Mapping (Case-Insensitive) ---
            name_cols = ["Name", "Tenant", "Contact"]
            phone_cols = ["PhoneNumber", "Phone", "Mobile"]
            # Map potential flag column names (lowercase) to interpretation (True means send)
            send_cols_map = {
                "sendflag": True,
                "send?": True,
                "active": True,  # Flags where True means send
                "paid": False,
                "false": False,  # Flags where False means send (e.g., 'FALSE' means not paid)
            }

            mapped_cols = {}
            found_name, found_phone = False, False
            send_col_source = None  # Store the original column name used for the flag
            send_flag_interpretation = (
                True  # Default: True in source means SendFlag=True
            )

            # Find best match for Name and Phone (case-insensitive)
            for col in temp_df.columns:
                col_lower = col.lower()
                if not found_name and any(c.lower() == col_lower for c in name_cols):
                    mapped_cols[col] = "Name"
                    found_name = True
                elif not found_phone and any(
                    c.lower() == col_lower for c in phone_cols
                ):
                    mapped_cols[col] = "PhoneNumber"
                    found_phone = True

            # Find best match for Send Flag (case-insensitive)
            for col in (
                temp_df.columns
            ):  # Corrected loop variable from temp_cols to temp_df.columns
                col_lower = col.lower()
                if col not in mapped_cols:  # Don't reuse Name/Phone col
                    if col_lower in send_cols_map:
                        send_col_source = col
                        send_flag_interpretation = send_cols_map[col_lower]
                        break  # Found the first matching flag

            if found_name and found_phone:
                # Rename based on found columns. Linter might still warn here due to dynamic nature.
                selected_df = temp_df.rename(mapped_cols)  # type: ignore

                # Convert SendFlagSource to boolean SendFlag based on interpretation
                if send_col_source:
                    # Standardize based on interpretation (True means send)
                    if (
                        send_flag_interpretation
                    ):  # True/Truthy in source means True (send)
                        selected_df = selected_df.with_columns(
                            pl.when(
                                pl.col(send_col_source)
                                .str.to_lowercase()
                                .is_in(["true", "1", "yes", "y"])
                            )
                            .then(pl.lit(True))
                            .otherwise(
                                pl.lit(False)
                            )  # Assume anything else means don't send
                            .alias("SendFlag")
                        )
                    else:  # False/Falsy in source means True (send)
                        selected_df = selected_df.with_columns(
                            pl.when(
                                pl.col(send_col_source)
                                .str.to_lowercase()
                                .is_in(["false", "0", "no", "n"])
                            )
                            .then(pl.lit(True))
                            .otherwise(
                                pl.lit(False)
                            )  # Assume anything else means don't send
                            .alias("SendFlag")
                        )
                    # Drop the original source column if it's different from 'SendFlag' and exists
                    if (
                        send_col_source != "SendFlag"
                        and send_col_source in selected_df.columns
                    ):
                        selected_df = selected_df.drop(send_col_source)
                    selected_columns = ["Name", "PhoneNumber", "SendFlag"]
                else:
                    # If no send flag column found, default to True
                    st.warning(
                        f"No recognizable send flag column found in {default_csv}. Defaulting SendFlag to True for all rows."
                    )
                    selected_df = selected_df.with_columns(
                        pl.lit(True).alias("SendFlag")
                    )
                    selected_columns = ["Name", "PhoneNumber", "SendFlag"]

                # Select final columns and cast to the correct schema
                # Use strict=False to allow casting even if some columns were missing initially
                # (though Name/Phone are checked above, SendFlag might default)
                st.session_state.recipients_df = selected_df.select(
                    selected_columns
                ).cast(recipients_schema, strict=False)  # type: ignore

            else:
                missing: list[str] = []
                if not found_name:
                    missing.append("'Name' (or similar)")
                if not found_phone:
                    missing.append("'PhoneNumber' (or similar)")
                st.warning(
                    f"Could not find required column(s): {', '.join(missing)} in {default_csv}. Starting empty."
                )
                st.session_state.recipients_df = pl.DataFrame(schema=recipients_schema)
        else:
            st.info(f"{default_csv} not found. Starting with empty recipient list.")
            st.session_state.recipients_df = pl.DataFrame(schema=recipients_schema)
    except Exception as e:
        st.error(
            f"Error reading or processing {default_csv}: {e}. Please check the file format. Starting with empty table."
        )
        st.session_state.recipients_df = pl.DataFrame(schema=recipients_schema)


# --- UI Sections ---
tab_settings, tab_schedule, tab_recipients = st.tabs(
    ["🔑 Settings", "🗓️ Schedule", "👥 Recipients"]
)

with tab_settings:
    st.header("Twilio Credentials")
    st.markdown(
        "_(These are typically loaded from your `.env` file. Editing here is for demonstration.)_"
    )

    # Display current settings (read-only for now) - Added keys for stability
    st.text_input(
        "Twilio Account SID",
        value=st.session_state.settings["twilio_account_sid"],
        disabled=True,
        key="disp_sid",
    )
    st.text_input(
        "Twilio Auth Token",
        value=st.session_state.settings["twilio_auth_token"],
        type="password",
        disabled=True,
        key="disp_token",
    )
    st.text_input(
        "Twilio Phone Number (From)",
        value=st.session_state.settings["twilio_phone_number"],
        disabled=True,
        key="disp_num",
    )

    st.info(
        "💡 In a future step, we can add functionality to update the `.env` file securely.",
        icon="ℹ️",
    )


with tab_schedule:
    st.header("When to Send Reminders")

    # Determine index safely
    schedule_options = ["End of Month", "Specific Day of Month", "Manual Trigger Only"]
    # Ensure the value retrieved is treated as a string for index lookup
    current_schedule_type = str(
        st.session_state.schedule.get("type", "Manual Trigger Only")
    )
    try:
        schedule_index = schedule_options.index(current_schedule_type)
    except ValueError:
        schedule_index = schedule_options.index(
            "Manual Trigger Only"
        )  # Default if invalid value in state

    schedule_type = st.selectbox(
        "Schedule Type",
        options=schedule_options,
        index=schedule_index,
        key="schedule_type_select",
    )

    if schedule_type == "End of Month":
        # Ensure value from session state is treated as int
        current_days_before = int(st.session_state.schedule.get("days_before_end", 3))
        days_before = st.number_input(
            "Days Before Month End to Send",
            min_value=0,
            max_value=10,  # Kept max at 10 for sanity
            value=current_days_before,
            step=1,  # Ensure integer steps
            key="days_before_input",
            help="How many days before the *last* day of the month should reminders be sent? (0 = last day)",
        )
        st.session_state.schedule["type"] = "End of Month"
        # Ensure value stored back is also int
        st.session_state.schedule["days_before_end"] = int(days_before)
        # Linter might still complain about st.write, safe to ignore
        st.write(  # type: ignore
            f"Reminders will be scheduled to send {int(days_before)} days before the end of each month."
        )

    elif schedule_type == "Specific Day of Month":
        # Ensure value from session state is treated as int
        current_day_of_month = int(st.session_state.schedule.get("day_of_month", 1))
        day_of_month = st.number_input(
            "Day of Month to Send",
            min_value=1,
            max_value=31,
            value=current_day_of_month,
            step=1,  # Ensure integer steps
            key="day_of_month_input",
            help="Which day of the month should reminders be sent?",
        )
        st.session_state.schedule["type"] = "Specific Day"
        # Ensure value stored back is also int
        st.session_state.schedule["day_of_month"] = int(day_of_month)
        st.write(  # type: ignore
            f"Reminders will be scheduled to send on day {int(day_of_month)} of each month."
        )

    else:  # Manual Trigger Only
        st.session_state.schedule["type"] = "Manual"
        st.write("Reminders will only be sent when manually triggered.")  # type: ignore

    st.button(
        "Send Test Message Now", disabled=True, key="test_send_button"
    )  # Placeholder for future functionality
    st.info(
        "💡 Actual scheduling logic (e.g., using a task scheduler) needs to be implemented separately.",
        icon="ℹ️",
    )


with tab_recipients:
    st.header("Manage Recipients")

    upload_option = st.radio(
        "Recipient Source",
        ["Use Existing/Edited List Below", "Upload New CSV"],
        horizontal=True,
        key="upload_option_radio",
    )

    if upload_option == "Upload New CSV":
        uploaded_file = st.file_uploader(
            "Choose a CSV file", type="csv", key="csv_uploader"
        )
        if uploaded_file is not None:
            try:
                # Read uploaded CSV into Polars DataFrame from buffer
                # Wrap in BytesIO for compatibility
                file_buffer = BytesIO(uploaded_file.getvalue())
                # Read all as string initially
                new_df = pl.read_csv(
                    file_buffer, has_header=True, infer_schema_length=0
                )

                # --- Reuse Column Mapping Logic (Case-Insensitive) ---
                name_cols = ["Name", "Tenant", "Contact"]
                phone_cols = ["PhoneNumber", "Phone", "Mobile"]
                send_cols_map = {
                    "sendflag": True,
                    "send?": True,
                    "active": True,
                    "paid": False,
                    "false": False,
                }

                mapped_cols = {}
                found_name, found_phone = False, False
                send_col_source = None
                send_flag_interpretation = True

                for col in new_df.columns:
                    col_lower = col.lower()
                    if not found_name and any(
                        c.lower() == col_lower for c in name_cols
                    ):
                        mapped_cols[col] = "Name"
                        found_name = True
                    elif not found_phone and any(
                        c.lower() == col_lower for c in phone_cols
                    ):
                        mapped_cols[col] = "PhoneNumber"
                        found_phone = True

                for col in new_df.columns:
                    col_lower = col.lower()
                    if col not in mapped_cols:
                        if col_lower in send_cols_map:
                            send_col_source = col
                            send_flag_interpretation = send_cols_map[col_lower]
                            break
                # --- End Reuse ---

                if found_name and found_phone:
                    selected_df = new_df.rename(mapped_cols)  # type: ignore

                    if send_col_source:
                        if send_flag_interpretation:  # True in source means send
                            selected_df = selected_df.with_columns(
                                pl.when(
                                    pl.col(send_col_source)
                                    .str.to_lowercase()
                                    .is_in(["true", "1", "yes", "y"])
                                )
                                .then(pl.lit(True))
                                .otherwise(pl.lit(False))
                                .alias("SendFlag")
                            )
                        else:  # False in source means send
                            selected_df = selected_df.with_columns(
                                pl.when(
                                    pl.col(send_col_source)
                                    .str.to_lowercase()
                                    .is_in(["false", "0", "no", "n"])
                                )
                                .then(pl.lit(True))
                                .otherwise(pl.lit(False))
                                .alias("SendFlag")
                            )
                        if (
                            send_col_source != "SendFlag"
                            and send_col_source in selected_df.columns
                        ):
                            selected_df = selected_df.drop(send_col_source)
                        selected_columns = ["Name", "PhoneNumber", "SendFlag"]
                    else:
                        st.warning(
                            "No recognizable send flag column found in uploaded CSV. Defaulting SendFlag to True."
                        )
                        selected_df = selected_df.with_columns(
                            pl.lit(True).alias("SendFlag")
                        )
                        selected_columns = ["Name", "PhoneNumber", "SendFlag"]

                    # Select and cast to the target schema
                    st.session_state.recipients_df = selected_df.select(
                        selected_columns
                    ).cast(recipients_schema, strict=False)  # type: ignore
                    st.success("CSV uploaded and processed successfully!")
                else:
                    missing = []
                    if not found_name:
                        missing.append("'Name' (or similar)")
                    if not found_phone:
                        missing.append("'PhoneNumber' (or similar)")
                    st.error(
                        f"Uploaded CSV must contain columns for: {', '.join(missing)}."
                    )

            except Exception as e:
                st.error(f"Error processing uploaded file: {e}")

    st.markdown("**Current Recipient List**")
    st.caption(
        "Edit names, phone numbers, and whether to send messages ('Send?'). Add or remove rows as needed."
    )

    # Use st.data_editor for interactive editing
    # Add a key to the data_editor for better state management
    edited_df = st.data_editor(
        st.session_state.get(
            "recipients_df", pl.DataFrame(schema=recipients_schema)
        ),  # Default to empty DF if not in state
        num_rows="dynamic",
        key="recipient_editor",  # Add key for stability
        column_config={
            "SendFlag": st.column_config.CheckboxColumn(
                "Send?",  # Label for the checkbox column
                help="Check this box to include this recipient in the next reminder send.",
                default=True,
            ),
            "PhoneNumber": st.column_config.TextColumn(
                "Phone Number",
                help="Enter the phone number ideally in E.164 format (e.g., +14155552671)",
                # Basic E.164 format regex validation - allows flexibility but guides user
                # Making it optional for cases where validation is too strict initially
                # validate="^\+[1-9]\d{1,14}$",
            ),
        },
        use_container_width=True,
    )

    # Update session state with edits. Check if the returned object is a Polars DataFrame.
    # st.data_editor might return pandas or potentially other types depending on interaction.
    if edited_df is not None:
        if not isinstance(edited_df, pl.DataFrame):
            # Attempt conversion if it's not Polars (likely Pandas)
            try:
                # Check if it looks like a pandas DataFrame before converting
                if hasattr(edited_df, "to_dict"):
                    st.session_state.recipients_df = pl.from_pandas(edited_df)
                    # Recast after conversion to ensure types, handle potential errors
                    st.session_state.recipients_df = (
                        st.session_state.recipients_df.cast(  # type: ignore
                            recipients_schema, strict=False
                        )
                    )
                else:
                    # If it's not Polars and not Pandas-like, log a warning.
                    st.warning(
                        "Data editor returned an unexpected format. Changes might not be saved correctly."
                    )
                    # Avoid overwriting state with unknown type
            except ImportError:
                st.error(
                    "Pandas is required for converting edited data back to Polars, but it's not installed."
                )
            except Exception as e:
                st.error(f"Error updating table after edits: {e}")
        else:
            # It's already a Polars DataFrame
            st.session_state.recipients_df = edited_df
            # Still good practice to ensure schema after editing
            st.session_state.recipients_df = st.session_state.recipients_df.cast(  # type: ignore
                recipients_schema,  # type: ignore
                strict=False,
            )

    if st.button("Save Recipients to CSV", key="save_csv_button"):
        # Ensure we have a Polars DataFrame before saving
        current_df = st.session_state.get("recipients_df")
        save_path = "August Rent - Sheet1.csv"  # Define path before try block
        if isinstance(current_df, pl.DataFrame) and not current_df.is_empty():
            try:
                current_df.write_csv(save_path)
                st.success(f"Recipient data saved to `{save_path}`.")
            except Exception as e:
                st.error(f"Failed to save CSV to `{save_path}`: {e}")
        elif isinstance(current_df, pl.DataFrame) and current_df.is_empty():
            st.warning("Recipient list is empty. Nothing to save.")
        else:
            st.warning("No valid recipient data found in session state to save.")

    st.info(
        "💡 Connecting this list to the actual message sending logic is the next step.",
        icon="ℹ️",
    )


# --- Footer or Status Bar (Optional) ---
st.sidebar.title("Actions")
st.sidebar.markdown("--- ")
st.sidebar.button(
    "Trigger Manual Send (All Marked Recipients)",
    disabled=True,
    key="manual_send_button",
)  # Placeholder

# Display current state for debugging (optional)
# with st.expander("Current State (Debug)"):
#     st.write("Settings:", st.session_state.settings)
#     st.write("Schedule:", st.session_state.schedule)
#     # Use st.dataframe for Polars display in Streamlit >= 1.26.0
#     # Use st.write(df.to_pandas()) for older versions if needed
#     current_df_debug = st.session_state.get("recipients_df")
#     if isinstance(current_df_debug, pl.DataFrame):
#         st.dataframe(current_df_debug)
#     else:
#         st.write("Recipients Data (Not a Polars DF):", current_df_debug)
