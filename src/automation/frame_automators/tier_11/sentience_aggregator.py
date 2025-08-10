"""
Sentience Aggregator Automator (Frame ID: 11.3)
Handles automation for the Sentience Aggregator frame in WidgetInc.
"""

import time
import pyautogui
from imagehash import phash
from PIL import ImageGrab
from typing import Any, Dict
from automation.base_automator import BaseAutomator


class SentienceAggregatorAutomator(BaseAutomator):
    """Automation logic for Sentience Aggregator (Frame 11.3)."""

    def __init__(self, frame_data: Dict[str, Any]):
        super().__init__(frame_data)

    def check_and_reset_board(self, bboxes, get_hash, THRESHOLD):
        """
        Check board state and return list of face-down cards.
        Handles edge case of odd number of face-down cards.
        """
        face_down_cards = []

        for i in range(len(bboxes)):
            current_hash = get_hash(i)
            if abs(current_hash - self.back_hash) < THRESHOLD:
                face_down_cards.append(i)

        if face_down_cards:
            # Handle odd number of face-down cards edge case
            if len(face_down_cards) % 2 != 0:
                self.logger.debug(
                    f"EDGE CASE: Odd number of face-down cards ({len(face_down_cards)}) - game waiting for second card"
                )
                self.logger.debug("Clicking any face-down card to put game in correct state")
                # Click the first face-down card to complete the pair
                centers = [((x1 + x2) // 2, (y1 + y2) // 2) for (x1, y1, x2, y2) in bboxes]
                pyautogui.click(*centers[face_down_cards[0]])
                self.sleep(0.5)  # Wait for flip animation

                # Reassess board again after the click
                face_down_cards = []
                for i in range(len(bboxes)):
                    current_hash = get_hash(i)
                    if abs(current_hash - self.back_hash) < THRESHOLD:
                        face_down_cards.append(i)

            self.logger.debug(f"Found {len(face_down_cards)} face-down cards: {face_down_cards}")
            return face_down_cards

        return None

    def run_automation(self):
        start_time = time.time()
        all_bboxes = self.frame_data["bbox"]
        bboxes = [bbox for bbox in all_bboxes.values() if isinstance(bbox, (list, tuple)) and len(bbox) == 4]
        centers = [((x1 + x2) // 2, (y1 + y2) // 2) for (x1, y1, x2, y2) in bboxes]
        THRESHOLD = 5
        BACKHASH_THRESHOLD = 20

        def get_hash(idx):
            return phash(ImageGrab.grab(bbox=tuple(bboxes[idx]), all_screens=True))

        # Store back hash once at start when all cards are guaranteed face down
        self.back_hash = get_hash(0)

        # Track loop detection
        last_queue_states = []
        loop_detection_threshold = 5

        while self.should_continue:
            if time.time() - start_time > self.max_run_time:
                break

            # Build the initial queue
            cards = list(range(len(bboxes)))
            hashes = [None for _ in range(len(bboxes))]  # type: ignore
            matched = [False] * len(bboxes)
            last_queue_states.clear()

            self.logger.debug(f"Initial card list: {cards}")

            while cards and self.should_continue:
                # Loop detection - check if we've seen this queue state before
                current_queue_state = tuple(sorted(cards))
                if current_queue_state in last_queue_states:
                    loop_count = last_queue_states.count(current_queue_state)
                    if loop_count >= loop_detection_threshold:
                        self.logger.debug(
                            f"Loop detected! Queue {cards} seen {loop_count} times - checking board state"
                        )
                        face_down_cards = self.check_and_reset_board(bboxes, get_hash, BACKHASH_THRESHOLD)
                        if face_down_cards:
                            cards = face_down_cards
                            hashes = [None for _ in range(len(bboxes))]  # type: ignore
                            matched = [False] * len(bboxes)
                            last_queue_states.clear()
                            self.logger.debug(f"Loop reset complete, new queue: {cards}")
                            continue
                        else:
                            self.logger.debug("No face-down cards found, breaking out of stuck loop")
                            break

                last_queue_states.append(current_queue_state)
                if len(last_queue_states) > 10:
                    last_queue_states.pop(0)

                # Take first two cards
                card1 = cards.pop(0)
                card2 = cards.pop(0) if cards else None

                if card2 is None:
                    break

                # Skip if either card is already matched
                if matched[card1] or matched[card2]:
                    continue

                # Pre-click validation: Ensure cards are actually face down before clicking
                card1_hash = get_hash(card1)
                if abs(card1_hash - self.back_hash) >= BACKHASH_THRESHOLD:
                    self.logger.debug(
                        f"Card {card1} is face up when expected to be face down - forcing board reassessment"
                    )
                    face_down_cards = self.check_and_reset_board(bboxes, get_hash, BACKHASH_THRESHOLD)
                    if face_down_cards:
                        cards = face_down_cards
                        hashes = [None for _ in range(len(bboxes))]  # type: ignore
                        matched = [False] * len(bboxes)
                        last_queue_states.clear()
                        self.logger.debug(f"Ultra-aggressive reset complete, new queue: {cards}")
                        continue

                    self.logger.error("Board reassessment failed - breaking automation")
                    break

                card2_hash = get_hash(card2)
                if abs(card2_hash - self.back_hash) >= BACKHASH_THRESHOLD:
                    self.logger.debug(
                        f"Card {card2} is face up when expected to be face down - forcing board reassessment"
                    )
                    face_down_cards = self.check_and_reset_board(bboxes, get_hash, BACKHASH_THRESHOLD)
                    if face_down_cards:
                        cards = face_down_cards
                        hashes = [None for _ in range(len(bboxes))]  # type: ignore
                        matched = [False] * len(bboxes)
                        last_queue_states.clear()
                        self.logger.debug(f"Ultra-aggressive reset complete, new queue: {cards}")
                        continue

                    self.logger.error("Board reassessment failed - breaking automation")
                    break

                # Click first two cards in queue
                pyautogui.click(*centers[card1])
                self.sleep(0.15)
                hashes[card1] = get_hash(card1)  # type: ignore
                self.logger.debug(f"Flipped card {card1}, hash: {str(hashes[card1])}")

                pyautogui.click(*centers[card2])
                self.sleep(0.15)
                hashes[card2] = get_hash(card2)  # type: ignore
                self.logger.debug(f"Flipped card {card2}, hash: {str(hashes[card2])}")

                self.logger.debug(f"Clicked pair: {card1}, {card2}")

                # While waiting the required time, check for matches
                diff = int(hashes[card1] - hashes[card2])  # type: ignore
                self.logger.debug(f"Current pair diff {card1}-{card2}: {diff}")

                if diff < THRESHOLD:
                    # Match found - remove from queue and mark them true
                    matched[card1] = True
                    matched[card2] = True
                    # Remove matched cards from anywhere else in the queue
                    cards = [c for c in cards if c not in (card1, card2)]
                    self.logger.debug(f"Confirmed match: {card1} and {card2}, removed from queue")
                else:
                    # If not match, compare both cards to all other hashes
                    potential_matches = []
                    for i in range(len(hashes)):
                        if matched[i] or hashes[i] is None or i == card1 or i == card2:
                            continue

                        if hashes[card1] is not None and int(hashes[card1] - hashes[i]) < THRESHOLD:  # type: ignore
                            potential_matches.append((card1, i))
                            self.logger.debug(f"Found potential match: {card1} matches {i}")

                        if hashes[card2] is not None and int(hashes[card2] - hashes[i]) < THRESHOLD:  # type: ignore
                            potential_matches.append((card2, i))
                            self.logger.debug(f"Found potential match: {card2} matches {i}")

                    if potential_matches:
                        # Add ALL potential matches to front of queue
                        for match_card1, match_card2 in potential_matches:
                            # Remove these cards from anywhere else in the queue first
                            cards = [c for c in cards if c not in (match_card1, match_card2)]
                            # Add to front (in reverse order so first match gets clicked first)
                            cards.insert(0, match_card2)
                            cards.insert(0, match_card1)
                            self.logger.debug(f"Moved potential match ({match_card1}, {match_card2}) to front of queue")
                    else:
                        # No matches found - cycle current pair to end
                        cards.append(card1)
                        cards.append(card2)
                        self.logger.debug(f"No matches found, cycling {card1}, {card2} to end")

                self.logger.debug(f"Remaining cards: {cards}")
                self.sleep(1)  # Wait for animation

            self.logger.debug(f"Final matched state: {matched}")

            # Check if all cards are actually matched or if there are face-down cards
            if all(matched):
                face_down_cards = self.check_and_reset_board(bboxes, get_hash, BACKHASH_THRESHOLD)
                if face_down_cards:
                    self.logger.debug("Found face-down cards, starting new round")
                    continue
                else:
                    self.logger.debug("All cards still face up, waiting...")

            if not self.sleep(0.2):
                break


"""
"bbox": {
    "1": [0.458565, 0.193056, 0.492361, 0.245833],
    "2": [0.458565, 0.343056, 0.492361, 0.395833],
    "3": [0.458565, 0.493056, 0.492361, 0.545833],
    "4": [0.458565, 0.643056, 0.492361, 0.695833],
    "5": [0.583565, 0.193056, 0.617361, 0.245833],
    "6": [0.583565, 0.343056, 0.617361, 0.395833],
    "7": [0.583565, 0.493056, 0.617361, 0.545833],
    "8": [0.583565, 0.643056, 0.617361, 0.695833],
    "9": [0.708565, 0.193056, 0.742361, 0.245833],
    "10": [0.708565, 0.343056, 0.742361, 0.395833],
    "11": [0.708565, 0.493056, 0.742361, 0.545833],
    "12": [0.708565, 0.643056, 0.742361, 0.695833],
    "13": [0.833565, 0.193056, 0.867361, 0.245833],
    "14": [0.833565, 0.343056, 0.867361, 0.395833],
    "15": [0.833565, 0.493056, 0.867361, 0.545833],
    "16": [0.833565, 0.643056, 0.867361, 0.695833]
}
"bbox": {
    "1": [0.441667, 0.166667, 0.509259, 0.272222],
    "2": [0.441667, 0.316667, 0.509259, 0.422222],
    "3": [0.441667, 0.466667, 0.509259, 0.572222],
    "4": [0.441667, 0.616667, 0.509259, 0.722222],
    "5": [0.566667, 0.166667, 0.634259, 0.272222],
    "6": [0.566667, 0.316667, 0.634259, 0.422222],
    "7": [0.566667, 0.466667, 0.634259, 0.572222],
    "8": [0.566667, 0.616667, 0.634259, 0.722222],
    "9": [0.691667, 0.166667, 0.759259, 0.272222],
    "10": [0.691667, 0.316667, 0.759259, 0.422222],
    "11": [0.691667, 0.466667, 0.759259, 0.572222],
    "12": [0.691667, 0.616667, 0.759259, 0.722222],
    "13": [0.816667, 0.166667, 0.884259, 0.272222],
    "14": [0.816667, 0.316667, 0.884259, 0.422222],
    "15": [0.816667, 0.466667, 0.884259, 0.572222],
    "16": [0.816667, 0.616667, 0.884259, 0.722222]
}

"""
