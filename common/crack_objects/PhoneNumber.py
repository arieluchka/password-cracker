import re
from typing import TypeVar, Tuple
from pydantic import BaseModel

C = TypeVar("C",bound="PhoneNumberValidator")


class PhoneNumberValidator(BaseModel): #todo: figure out why i need to write the key-argument "phone_number"
    phone_number: str

    @classmethod
    def is_valid(cls, phone_number: str) -> bool:
        PHONE_NUMBER_PATTERN = re.compile(r"^05\d-\d{7}$|^05\d\d{7}$")
        return bool(PHONE_NUMBER_PATTERN.match(phone_number))

    def model_post_init(self, __context) -> None:
        if '-' not in self.phone_number and len(self.phone_number) == 10:
            self.phone_number = f"{self.phone_number[:3]}-{self.phone_number[3:]}"

        if not self.is_valid(self.phone_number):
            raise ValueError(f"Invalid phone number format: {self.phone_number}")

    def __str__(self):
        return self.phone_number

    @classmethod
    def range(cls, start: C, end: C):
        start_num = int(start.phone_number.replace('-', ''))
        end_num = int(end.phone_number.replace('-', ''))
        
        if start_num > end_num:
            start_num, end_num = end_num, start_num
        
        for num in range(start_num, end_num + 1):
            num_str = "0" + str(num)
            if num_str.startswith('05') and len(num_str) == 10: # todo: how can we save on ifs
                yield f"{num_str[:3]}-{num_str[3:]}"
            else: # went beyond 059? break the range?
                break

    @classmethod
    def split_to_sub_ranges(cls, start: C, end: C, sub_ranges_size: int) -> Tuple[C, C]:
        start_num = int(start.phone_number.replace('-', ''))
        end_num = int(end.phone_number.replace('-', ''))

        if start_num > end_num:
            start_num, end_num = end_num, start_num

        sub_start_num = start_num
        while (sub_start_num + sub_ranges_size) < end_num:
            sub_end_num = sub_start_num + (sub_ranges_size - 1)
            yield (PhoneNumberValidator(phone_number="0" + str(sub_start_num)),
                   PhoneNumberValidator(phone_number="0" + str(sub_end_num)))
            sub_start_num += sub_ranges_size

        if start_num < end_num:
            yield (PhoneNumberValidator(phone_number="0" + str(sub_start_num)),
                   PhoneNumberValidator(phone_number="0" + str(end_num)))


if __name__ == '__main__':
    phone1 = PhoneNumberValidator(phone_number="050-9900000")
    phone2 = PhoneNumberValidator(phone_number="051-1000300")

    for phones in PhoneNumberValidator.split_to_sub_ranges(phone2, phone1, 10000):
        print(f"{phones[0]}, {phones[1]}")