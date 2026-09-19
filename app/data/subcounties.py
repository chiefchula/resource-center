# app/data/subcounties.py
"""
Kenyan subcounties → wards mapping.

REPLACE the sample content below with your real list.
Format:
    SUBCounty_WARDS = {
        "Subcounty Name": ["Ward 1", "Ward 2", ...],
        ...
    }
"""

SUBCounty_WARDS = {
    "Ganze": [
        "Bamba", "Ganze", "Jaribuni", "Sokoke",
    ],
    "Kaloleni": [
        "Kaloleni", "Kayafungo", "Mariakani", "Mwanamwinga",
    ],
    "Kilifi North": [
        "Dabaso", "Kibarani", "Matsangoni", "Sokoni", "Tezo", "Watamu",
    ],
    "Kilifi South": [
        "Chasimba", "Junju", "Mtepeni", "Mwarakaya", "Shimo La Tewa",
    ],
    "Magarini": [
        "Adu", "Garashi", "Gongoni", "Magarini", "Marafa", "Sabaki",
    ],
    "Malindi": [
        "Ganda", "Jilore", "Kakuyuni", "Malindi Town", "Shella",
    ],
    "Rabai": [
        "Kambe/Ribe", "Mwawesa", "Rabai/Kisurutini", "Ruruma",
    ],
}

# Convenience: sorted list of subcounty names for dropdown population
SUBCounty_NAMES = sorted(SUBCounty_WARDS.keys())