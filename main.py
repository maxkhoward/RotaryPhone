#!/usr/bin/env python3

from phone import Phone

if __name__ == "__main__":
    phone = Phone.get_instance()
    print("Ready")
    while True:
        try:
            # Wait for phone to be picked up
            phone.wait_until_answered()
            # Dial a number
            phone.process_dial()
        except Exception as e:
            print(e)
        finally:
            phone.clear_event()
