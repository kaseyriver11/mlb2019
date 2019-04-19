
import pandas as pd

if __name__ == '__main__':

    a = [1, 2, 3, 4, 5]

    df = pd.DataFrame(a)
    df.to_csv("test.csv")
