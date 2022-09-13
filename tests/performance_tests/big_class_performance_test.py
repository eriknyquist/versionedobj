import importlib
import time
import string
import random
import sys
import os

import matplotlib
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))


def gen_random_string():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randrange(64, 128)))

def generate_big_class(filename, nesting_levels=100, vars_per_level=1000):
    with open(filename, 'w') as fh:
        fh.write("from versionedobj import VersionedObject\n\n")

        # First, generate all the nested classes...
        for n in range(nesting_levels):
            fh.write(f"class NestedConfig{n}(VersionedObject):\n")

            for v in range(vars_per_level - 1):
                fh.write(f"    var{v} = '{gen_random_string()}'\n")

            # Last var, might need to be another config object
            if n > 0:
                # Last var is another nested config
                fh.write(f"    var{vars_per_level - 1} = NestedConfig{n - 1}()\n")
            else:
                # Last var is not a nested config
                fh.write(f"    var{vars_per_level - 1} = '{gen_random_string()}'\n")

            fh.write("\n")

        # Now, generate the top-level class
        fh.write("class BigTestConfig(VersionedObject):\n")

        for v in range(vars_per_level - 1):
            var_data = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randrange(32, 64)))
            fh.write(f"    var{v} = '{var_data}'\n")

        fh.write(f"    var{vars_per_level - 1} = NestedConfig{nesting_levels - 1}()\n")

def run_test_iterations(index, nesting_levels, vars_per_level, num_iterations=10):
    # Generate module
    classname = f"big_test_class{index}"
    generate_big_class(f"{classname}.py", nesting_levels, vars_per_level)

    # Import module
    importlib.invalidate_caches()
    big_test_class = importlib.import_module(f"{classname}")

    init_start = time.time()
    cfg = big_test_class.BigTestConfig()
    init_time = time.time() - init_start

    to_dict_times = []
    to_json_times = []
    from_dict_times = []
    from_json_times = []
    j = ""

    print("starting test...")
    for i in range(num_iterations):
        to_dict_start = time.time()
        d = cfg.to_dict()
        to_dict_times.append(time.time() - to_dict_start)

        to_json_start = time.time()
        j = cfg.to_json()
        to_json_times.append(time.time() - to_json_start)

        from_dict_start = time.time()
        cfg.from_dict(d, validate=False)
        from_dict_times.append(time.time() - from_dict_start)

        from_json_start = time.time()
        cfg.from_json(j, validate=False)
        from_json_times.append(time.time() - from_json_start)

        print(f"completed iteration {i + 1}/{num_iterations}")

    to_dict_avg = sum(to_dict_times) / num_iterations
    to_json_avg = sum(to_json_times) / num_iterations
    from_dict_avg = sum(from_dict_times) / num_iterations
    from_json_avg = sum(from_json_times) / num_iterations

    os.remove(f"{classname}.py")

    return len(j), init_time, to_dict_avg, to_json_avg, from_dict_avg, from_json_avg

def main():
    json_lens = []
    init_times = []
    to_dict_times = []
    to_json_times = []
    from_dict_times = []
    from_json_times = []

    nesting_levels = []
    vars_per_levels = []

    def generate_data_point(index, nesting_level, vars_per_level):
        nesting_levels.append(nesting_level)
        vars_per_levels.append(vars_per_level)

        json_len, init_time, to_dict_time, to_json_time, from_dict_time, from_json_time = run_test_iterations(index, nesting_level, vars_per_level)
        json_lens.append(json_len)
        init_times.append(init_time)
        to_dict_times.append(to_dict_time)
        to_json_times.append(to_json_time)
        from_dict_times.append(from_dict_time)
        from_json_times.append(from_json_time)

    generate_data_point(0, 10, 10)
    generate_data_point(1, 10, 50)
    generate_data_point(2, 10, 100)
    generate_data_point(3, 20, 100)
    generate_data_point(4, 20, 150)
    generate_data_point(5, 20, 200)
    generate_data_point(6, 40, 200)
    generate_data_point(7, 40, 250)
    generate_data_point(8, 40, 300)
    generate_data_point(9, 60, 300)
    generate_data_point(10, 60, 350)
    generate_data_point(11, 60, 400)
    generate_data_point(12, 80, 400)
    generate_data_point(13, 80, 450)
    generate_data_point(14, 90, 500)
    generate_data_point(15, 90, 550)
    generate_data_point(16, 90, 600)
    generate_data_point(17, 100, 600)

    fig, ax1 = plt.subplots()

    ax2 = ax1.twiny()
    ax2.set_xlabel('Deepest sub-object nesting level')
    ax2.set_xlim(nesting_levels[0], nesting_levels[-1])

    ax3 = ax1.twiny()
    ax3.set_xlabel('Attribute count per nested sub-object')
    ax3.set_xlim(vars_per_levels[0], vars_per_levels[-1])
    ax3.spines["top"].set_position(("axes", 1.09))

    ax1.grid(linestyle='dotted')

    ax2.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: str(int(x))))
    ax3.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: str(int(x))))

    ax1.plot(json_lens, to_dict_times, label='time to complete to_dict()')
    ax1.plot(json_lens, from_dict_times, label='time to complete from_dict()')
    ax1.plot(json_lens, init_times, label='time to create object instance')

    l = ax1.get_xlim()
    l2 = ax2.get_xlim()
    f = lambda x : l2[0]+(x-l[0])/(l[1]-l[0])*(l2[1]-l2[0])
    ticks = f(ax1.get_xticks())
    ax2.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))

    l = ax1.get_xlim()
    l2 = ax3.get_xlim()
    f = lambda x : l2[0]+(x-l[0])/(l[1]-l[0])*(l2[1]-l2[0])
    ticks = f(ax1.get_xticks())
    ax3.xaxis.set_major_locator(matplotlib.ticker.FixedLocator(ticks))

    ax1.set_xlabel('JSON string size in bytes')
    ax1.set_ylabel('Time in seconds')
    ax1.get_xaxis().set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax1.legend(bbox_to_anchor=(0,1), loc='upper left', ncol=1)

    plt.show()

if __name__ == "__main__":
    main()
