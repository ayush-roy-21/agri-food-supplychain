import csv
import sys

def main():
    source_csv = 'data/results/topic_rq_grid_mapping.csv'
    dest_csv = 'topic_locus_mapping.csv'

    with open(source_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Exclude topics -1, 8, 9
    valid_topics = [r for r in rows if int(r['Topic']) not in (-1, 8, 9)]

    with open(dest_csv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Topic', 'Top_Keywords', 'Notes', 'locus_primary', 'locus_secondary'])
        writer.writeheader()
        for r in valid_topics:
            writer.writerow({
                'Topic': r['Topic'],
                'Top_Keywords': r['Top_Keywords'],
                'Notes': r['Notes'],
                'locus_primary': '',
                'locus_secondary': ''
            })

    print(f"Created {dest_csv} with {len(valid_topics)} topics.")

if __name__ == '__main__':
    main()
