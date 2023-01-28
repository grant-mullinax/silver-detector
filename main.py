import requests

tiers = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8']
materials = ['WOOD', 'PLANKS']
qualities = ['', '_LEVEL1@1', '_LEVEL2@2', '_LEVEL3@3', '_LEVEL4@4']

items = []
for material in materials:
    for tier in tiers:
        for quality in qualities:
            if tier in ['T2', 'T3'] and quality != '':
                continue
            items.append(tier + '_' + material + quality)


r = requests.get('https://www.albion-online-data.com/api/v2/stats/prices/' +
                 ','.join(items) +
                 '.json?locations=fortsterling')

print(r)
