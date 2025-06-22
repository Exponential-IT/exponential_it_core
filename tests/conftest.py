import pytest
import time
from collections import defaultdict
from pathlib import Path

_descriptive_results = defaultdict(list)
_test_durations = {}
_test_status = {}
_slow_threshold = 0.5  # segundos
_summary_lines = []
_summary_path = Path("tests/test_summary.txt")

# Colores ANSI
GREEN = "\033[92m"
RED = "\033[91m"
GREY = "\033[90m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def pytest_itemcollected(item):
    """Reemplaza el nodeid por el docstring si existe"""
    doc = item._obj.__doc__
    nodeid = doc.strip() if doc else item.nodeid
    item._nodeid = nodeid
    _descriptive_results[item.fspath].append(nodeid)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    """Mide la duración del test"""
    start = time.time()
    outcome = yield
    duration = time.time() - start
    _test_durations[item.nodeid] = duration


def pytest_runtest_logreport(report):
    """Registra si el test pasó o falló"""
    if report.when == "call":
        _test_status[report.nodeid] = report.outcome


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Resumen por archivo con colores, tiempos, totales y exportado a archivo"""
    separator = "=" * 110
    header = f"{separator}\nResumen agrupado por archivo y descripción\n{separator}\n"
    terminalreporter.write_sep("=", "Resumen agrupado por archivo y descripción")
    _summary_lines.append(header)

    total_tests = 0
    total_passed = 0

    for file, descriptions in _descriptive_results.items():
        file_name = Path(file).name
        passed = 0

        file_str = f"\n📄 {GREY}{file_name}{RESET}"
        _summary_lines.append(f"\n📄 {file_name}")
        terminalreporter.write_line(file_str)

        for desc in descriptions:
            duration = _test_durations.get(desc, 0)
            status = _test_status.get(desc, "passed")
            status_icon = (
                f"{GREEN}✓{RESET}" if status == "passed" else f"{RED}❌{RESET}"
            )
            raw_icon = "✓" if status == "passed" else "❌"
            slow_flag = f"{YELLOW} 🐢{RESET}" if duration > _slow_threshold else ""
            raw_slow_flag = " 🐢" if duration > _slow_threshold else ""

            line = f"  - {status_icon} {desc} ({duration:.2f}s){slow_flag}"
            raw_line = f"  - {raw_icon} {desc} ({duration:.2f}s){raw_slow_flag}"

            terminalreporter.write_line(line)
            _summary_lines.append(raw_line)

            total_tests += 1
            if status == "passed":
                passed += 1

        total_passed += passed
        terminalreporter.write_line(
            f"  📊 Total archivo: {passed}/{len(descriptions)} passed\n"
        )
        _summary_lines.append(
            f"  📊 Total archivo: {passed}/{len(descriptions)} passed\n"
        )

    # Resumen global
    footer = f"{separator}\n🧮 Total global: {total_passed}/{total_tests} tests passed\n{separator}\n"
    terminalreporter.write_line(footer)
    _summary_lines.append(footer)

    # Guardar resumen
    _summary_path.parent.mkdir(parents=True, exist_ok=True)
    _summary_path.write_text("\n".join(_summary_lines), encoding="utf-8")
