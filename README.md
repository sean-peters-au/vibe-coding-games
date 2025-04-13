# Tower Defense

A little tower defense game I made for an evenings amusement :)

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Gameplay

*   **Dynamic Path:** Enemies follow a randomly generated path that changes *every wave*!
*   **Tower Placement:** Place various towers by selecting them from the right-hand UI panel and clicking on valid grass tiles (left game area).
*   **Income:** Primarily earn gold by clicking placed **Gold Mines**. You also get a reward for completing each wave, and the **Bounty Hunter** tower grants gold for enemies it kills.
*   **Tower Mobility:** Towers aren't fixed! Adapt to the changing path:
    *   **Move:** Click and drag a tower to a new valid location. There's a cooldown before you can move it again (indicated by a bar below the tower).
    *   **Sell:** Right-click a tower to sell it for a partial refund.
*   **Waves:** Survive waves of increasingly difficult enemies, including Goblins, Ogres, Runners, Brutes, Diggers, and Dragons.
*   **Towers:** Place Guard Towers, Cannons (splash damage), Ice Towers (splash slow), Gold Mines (click for gold), and Bounty Hunters (get gold on kill).
*   **Objective:** Prevent enemies from reaching the end of the path by managing your defenses and economy.

## Controls

*   **Left Click (Game Area):** Place selected tower on grass / Drag existing tower.
*   **Left Click (UI Panel):** Select tower type to build.
*   **Left Click (Gold Mine):** Collect gold.
*   **Right Click (Tower):** Sell tower.
*   **ESC:** Quit game. 