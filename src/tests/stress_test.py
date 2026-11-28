import threading
import time
from unittest.mock import patch

from environment import Environment
from simulation import Simulation


MAX_INIT_TIME = 60
MAX_FINISH_TIME = 10


class StressSimulation(Simulation):

    def __init__(self, enviroment, config):
        super().__init__(enviroment, config)
        self.max_threads = 0
        self.finished_threads = []

    def _update_alive_threads_list(self):
        # Keep finished threads to count their cycles at the end of the test
        alive_threads = []

        for thread in self.threads:
            if thread.is_alive():
                alive_threads.append(thread)
            else:
                thread.join()
                self.finished_threads.append(thread)

        self.threads = alive_threads
        self.max_threads = max(self.max_threads, len(self.threads))

    def _print_simulation(self, force):
        # Avoid printing the matrix during the stress test
        pass


def run_stress_test(num_predators, matrix_size, duration, sleep_times):

    config = {
        "init_num_predators": num_predators,
        "alien_predator_ratio": 5,
        "hatching_egg_time": 30,
        "alien_sleep_time": sleep_times[0],
        "predator_sleep_time": sleep_times[1],
        "human_sleep_time": sleep_times[2]
    }

    environment = Environment(matrix_size)
    simulation = StressSimulation(environment, config)

    # Measure initial generation time separately
    init_start = time.monotonic()
    initialized = simulation.init()
    init_time = time.monotonic() - init_start

    if not initialized:
        print("ERROR: No se han podido generar todos los individuos")
        return None

    initial_population = (
        len(simulation.aliens) + len(simulation.predators) + len(simulation.humans)
    )

    thread_errors = []
    old_hook = threading.excepthook

    def save_thread_error(args):
        thread_errors.append(f"{args.thread.name}: {args.exc_value}")

    threading.excepthook = save_thread_error

    stop_time = [None]

    def stop_simulation():
        stop_time[0] = time.monotonic()
        simulation.game_over = True

    timer = threading.Timer(duration, stop_simulation)
    run_error = None
    run_start = time.monotonic()
    timer.start()

    try:
        with patch("builtins.print"):
            simulation.run()
    except Exception as error:
        run_error = f"{type(error).__name__}: {error}"
    finally:
        simulation.game_over = True
        timer.cancel()
        timer.join()

        # Wait for any threads that were started before a possible error
        for thread in simulation.threads:
            thread.join()

        threading.excepthook = old_hook

    run_end = time.monotonic()

    # Threads removed from simulation.threads are also included
    all_threads = simulation.finished_threads + simulation.threads
    unfinished_threads = 0
    total_cycles = 0

    for thread in all_threads:
        if thread.is_alive():
            unfinished_threads += 1
        total_cycles += thread.activity_cycles

    if stop_time[0] is not None:
        activity_time = stop_time[0] - run_start
        finish_time = run_end - stop_time[0]
    else:
        activity_time = run_end - run_start
        finish_time = None

    cycles_per_second = total_cycles / activity_time if activity_time > 0 else 0

    passed = (run_error is None and not thread_errors and unfinished_threads == 0
              and len(all_threads) >= initial_population and init_time <= MAX_INIT_TIME
              and (finish_time is None or finish_time <= MAX_FINISH_TIME))

    error_message = run_error
    if thread_errors:
        error_message = thread_errors[0]

    return {
        "initial": initial_population,
        "max_threads": simulation.max_threads,
        "cycles_per_second": cycles_per_second,
        "activity_time": activity_time,
        "natural_end": stop_time[0] is None,
        "init_time": init_time,
        "finish_time": finish_time,
        "threads_created": len(all_threads),
        "unfinished": unfinished_threads,
        "passed": passed,
        "error": error_message
    }


def main():
    matrix_size = 160
    duration = 10
    predator_cases = [128, 256, 384, 512, 768, 1024]

    # Each phase uses the same matrix and number of individuals
    phases = [
        ("NORMAL", (1, 2, 3)),
        ("INTENSIVA", (0.1, 0.2, 0.3))
    ]

    print("=== TEST DE ESTRES ===")
    print(f"Matriz: {matrix_size}x{matrix_size}")
    print(f"Tiempo por prueba: {duration} segundos")

    stop_test = False

    for phase_name, sleep_times in phases:
        print(f"\n=== FASE {phase_name} ===")
        print(f"Sleep Alien/Predator/Humano: {sleep_times}")
        print("Predators | Iniciales | Max. hilos | Ciclos/s | Activa (s) | Init (s) | Fin (s) | Resultado")

        for num_predators in predator_cases:
            result = run_stress_test(num_predators, matrix_size, duration, sleep_times)

            if result is None:
                stop_test = True
                break

            status = "OK" if result["passed"] else "ERROR"
            if result["passed"] and result["natural_end"]:
                status = "FIN NATURAL"
            finish_text = "---" if result["finish_time"] is None else f"{result['finish_time']:.2f}"
            print(f"{num_predators:>9} | {result['initial']:>9} | "
                  f"{result['max_threads']:>10} | "
                  f"{result['cycles_per_second']:>8.1f} | "
                  f"{result['activity_time']:>10.2f} | "
                  f"{result['init_time']:>8.2f} | "
                  f"{finish_text:>7} | {status}")

            if not result["passed"]:
                print(f"Hilos sin terminar: {result['unfinished']}")
                if result["init_time"] > MAX_INIT_TIME:
                    print("Inicializacion demasiado lenta")
                if result["finish_time"] is not None and result["finish_time"] > MAX_FINISH_TIME:
                    print("Finalizacion demasiado lenta")
                if result["error"]:
                    print(f"Error: {result['error']}")
                stop_test = True
                break

        if stop_test:
            print("Prueba detenida: no se aumenta mas la carga")
            break


if __name__ == "__main__":
    main()