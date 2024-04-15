
import pandas as pd
from sklearn.datasets import load_iris

# Load Iris dataset
iris = load_iris()
df = pd.DataFrame(data=iris.data, columns=iris.feature_names)

# Calculate mean and standard deviation for sepal length and width
sepal_length_mean = df['sepal length (cm)'].mean()
sepal_width_mean = df['sepal width (cm)'].mean()
sepal_length_std = df['sepal length (cm)'].std()
sepal_width_std = df['sepal width (cm)'].std()

print(f"Sepal Length - Mean: {sepal_length_mean:.2f}, Std: {sepal_length_std:.2f}")
print(f"Sepal Width - Mean: {sepal_width_mean:.2f}, Std: {sepal_width_std:.2f}")

my_str = "foo"

my_dict = {}
my_dict[my_str] = 123

if True:
    scoped_df = pd.DataFrame()
