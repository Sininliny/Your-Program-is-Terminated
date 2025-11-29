# Your-Program-is-Terminated

A simple tool lib for **linux** to send notification email when your **Python** progam is terminated.

# Quick Start

### 1. Download your_program_is_terminated.py to where it will be imported

### 2. Import termination_monitor

```
from your_program_is_terminated import termination_monitor
```

_Install any missing required python packages_

### 3. Set up config

_Tips: If you're setting a **Gmail** as sender, please active two-step authority for your gmail account and use the 16 characters **App Password** without spaces as the SENDER PASSWORD. Visit [Sign in with app passwords - Google Account Help](https://support.google.com/accounts/answer/185833?hl=en) for more info._

##### 3.1 Config by environment variables (Recommended)

```
# In ~/.bashrc
export TERMINATION_MONITOR_RECIPIENT_EMAIL="target@example.com"
export TERMINATION_MONITOR_SMTP_HOST="smtp.gmail.com"
export TERMINATION_MONITOR_SMTP_PORT="587"
export TERMINATION_MONITOR_SENDER_EMAIL="example@gmail.com"
export TERMINATION_MONITOR_SENDER_PASSWORD="xxxxxxxxxxxxxxxx"

# Set up proxy if it needs. Priority: HTTP > HTTPS > SOCKS
export TERMINATION_MONITOR_HTTP_PROXY="http://127.0.0.1:1111"
export TERMINATION_MONITOR_HTTPS_PROXY="http://127.0.0.1:1111"
export TERMINATION_MONITOR_SOCKS_PROXY="socks5://127.0.0.1:1111"
```

```
$ source ~/.bashrc
```

##### 3.2 Config by instance init parameters (This will overwrite env setting)

```
email_config = {
    "recipient_email": "target@example.com",
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "example@gmail.com",
    "sender_password": "xxxxxxxxxxxxxxxx", 
    "http_proxy": "http://127.0.0.1:1111",
    "https_proxy": "http://127.0.0.1:1111",
    "socks_proxy": "socks5://127.0.0.1:1111"
}
with termination_monitor(**email_config):
    your_enterpoint_func()
```

### 4. Use termination_monitor with your program main enterpoint

```
from your_program_is_terminated import termination_monitor

# Example
if __name__ == '__main__':
    # Email alert
    with termination_monitor():
        your_enterpoint_func()
```

### 5. Run your program
