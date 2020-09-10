import numpy as np


class CorsikaRandomSeed:
    def __init__(self, NUM_DIGITS_RUN_ID=6, NUM_DIGITS_AIRSHOWER_ID=3):

        assert NUM_DIGITS_RUN_ID > 0
        assert NUM_DIGITS_AIRSHOWER_ID > 0

        self.NUM_DIGITS_RUN_ID = NUM_DIGITS_RUN_ID
        self.NUM_DIGITS_AIRSHOWER_ID = NUM_DIGITS_AIRSHOWER_ID

        self.NUM_DIGITS_SEED = (
            self.NUM_DIGITS_RUN_ID + self.NUM_DIGITS_AIRSHOWER_ID
        )
        assert self.NUM_DIGITS_SEED <= 9

        self.NUM_AIRSHOWER_IDS_IN_RUN = 10 ** self.NUM_DIGITS_AIRSHOWER_ID
        self.NUM_RUN_IDS = 10 ** self.NUM_DIGITS_RUN_ID
        self.NUM_SEEDS = self.NUM_AIRSHOWER_IDS_IN_RUN * self.NUM_RUN_IDS
        assert self.NUM_SEEDS < np.iinfo(np.int32).max

        self.SEED_TEMPLATE_STR = "{seed:0" + str(self.NUM_DIGITS_SEED) + "d}"

    def random_seed_based_on(self, run_id, airshower_id):
        assert self.is_valid_run_id(run_id)
        assert self.is_valid_airshower_id(airshower_id)
        return run_id * self.NUM_AIRSHOWER_IDS_IN_RUN + airshower_id

    def run_id_from_seed(self, seed):
        if np.isscalar(seed):
            assert seed <= self.NUM_SEEDS
        else:
            seed = np.array(seed)
            assert (seed <= self.NUM_SEEDS).all()
        return seed // self.NUM_AIRSHOWER_IDS_IN_RUN

    def airshower_id_from_seed(self, seed):
        return (
            seed - self.run_id_from_seed(seed) * self.NUM_AIRSHOWER_IDS_IN_RUN
        )

    def is_valid_run_id(self, run_id):
        if run_id >= 0 and run_id < self.NUM_RUN_IDS:
            return True
        else:
            return False

    def is_valid_airshower_id(self, airshower_id):
        if airshower_id >= 0 and airshower_id < self.NUM_AIRSHOWER_IDS_IN_RUN:
            return True
        else:
            return False

    def __repr__(self):
        out = self.__class__.__name__
        out += "("
        out += "num. digits: run-id " + str(self.NUM_DIGITS_RUN_ID) + ", "
        out += "airshower-id " + str(self.NUM_DIGITS_AIRSHOWER_ID)
        out += ")"
        return out
