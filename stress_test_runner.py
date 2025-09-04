"""Generate a continuous event stream to stress test the writer."""

import argparse
import random
import time

from reliable_writer import ReliableWriter


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test event writer")
    parser.add_argument("--duration", type=int, default=7200, help="Duration in seconds")
    parser.add_argument("--output", default="/tmp/stress_events.log", help="Output file path")
    args = parser.parse_args()

    writer = ReliableWriter(args.output)
    start = time.time()
    count = 0
    while time.time() - start < args.duration:
        writer.write({"event": count, "value": random.random()})
        time.sleep(0.01)
        count += 1
    writer.stop()
    print(f"generated {count} events")


if __name__ == "__main__":
    main()

