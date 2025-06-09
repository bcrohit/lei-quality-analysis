import pandas as pd
import pycountry

def check_completeness(df):
    """Check if required fields are present and not null."""
    required_columns = ["lei", "entity.legalName.name", "entity.legalAddress.country", "registration.initialRegistrationDate", "registration.nextRenewalDate"]
    completeness = df[required_columns].notnull().all(axis=1)
    return completeness

def check_country_validity(df):
    """Check if country codes are valid ISO alpha-2 codes."""
    valid_countries = {c.alpha_2 for c in pycountry.countries}
    return df["entity.legalAddress.country"].apply(lambda x: x in valid_countries)

def check_date_consistency(df):
    """Check if expiration date is after registration date."""
    df["registration.initialRegistrationDate"] = pd.to_datetime(df["registration.initialRegistrationDate"])
    df["registration.nextRenewalDate"] = pd.to_datetime(df["registration.nextRenewalDate"])
    return df["registration.nextRenewalDate"] > df["registration.initialRegistrationDate"]

def check_uniqueness(df):
    return ~df["lei"].duplicated()

def check_if_expired(df):
    return pd.to_datetime(df["registration.nextRenewalDate"]) >= pd.Timestamp.today(tz='utc')


def run_quality_checks(df):
    df["Completeness"] = check_completeness(df)
    df["CountryValid"] = check_country_validity(df)
    df["DateConsistent"] = check_date_consistency(df)
    df["UniqueLEI"] = check_uniqueness(df)
    df["NotExpired"] = check_if_expired(df)
    return df