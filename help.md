## pixly - a general purpose Skyblock Bot designed to be better than blockhelper, which was also made by me ^^

### Updating
- try to ensure that you always have the latest version of `skyblockparser` with the latest code installed

### Installing
- create a virtual environment and execute the activate Script.
`python -m venv venv`
`venv/Scripts/activate`
- install the required packages.
`pip install -r requirements.txt`

if you want to add a new package please include it in the requirements.txt.

### Usage
- update your constants in constants.example.py (bot token etc.) and rename it to constants.py
# DO NOT CHANGE THE .gitignore under any circumstance.

### Coding
- make sure to create commands like the ones already present in `commands/{command}.py`, (the logic should be present in `./util/views.py`) if you want them to include a profile selector, otherwise feel free to do whatever.

### Emojis
- I will be sharing an identity with which you can add your testing bot to each emoji server.
- The emoji files get automatically updated by me on a regular basis, therefore look at step updating.

### do not update emojis.