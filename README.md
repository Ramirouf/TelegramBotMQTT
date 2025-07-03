# MQTT Telegram Thermostat Bot

This project is a Python-based Telegram bot that serves as a remote control for a smart thermostat built with a Raspberry Pi Pico. The bot provides a simple inline keyboard interface to send commands to the device via an MQTT broker.

## How It Works

The system architecture is straightforward:

```
User <--> Telegram Bot <--> MQTT Broker <--> Raspberry Pi Pico --> Relay
```

1.  The user sends a command to the bot using the Telegram interface.
2.  The Python bot publishes a message to the appropriate MQTT topic.
3.  The Raspberry Pi Pico, subscribed to these topics, receives the message and controls the relay or updates its settings.

## Features

- **Setpoint:** Set the target temperature for automatic mode.
- **Periodo:** Configure the data publishing interval of the device.
- **Modo:** Switch between Automatic (thermostat) and Manual control.
- **Relé:** Manually turn the relay ON or OFF when in Manual mode.
- **Destello:** Blink the Pico's onboard LED for diagnostics.
- **Secure:** Only authorized Telegram user IDs can interact with the bot.

## Technologies Used

- **Language:** Python 3.11+
- **Bot Framework:** `python-telegram-bot`
- **MQTT Communication:** `aiomqtt`
- **Concurrency:** `asyncio`
- **Deployment:** Docker (recommended)

## How to Use

### 1. Prerequisites

- A running MQTT Broker.
- A Telegram Bot Token obtained from [@BotFather](https://t.me/BotFather).
- Your Telegram User ID. You can get it from [@userinfobot](https://t.me/userinfobot).

### 2. Configuration

Clone the repository and create a `.env` file in the root directory with the following variables:

```
# Your Telegram Bot Token
TB_TOKEN="12345:ABC-DEF12345"

# Comma-separated list of authorized Telegram User IDs
TB_AUTORIZADOS="123456789,987654321"

# Your MQTT Broker details
SERVIDOR="your-mqtt-broker.com"
MQTT_PORT="23816" # Your broker's port
MQTT_USR="your_username"
MQTT_PASS="your_password"
```

### 3. Running the Bot

#### Using Docker (Recommended)

1.  **Build the Docker image:**

    ```bash
    docker build -t thermostat-bot .
    ```

2.  **Run the container:**
    ```bash
    docker run --env-file .env --rm --name my-thermostat-bot thermostat-bot
    ```

#### Using Python Virtual Environment

1.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install python-telegram-bot aiomqtt
    ```

3.  **Run the bot:**
    ```bash
    python telegrambot.py
    ```
