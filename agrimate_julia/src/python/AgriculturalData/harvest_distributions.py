import numpy as np
from math import pi


def gaussian_harvest_distribution(start_day, end_day, duration_in_sigmas=3.3, total_duration_in_sigmas=None):
    # If end day is earlier in the calendar, consider it as belonging to the next year
    if end_day < start_day:
        end_day += 365

    duration = end_day - start_day + 1
    sigma = duration / duration_in_sigmas

    # Harvest period can extend to the previous or the next year.
    # Hence, consider 3 year period with harvest middle day in the second year.
    days = np.arange(1, 3 * 365 + 1)
    start_day += 365
    end_day += 365
    mid_day = (start_day + end_day) / 2
    distribution = np.exp(-(days - mid_day)**2 / (2 * sigma**2))

    # Assume non-zero harvests only in the period of length total_duration_in_sigmas * sigma
    if total_duration_in_sigmas is not None:
        extension_length = int(round((total_duration_in_sigmas * sigma - duration) / 2))
        distribution[(days < start_day - extension_length) | (days > end_day + extension_length)] = 0

    # Fold it back onto one calendar year
    distribution = sum(distribution[i*365:(i+1)*365] for i in range(3))

    # Normalize
    distribution = distribution / sum(distribution)

    return distribution

def semicircle_harvest_distribution(start_day, end_day, duration_in_R=1.6):
    # If end day is earlier in the calendar, consider it as belonging to the next year
    if end_day < start_day:
        end_day += 365

    duration = end_day - start_day + 1
    R = duration / duration_in_R

    # Harvest period can extend to the previous or the next year.
    # Hence, consider 3 year period with harvest middle day in the second year.
    days = np.arange(1, 3 * 365 + 1)
    start_day += 365
    end_day += 365
    mid_day = (start_day + end_day) / 2
    distribution = np.zeros(days.shape)
    args = R**2 - (days - mid_day)**2
    distribution[args >= 0] = np.sqrt(args[args >=0])

    # Fold it back onto one calendar year
    distribution = sum(distribution[i*365:(i+1)*365] for i in range(3))

    # Normalize
    distribution = distribution / sum(distribution)

    return distribution

def raised_cosine_harvest_distribution(start_day, end_day, duration_in_s=1.2):
    # If end day is earlier in the calendar, consider it as belonging to the next year
    if end_day < start_day:
        end_day += 365

    duration = end_day - start_day + 1
    s = duration / duration_in_s

    # Harvest period can extend to the previous or the next year.
    # Hence, consider 3 year period with harvest middle day in the second year.
    days = np.arange(1, 3 * 365 + 1)
    start_day += 365
    end_day += 365
    mid_day = (start_day + end_day) / 2
    distribution = np.zeros(days.shape)
    support = np.abs(days - mid_day) <= s
    distribution[support] = (1 + np.cos((days - mid_day) / s * pi))[support]

    # Fold it back onto one calendar year
    distribution = sum(distribution[i*365:(i+1)*365] for i in range(3))

    # Normalize
    distribution = distribution / sum(distribution)

    return distribution