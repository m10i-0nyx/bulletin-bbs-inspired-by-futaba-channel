# A bulletin board inspired by Futaba Channel.
ふたばちゃんねるを意識した掲示板

## Install
```bash
sudo dnf install git python3.13-pip mariadb1011-server nginx
cd ~
git clone https://github.com/m10i-0nyx/bulletin-bbs-inspired-by-futaba-channel.git bbs
cd bbs
python3.13 -m venv venv
source ./venv/bin/activate
pip3 install -U -r requirements.txt
mkdir -p ~/.config/systemd/user/
cp streamlit.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now streamlit.service
```
