from typing import List, Tuple

from common.crack_objects import PhoneNumberValidator


phone_num_range = (
    ("050-0000000", "059-9999999")
)
efficient_phone_num_range = (
    ("050-0000000", "054-9999999"), # COMMON
    ("055-2200000", "055-2799999"),
    ("055-3200000", "055-3399999"),
    ("055-4400000", "055-4499999"),
    ("055-5000000", "055-5199999"),
    ("055-5500000", "055-5599999"),
    ("055-6600000", "055-6899999"),
    ("055-7000000", "055-7299999"),
    ("055-8700000", "055-9999999"),
    ("056-0000000", "056-9999999"),
    ("058-0000000", "058-9999999"),
    ("059-0000000", "059-9999999"),
    ("055-0000000", "055-2199999"), # UNCOMMON
    ("055-2800000", "055-3199999"),
    ("055-3400000", "055-4399999"),
    ("055-4500000", "055-4999999"),
    ("055-5200000", "055-5499999"),
    ("055-5600000", "055-6599999"),
    ("055-6900000", "055-6999999"),
    ("055-7300000", "055-8699999"),
    ("057-0000000", "057-9999999"),
)


# following https://en.wikipedia.org/wiki/Telephone_numbers_in_Israel#:~:text=Bezeq-,Cellular%20and%20mobile%20devices%20area%20code%2005,-Local%20Format
# PROOF IT'S THE FULL RANGE -> https://imgur.com/a/cX4077U
def _ranges_for_jobs_generator(password_ranges: Tuple[Tuple[str, str]], passwords_per_job: int):
    for big_pass_range in password_ranges:
        for job_pass_range in PhoneNumberValidator.split_to_sub_ranges(
            start=PhoneNumberValidator(phone_number=big_pass_range[0]),
            end=PhoneNumberValidator(phone_number=big_pass_range[1]),
            sub_ranges_size=passwords_per_job
        ):
            yield job_pass_range