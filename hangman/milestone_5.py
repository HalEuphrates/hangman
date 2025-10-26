# hangman_datamuse.py
# A playable Hangman game that fetches random words from the Datamuse API,
# with a safe offline fallback list. Paste this file into your repo and run.

import random
import requests
from typing import List, Optional

# ----------------------------
# Datamuse integration
# ----------------------------

def fetch_random_word_from_datamuse(
    min_len: int = 5,
    max_len: int = 8,
    tries: int = 3,
    timeout: float = 10.0,
    max_results: int = 1000,
) -> Optional[str]:
    """
    Fetch a single random word from Datamuse within the given length range.

    Strategy:
    - Pick a random target length between min_len and max_len.
    - Query Datamuse with a wildcard spelling pattern (e.g., '?????').
    - Filter to purely alphabetic words (no spaces, hyphens, apostrophes).
    - Return a random pick from the results, or None on failure.

    Datamuse words endpoint:
    https://api.datamuse.com/words?sp=?????&max=1000
    """
    for _ in range(tries):
        target_len = random.randint(min_len, max_len)
        pattern = "?" * target_len
        url = f"https://api.datamuse.com/words?sp={pattern}&max={max_results}"
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            data = r.json()
            # Filter to alphabetic words of exact length (safety)
            candidates = [
                wobj.get("word", "").lower()
                for wobj in data
                if isinstance(wobj, dict)
                and wobj.get("word")
                and wobj["word"].isalpha()
                and len(wobj["word"]) == target_len
            ]
            if candidates:
                return random.choice(candidates)
        except requests.RequestException:
            # Try again with a new random length
            continue
    return None


# ----------------------------
# Offline fallback list
# ----------------------------

FALLBACK_WORDS = [
    "apple", "banana", "cherry", "date", "elderberry",
    "grape", "orange", "peach", "pear", "plum",
    "mango", "papaya", "kiwi", "melon", "apricot",
]


# ----------------------------
# Hangman game
# ----------------------------

class Hangman:
    def __init__(
        self,
        num_lives: int = 5,
        min_len: int = 5,
        max_len: int = 8,
        use_datamuse: bool = True,
        fallback_words: Optional[List[str]] = None,
    ):
        """
        Create a Hangman game.

        Args:
            num_lives: starting lives.
            min_len, max_len: desired word length range.
            use_datamuse: if True, try to fetch from Datamuse first.
            fallback_words: optional local list to use as a fallback.
        """
        self.num_lives = int(num_lives)
        self.min_len = int(min_len)
        self.max_len = int(max_len)
        self.use_datamuse = bool(use_datamuse)
        self.fallback_words = list(fallback_words) if fallback_words else list(FALLBACK_WORDS)

        self.word = self._choose_word()
        self.word_guessed = ["_"] * len(self.word)
        self.list_of_guesses: List[str] = []

        # Track remaining unique letters for win condition
        self._letters_remaining = set(self.word)
        self.num_letters = len(self._letters_remaining)

        print("Welcome to Hangman!")
        print(f"The word has {len(self.word)} letters.")
        print(" ".join(self.word_guessed))

    def _choose_word(self) -> str:
        """Choose a word via Datamuse or local fallback."""
        if self.use_datamuse:
            w = fetch_random_word_from_datamuse(self.min_len, self.max_len)
            if w:
                return w
            # If Datamuse fails, fall back silently
        # Filter fallback to desired length if possible
        pool = [w for w in self.fallback_words if self.min_len <= len(w) <= self.max_len and w.isalpha()]
        if not pool:
            pool = self.fallback_words[:]  # last resort
        return random.choice(pool).lower()

    def _reveal_letter_positions(self, guess: str) -> None:
        """Reveal guessed letter in the display list."""
        for i, ch in enumerate(self.word):
            if ch == guess:
                self.word_guessed[i] = guess

    def check_guess(self, guess: str) -> None:
        """Apply a validated guess (single alphabetic char not guessed before)."""
        guess = guess.lower()

        if guess in self.word:
            print(f"Good guess! '{guess}' is in the word.")
            self._reveal_letter_positions(guess)
            if guess in self._letters_remaining:
                self._letters_remaining.remove(guess)
                self.num_letters = len(self._letters_remaining)
        else:
            self.num_lives -= 1
            print(f"Sorry, '{guess}' is not in the word.")
            print(f"You have {self.num_lives} lives left.")

        print(" ".join(self.word_guessed))

    def ask_for_input(self) -> None:
        """
        Prompt the user for a guess and process it.
        This method performs one validated turn (not the whole game loop).
        """
        while True:
            guess = input("Please enter a single letter: ").strip().lower()

            if len(guess) != 1 or not guess.isalpha():
                print("Invalid letter. Please, enter a single alphabetical character.")
                continue

            if guess in self.list_of_guesses:
                print("You already tried that letter!")
                continue

            # Valid new guess
            self.list_of_guesses.append(guess)
            self.check_guess(guess)
            return


def play_game(
    num_lives: int = 5,
    min_len: int = 5,
    max_len: int = 8,
    use_datamuse: bool = True,
    fallback_words: Optional[List[str]] = None,
) -> None:
    game = Hangman(
        num_lives=num_lives,
        min_len=min_len,
        max_len=max_len,
        use_datamuse=use_datamuse,
        fallback_words=fallback_words,
    )

    while True:
        if game.num_lives <= 0:
            print(f"You lost! The word was: {game.word}")
            break
        if game.num_letters > 0:
            game.ask_for_input()
        else:
            print(f"Congratulations. You won the game! The word was: {game.word}")
            break


if __name__ == "__main__":
    # You can tweak lengths and lives here
    # Example: 5–7 letter words, 6 lives, use Datamuse with offline fallback
    play_game(num_lives=6, min_len=5, max_len=7, use_datamuse=True)
