import pandas as pd
df = pd.read_csv('data/results/bertopic_topic_info.csv')
for i, row in df.iterrows():
    print(f"Topic {row['Topic']}: {row['Name']} (Count: {row['Count']})")
    docs = eval(row['Representative_Docs'])
    for d in docs[:1]:
        print('  Doc snippet:', d[:200].replace('\n', ' '))
