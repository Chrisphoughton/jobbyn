import pandas as pd

def csv_to_text(file_path):
    try:
        # Load the CSV
        df = pd.read_csv(file_path)

        # Convert the DataFrame to a readable text format
        text = df.to_string(index=False)  # Exclude the index for cleaner output
        return text
    except Exception as e:
        print(f"Error converting CSV to text: {e}")
        return ""

# Example usage
csv_file = "data/data.csv"
csv_text = csv_to_text(csv_file)
print(csv_text)