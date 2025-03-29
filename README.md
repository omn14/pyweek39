# Logs Odysseys
## Overview
Logs Odysseys is a log-floating game built using Panda3D, a powerful game engine for 3D rendering and game development. It aims to create semi-realistic fluid flow mechanics where players navigate logs through a braided river system. It was developed as an entry for PyWeek 39, where the theme for the game jam was "Downstream".

## Rules
You just bought a ton of wood upriver. You must float it down to the sawmill to sell at a higher price. Watch out so timber doesn't get stuck or lost off to side rivers. Use left mouse button to push wood with a shock wave. Use right mouse button to place a river barrier. Longer logs have more mass and fetch a higher price at the sawmill, but are more difficult to control. Each batch of wood you buy gets more expensive. Please keep the wood flowing to the mill! If you run out of money in the bank, the game is literally over.

## Features
- Semi-realistic water simulation based on the Navier-Stokes equation
- Log floating in a braided river system
- Interactive elements for user engagement
- Economic system

## Requirements
- Python 3.8 or later
- Panda3D 1.10 or later

## Installation
1. Clone the repository:
    ```bash
    git clone <repository-url>
    ```
2. Navigate to the project directory:
    ```bash
    cd river
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
Run the main script to start the simulation:
```bash
python main.py
```

## Assets
- Sound effects: https://freesound.org/people/MessySloth/sounds/750289/
- 3D Models: https://www.blenderkit.com/asset-gallery-detail/72ce2c5b-03b6-44e3-9c2a-4e0e38e3cbb0/
- Water shader adapted from: https://www.shadertoy.com/view/ldd3WS

## Contributing
Contributions are welcome! Please fork the repository and submit a pull request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.
