#! /usr/bin/python3
import re
import sys
import argparse


def parse_logs(file_handle):
    # Regular expressions to match the lines
    total_time_re = re.compile(r"^Total time:\s+([0-9.]+)")
    search_re = re.compile(r"^\s*Search:\s*\([0-9.]+\)\s*([0-9.]+)")
    apply_re = re.compile(r"^\s*Apply:\s*\([0-9.]+\)\s*([0-9.]+)")
    rebuild_re = re.compile(r"^\s*Rebuild:\s*\([0-9.]+\)\s*([0-9.]+)")

    # New components
    unions_re = re.compile(r"^\s*Unions:\s+([0-9.]+)")
    rebuild_classes_re = re.compile(r"^\s*Rebuild classes:\s+([0-9.]+)")
    update_whitelist_re = re.compile(r"^\s*Update whitelist:\s+([0-9.]+)")

    # Initialize totals
    total_time_sum = 0.0
    search_time_sum = 0.0
    apply_time_sum = 0.0
    rebuild_time_sum = 0.0

    # Initialize new component totals
    unions_time_sum = 0.0
    rebuild_classes_time_sum = 0.0
    update_whitelist_time_sum = 0.0

    for line_number, line in enumerate(file_handle, 1):
        # Strip leading/trailing whitespace
        line = line.strip()

        # Match Total time
        total_match = total_time_re.match(line)
        if total_match:
            try:
                value = float(total_match.group(1))
                total_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Total time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Total time on line {line_number}: '{line}'"
                )
            continue

        # Match Search time
        search_match = search_re.match(line)
        if search_match:
            try:
                value = float(search_match.group(1))
                search_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Search time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Search time on line {line_number}: '{line}'"
                )
            continue

        # Match Apply time
        apply_match = apply_re.match(line)
        if apply_match:
            try:
                value = float(apply_match.group(1))
                apply_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Apply time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Apply time on line {line_number}: '{line}'"
                )
            continue

        # Match Rebuild time
        rebuild_match = rebuild_re.match(line)
        if rebuild_match:
            try:
                value = float(rebuild_match.group(1))
                rebuild_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Rebuild time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Rebuild time on line {line_number}: '{line}'"
                )
            continue

        # Match Unions time
        unions_match = unions_re.match(line)
        if unions_match:
            try:
                value = float(unions_match.group(1))
                unions_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Unions time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Unions time on line {line_number}: '{line}'"
                )
            continue

        # Match Rebuild classes time
        rebuild_classes_match = rebuild_classes_re.match(line)
        if rebuild_classes_match:
            try:
                value = float(rebuild_classes_match.group(1))
                rebuild_classes_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Rebuild classes time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Rebuild classes time on line {line_number}: '{line}'"
                )
            continue

        # Match Update whitelist time
        update_whitelist_match = update_whitelist_re.match(line)
        if update_whitelist_match:
            try:
                value = float(update_whitelist_match.group(1))
                update_whitelist_time_sum += value
                # Debug statement (optional)
                # print(f"Line {line_number}: Found Update whitelist time = {value}")
            except ValueError:
                print(
                    f"Warning: Unable to parse Update whitelist time on line {line_number}: '{line}'"
                )
            continue

    return {
        "total_time_sum": total_time_sum,
        "search_time_sum": search_time_sum,
        "apply_time_sum": apply_time_sum,
        "rebuild_time_sum": rebuild_time_sum,
        "unions_time_sum": unions_time_sum,
        "rebuild_classes_time_sum": rebuild_classes_time_sum,
        "update_whitelist_time_sum": update_whitelist_time_sum,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse log files and compute aggregated time totals and fractions."
    )
    parser.add_argument(
        "logfile",
        nargs="?",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Path to the log file. Reads from stdin if not provided.",
    )
    args = parser.parse_args()

    totals = parse_logs(args.logfile)

    total_time = totals["total_time_sum"]
    search_time = totals["search_time_sum"]
    apply_time = totals["apply_time_sum"]
    rebuild_time = totals["rebuild_time_sum"]
    unions_time = totals["unions_time_sum"]
    rebuild_classes_time = totals["rebuild_classes_time_sum"]
    update_whitelist_time = totals["update_whitelist_time_sum"]

    print(f"\nAggregated Times:")
    print(f"  Total time: {total_time:.9f} seconds")

    if total_time > 0:
        search_fraction = search_time / total_time
        apply_fraction = apply_time / total_time
        rebuild_fraction = rebuild_time / total_time

        print(f"    Search:  {search_time:.9f} seconds ({search_fraction:.2%})")
        print(f"    Apply:   {apply_time:.9f} seconds ({apply_fraction:.2%})")
        print(f"    Rebuild: {rebuild_time:.9f} seconds ({rebuild_fraction:.2%})")
    else:
        print("  Total time is zero. Cannot compute fractions.")

    # Check if rebuild_time is greater than zero before computing fractions
    if rebuild_time > 0:
        print(f"\n  Breakdown of Rebuild Time:")
        print(
            f"    Unions:              {unions_time:.9f} seconds ({(unions_time / rebuild_time):.2%})"
        )
        print(
            f"    Rebuild classes:     {rebuild_classes_time:.9f} seconds ({(rebuild_classes_time / rebuild_time):.2%})"
        )
        print(
            f"    Update whitelist:    {update_whitelist_time:.9f} seconds ({(update_whitelist_time / rebuild_time):.2%})"
        )
    else:
        print(
            "\n  Rebuild time is zero. Cannot compute fractions for Rebuild breakdown."
        )


if __name__ == "__main__":
    main()
