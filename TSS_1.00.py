import csv
import itertools
import time
from tabulate import tabulate

start = time.time()

riders = []

# Reading data from CSV
with open("Cyclists.csv", "r") as file:
    reader = csv.DictReader(file)
    for row in reader:
        riders.append(row)


# Draft values for different positions (P1 to P4)
Draft = [0, 0.23, 0.28, 0.33, 0.33, 0.33, 0.33, 0.33]
Draft = list(map(float, Draft))

for rider in riders:
    rider["FTP"] = int(rider["FTP"])
    rider["Lead power"] = int(rider["Lead power"])
    rider["Lead time"] = int(rider["Time on front"])


# Possible time on front values to try
time_on_front_values = [30, 45, 60, 90]

# Function to remove cyclic permutations
def remove_cyclic_permutations(permutations):
    seen = set()
    unique_permutations = []

    for perm in permutations:
        perm_names = tuple(rider["Name"] for rider in perm)
        cyclic_shifts = [tuple(perm_names[i:] + perm_names[:i]) for i in range(len(perm_names))]
        canonical = min(cyclic_shifts)
        
        if canonical not in seen:
            unique_permutations.append(perm)
            seen.add(canonical)
    
    return unique_permutations

# Initial calculations
def calculate_tss_diff():
    all_permutations = list(itertools.permutations(riders, 8))
    unique_permutations = remove_cyclic_permutations(all_permutations)
    
    all_results = []

    # Iterate through all combinations of riders
    for combination in unique_permutations:
        power_on_front = [float(rider['Lead power']) for rider in combination]

        for i, rider in enumerate(combination):
            rider["Position"] = i + 1  # Position 1 to X

        # Time calculations (Power, Lead time, Time on front)
        for i, rider in enumerate(combination):
            for p in range(1, 9):
                rider[f'P{p}_W'] = power_on_front[(i - p + 1) % len(combination)] - (
                    power_on_front[(i - p + 1) % len(combination)] * Draft[p - 1])

        # Initialize variable
        total_time_on_front = 0

        for rider in combination:
            total_time_on_front += int(rider["Lead time"])

        # Estimated time to finish the course and number of cycles
        est_time = 46
        cycles = est_time * 60 / total_time_on_front  # Calculate the cycles

        time_on_fronts = [rider["Lead time"] * cycles for rider in combination]

        for i, rider in enumerate(combination):
            for p in range(1, 9):
                rider[f'P{p}_t'] = float(time_on_fronts[(i - p + 1) % len(combination)]) 

        # Time in percentage of hour
        for rider in combination:
            for p in range(1, 9):
                rider[f'P{p}_t_per'] = float(rider[f'P{p}_t'] / 36)

        # Normalized power & TSS calculation
        for rider in combination:
            NP_pretotal = 0
            t_per_total = 0
            for p in range(1, 9):
                P_W = float(rider[f"P{p}_W"])
                P_t_per = float(rider[f"P{p}_t_per"])
                NP_pretotal += (P_W ** 4) * P_t_per
                t_per_total += P_t_per

            rider["NP"] = float((NP_pretotal / t_per_total) ** (1 / 4))
            rider["TSS"] = float((rider["NP"] / rider["FTP"]) ** 2 * t_per_total)

        # Calculate the difference between the highest and lowest TSS values for this combination
        tss_values = [rider["TSS"] for rider in combination]
        tss_difference = round(max(tss_values) - min(tss_values), 2)

        combination_result = {
            "combination": combination,
            "TSS_diff": tss_difference
        }
        all_results.append(combination_result)

    # Sort the results by TSS_diff (ascending order: lowest first)
    all_results_sorted = sorted(all_results, key=lambda x: x['TSS_diff'])

    lowest_tss_diff = all_results_sorted[0]['TSS_diff']
    lowest_tss_combination = all_results_sorted[0]['combination']

    return lowest_tss_diff, lowest_tss_combination

# Prepare the CSV file
csv_file = open('tss_results.csv', mode='w', newline='')
csv_writer = csv.writer(csv_file)

# Write the header to the CSV file
header = ["TSS_diff", "Rider Name", "Position", "Lead time", "TSS"] + [f"P{i}_W" for i in range(1, 9)]
csv_writer.writerow(header)

# Main loop to adjust Lead time and continue until TSS_diff < 7
lowest_tss_diff, lowest_tss_combination = calculate_tss_diff()

# Loop until the lowest TSS difference is below 7
while lowest_tss_diff >= 6:
    print(f"Lowest TSS difference: {lowest_tss_diff}")
    print("Corresponding riders and positions:")

    # Prepare the data for the table
    table_data = []
    for rider in lowest_tss_combination:
        row = [rider['Name'], rider['Position'], rider["Lead time"], round(rider['TSS'], 2)]
        # Add P1_t to P8_t and P1_W to P8_W to the row
        for p in range(1, 9):
            row.append(round(rider[f'P{p}_W'], 0))  # Add P1_W to P8_W
        table_data.append(row)

    # Print the final table with additional columns
    headers = ["Rider Name", "Position", "Lead time", "TSS"] + [f"P{i}_W" for i in range(1, 9)]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # Write the result to the CSV file after each iteration
    #for row in table_data:
    #    csv_writer.writerow([lowest_tss_diff] + row)
    
    # Write an empty row to the CSV after each iteration's results
    #csv_writer.writerow([])  # This inserts an empty row

    # Identify the rider with the lowest TSS and increment their Lead time
    min_tss_rider = min(lowest_tss_combination, key=lambda rider: rider["TSS"])
    
    # Find the index of the rider and increment their Lead time by 1
    min_tss_rider_index = lowest_tss_combination.index(min_tss_rider)
    current_lead_time = int(min_tss_rider["Lead time"])

    # Increment the Lead time
    new_lead_time = time_on_front_values[(time_on_front_values.index(current_lead_time) + 1) % len(time_on_front_values)]
    min_tss_rider["Lead time"] = new_lead_time  # Update Lead time directly on the original rider list

    # Recalculate the TSS difference with the updated Lead time
    lowest_tss_diff, lowest_tss_combination = calculate_tss_diff()

# Final results after the loop
print(f"\nFinal lowest TSS difference: {lowest_tss_diff}")
print("Corresponding riders and positions:")

table_data = []
for rider in lowest_tss_combination:
    row = [rider['Name'], rider['Position'], rider["Lead time"], round(rider['TSS'], 2)]
    for p in range(1, 9):
        row.append(round(rider[f'P{p}_W'], 0))  # Add P1_W to P8_W
    table_data.append(row)

# Print the final table with additional columns
headers = ["Rider Name", "Position", "Lead time", "TSS"] + [f"P{i}_W" for i in range(1, 9)]
print(tabulate(table_data, headers=headers, tablefmt="grid"))

# Write the final result to the CSV file
for row in table_data:
    csv_writer.writerow([lowest_tss_diff] + row)

# Write an empty row after the final results
csv_writer.writerow([])  # This inserts an empty row

# Close the CSV file
csv_file.close()

print('{0:.2f} seconds elapsed.'.format(time.time()-start))
