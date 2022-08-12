# UDP Chat
![Main window](https://github.com/Yarosvet/udp_chat/raw/master/screenshot_udpchat.png)
---
A chat programm using UDP protocol and RSA-1024 encryption of messages, point-to-point.
# Run
```bash
pip3 install -r requirements.txt
python3 client.py
```
# Build
```bash
pip3 install pyinstaller
pyinstaller --noconsole --onefile client.py
```
