import os
import signal
import time


def main() -> None:
    redis_url = os.getenv("REDIS_URL", "redis://skillforge-redis:6379/0")
    runner_mode = os.getenv("RUNNER_MODE", "static-placeholder")
    print(f"SkillForge worker started. mode={runner_mode} redis={redis_url}", flush=True)
    print("MVP note: API performs static grading. Use this worker for the future Kubernetes Job runner.", flush=True)

    running = True

    def stop(*_: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while running:
        time.sleep(10)
        print("worker heartbeat", flush=True)


if __name__ == "__main__":
    main()
