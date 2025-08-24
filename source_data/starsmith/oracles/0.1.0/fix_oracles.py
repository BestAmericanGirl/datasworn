from pathlib import Path
from pprint import pp
# ruamel.yaml supports periods in anchor names and preserves order on yaml output
from ruamel.yaml import YAML

yaml = YAML()


def fix_oracle(oracle, filename):
    remove_keys(oracle)

    oracle['datasworn_version'] = '0.1.0'
    oracle['type'] = 'expansion'
    oracle['ruleset'] = 'starforged'
    oracle['_id'] = 'starsmith'

    for _, ora in oracle["oracles"].items():
        fix_oracle_collection(ora)

    out_dir = Path('.') / 'oracles'
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f'{filename}'
    print(out_file)
    with open(out_file, 'w', encoding='utf-8') as f:
        yaml.dump(oracle, f)


def fix_oracle_collection(oracle):
    if 'enhances' in oracle:
        oracle['enhances'] = fix_enhances(oracle['enhances'])
    oracle['type'] = 'oracle_collection'
    if 'oracle_type' not in oracle:
        oracle['oracle_type'] = 'tables'
    if 'contents' in oracle:
        for _, oracle_rollable in oracle['contents'].items():
            fix_oracle_rollable(oracle_rollable)

    if oracle['name'] == 'Opportunity' or oracle['name'] == 'Peril':
        insert_null_rolls(oracle['contents']['lifebearing'], oracle['contents']['lifeless'])

    if 'collections' in oracle:
        for collection in oracle['collections'].values():
            fix_oracle_collection(collection)


def insert_null_rolls(lifebearing, lifeless):
    TABLES_PER_TABLE = 3
    lifebearing_rows = lifebearing['rows']
    lifeless_rows = lifeless['rows']
    diff = (len(lifebearing_rows) - len(lifeless_rows)) // TABLES_PER_TABLE
    lifebearing_table_offset = len(lifebearing_rows) // TABLES_PER_TABLE
    lifeless_table_offset = len(lifeless_rows) // TABLES_PER_TABLE

    lifeless_segments = []

    for idx in range(TABLES_PER_TABLE):
        lifeless_segments.append([
            {
                'roll': None,
            #     'roll': {
            #         'min': None,
            #         'max': None,
            # },
            'text': row['text']}
            for row in lifebearing_rows[idx * lifebearing_table_offset:idx * lifebearing_table_offset + diff]
        ])
        lifeless_segments.append(lifeless_rows[idx * lifeless_table_offset:(idx + 1) * lifeless_table_offset])

    lifeless['rows'] = sum(lifeless_segments, start=[])


def fix_oracle_rollable(oracle_rollable):
    oracle_rollable['type'] = 'oracle_rollable'
    if 'replaces' in oracle_rollable:
        new_replaces = oracle_rollable['replaces'].replace('/oracles', '')
        oracle_rollable['replaces'] = [f'oracle_rollable:{new_replaces}']
    fix_rows(oracle_rollable['rows'])


def fix_rows(rows):
    for row in rows:
        if 'text' in row:
            if 'text' in row.non_merged_items():
                row['text'] = row['text'].replace('/oracles', '').replace('starforged', 'starsmith')
            else:
                fix_merge_text(row)
        if 'oracle_rolls' in row:
            fix_oracle_rolls(row['oracle_rolls'])
        fix_minmax_merge(row)
        if 'roll' in row:
            continue

        if 'min' not in row:
            continue

        try:
            minmax_to_roll(row)
        except:
            pp(row)
            pp(rows)
            raise


def fix_merge_text(row):
    for _, ma in row.merge:
        if 'text' in ma:
            ma['text'] = ma['text'].replace('/oracles', '').replace('id:', 'oracle_rollable:').replace('starforged', 'starsmith')

    row.update_key_value('text')


def fix_minmax_merge(row):
    for jdx, me in enumerate(row.merge):
        idx, ma = me
        if 'min' in ma:
            row.merge.pop(jdx)
            row.add_yaml_merge([(idx, fix_minmax_anchor(ma))])


def fix_minmax_anchor(ma):
    # FUCK YAML
    ma['roll'] = {
        'min': ma['min'],
        'max': ma['max']
    }

    del ma['min']
    del ma['max']

    return ma


def minmax_to_roll(row):
    row['roll'] = {
        'min': row['min'],
        'max': row['max'],
    }
    del row['min']
    del row['max']



def fix_oracle_rolls(oracle_rolls):
    for oracle_roll in oracle_rolls:
        if 'oracle' not in oracle_roll:
            continue
        oracle = oracle_roll['oracle']
        if oracle is None:
            continue
        if oracle.startswith('oracle_rollable:'):
            continue
        oracle = oracle.replace('/oracles', '').replace('starforged', 'starsmith')
        oracle_roll['oracle'] = f'oracle_rollable:{oracle}'


def fix_enhances(enhances):
    return [f'oracle_collection:{enhances}']


def remove_keys(oracle):
    keys_to_remove = ['title', 'authors', 'date', 'url', 'license', 'package_type', 'id']

    for key in keys_to_remove:
        if key in oracle:
            del oracle[key]

def main():
    reference_files = Path('./oracles/ref2').glob('*.yaml')
    for oracle_path in reference_files:
        print(oracle_path)
        oracle = yaml.load(oracle_path.read_text(encoding='utf-8'))
        fix_oracle(oracle, oracle_path.name)


if __name__ == '__main__':
    main()
