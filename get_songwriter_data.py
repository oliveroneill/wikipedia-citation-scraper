"""Create a dataset of songwriter's wikipedia articles."""
import constants
import main

if __name__ == "__main__":
    for s in constants.LIST_OF_SONGWRITERS:
        print(s)
        print('-' * 80)
        try:
            main.main(s)
        except Exception:
            pass
