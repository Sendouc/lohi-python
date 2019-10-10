class VotedPlayer:
    def __init__(self, name: str, na: bool, id: int, suggested: bool = False):
        self.name = name
        self.id = id
        # True if the user was suggested (in other words False means the player was in the server at the time of the
        # voting.
        self.suggested = suggested
        # Vote count i.e. how many +2, +1 etc. the player got in the voting.
        # 0 index = EU - 1 index = NA
        self.plustwo = [0, 0]
        self.plusone = [0, 0]
        self.minustwo = [0, 0]
        self.minusone = [0, 0]
        # How many votes there were
        self.count = [0, 0]
        self.na = na

    def __gt__(self, player2):
        return self.vote_sum() > player2.vote_sum()

    def __str__(self):
        return (
            f"**{self.name}**\n`{sum(self.minustwo)}/{sum(self.minusone)}/{sum(self.plusone)}/{sum(self.plustwo)}`\n"
            f"__{self.get_vote_ratio()}__ (NA: {self.get_regional_vote_ratio(True)} EU: {self.get_regional_vote_ratio(False)})"
        )

    def add_vote(self, vote: int, na: bool) -> None:
        index = int(na)
        # If the voter is from the opposite region we half their vote
        if self.na != na and (vote == 2 or vote == -2):
            vote /= 2

        if vote == 2:
            self.plustwo[index] += 1
        elif vote == 1:
            self.plusone[index] += 1
        elif vote == -1:
            self.minusone[index] += 1
        elif vote == -2:
            self.minustwo[index] += 1
        else:
            raise ValueError(f"Expected -2, -1, 1 or 2. Got: {vote}")

        self.count[index] += 1

    def get_vote_ratio(self) -> str:
        vote_ratio = float(self.get_regional_vote_ratio(True)) + float(
            self.get_regional_vote_ratio(False)
        )
        return "%+.2f" % round(vote_ratio, 2)

    def get_regional_vote_ratio(self, na: bool) -> str:
        vote_ratio = self.regional_sum(na) / self.regional_total(na)
        return "%+.2f" % round(vote_ratio, 2)

    def vote_sum(self):
        return (
            (sum(self.plustwo) * 2)
            + (sum(self.plusone) * 1)
            + (sum(self.minustwo) * -2)
            + (sum(self.minusone) * -1)
        )

    def regional_sum(self, na: bool):
        index = int(na)
        return (
            (self.plustwo[index] * 2)
            + (self.plusone[index] * 1)
            + (self.minustwo[index] * -2)
            + (self.minusone[index] * -1)
        )

    def votes_total(self):
        return sum(self.count)

    def regional_total(self, na: bool):
        index = int(na)
        return self.count[index]
