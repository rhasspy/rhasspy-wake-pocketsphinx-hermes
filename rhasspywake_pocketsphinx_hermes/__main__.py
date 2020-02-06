"""Hermes MQTT service for Rhasspy wakeword with pocketsphinx"""
import argparse
import logging
from pathlib import Path

import paho.mqtt.client as mqtt

from . import WakeHermesMqtt

_LOGGER = logging.getLogger(__name__)


def main():
    """Main method."""
    parser = argparse.ArgumentParser(prog="rhasspy-wake-pocketsphinx-hermes")
    parser.add_argument(
        "--acoustic-model",
        required=True,
        help="Path to Pocketsphinx acoustic model directory (hmm)",
    )
    parser.add_argument(
        "--dictionary", required=True, help="Path to pronunciation dictionary file"
    )
    parser.add_argument(
        "--keyphrase", required=True, help="Keyword phrase to listen for"
    )
    parser.add_argument(
        "--keyphrase-threshold",
        type=float,
        default=1e-40,
        help="Threshold for keyphrase (default: 1e-40)",
    )
    parser.add_argument(
        "--mllr-matrix", default=None, help="Path to tuned MLLR matrix file"
    )
    parser.add_argument(
        "--wakewordId",
        default="default",
        help="Wakeword ID of each keyphrase (default: default)",
    )
    parser.add_argument(
        "--host", default="localhost", help="MQTT host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=1883, help="MQTT port (default: 1883)"
    )
    parser.add_argument(
        "--siteId",
        action="append",
        help="Hermes siteId(s) to listen for (default: all)",
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _LOGGER.debug(args)

    try:
        # Convert to paths
        args.acoustic_model = Path(args.acoustic_model)
        args.dictionary = Path(args.dictionary)

        if args.mllr_matrix:
            args.mllr_matrix = Path(args.mllr_matrix)

        # Listen for messages
        client = mqtt.Client()
        hermes = WakeHermesMqtt(
            client,
            args.keyphrase,
            args.acoustic_model,
            args.dictionary,
            wakeword_id=args.wakewordId,
            keyphrase_threshold=args.keyphrase_threshold,
            mllr_matrix=args.mllr_matrix,
            siteIds=args.siteId,
            debug=args.debug,
        )

        hermes.load_decoder()

        def on_disconnect(client, userdata, flags, rc):
            try:
                # Automatically reconnect
                _LOGGER.info("Disconnected. Trying to reconnect...")
                client.reconnect()
            except Exception:
                logging.exception("on_disconnect")

        # Connect
        client.on_connect = hermes.on_connect
        client.on_disconnect = on_disconnect
        client.on_message = hermes.on_message

        _LOGGER.debug("Connecting to %s:%s", args.host, args.port)
        client.connect(args.host, args.port)

        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug("Shutting down")


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()