import json
import os
from PIL import Image

recipe_json = dict()
item_json = dict()

name_tran = dict()
name_set = set()

def load_data():
    with open('data.json', 'r') as f:
        js = json.load(f)

        for type in js:
            if type != 'recipe':
                for name in js[type]:
                    item_json[name] = js[type][name]
        for name in js['recipe']:
            recipe_json[name] = js['recipe'][name]
            if name not in item_json:
                print(f'[Warn] {name} not a item')

        print(f'load {len(item_json)} items')
        print(f'load {len(recipe_json)} recipes')

def load_name():
    for name in recipe_json:
        name_set.add(name)

    for name in item_json:
        name_set.add(name)

def load_tran():
    with open('./data/base/locale/zh-CN/base.cfg', 'r') as f:
        tran_temp = dict()
        for line in f.readlines():
            splits = line.split('=')
            if len(splits) == 2:
                tran_temp[splits[0]] = splits[1][:-1]

        for name in name_set:
            if name not in tran_temp:
                print(f'[WARN] {name} tran missing')
            else:
                name_tran[name] = tran_temp[name]

def load_icon():
    if not os.path.exists('./images'):
        os.mkdir('./images')

    for name in item_json:
        path = ''
        # icon_mipmaps = item_json[name]['icon_mipmaps']
        # icon_size = item_json[name]['icon_size']
        if 'icon' in item_json[name]:
            path = item_json[name]['icon'].replace('__base__', './data/base')
        else:
            path = item_json[name]['icons'][0]['icon'].replace('__base__', './data/base')

        dest = f'./images/{name}.png'
        if not os.path.exists(dest):
            with Image.open(path) as img:
                box = (0, 0, 64, 64)
                img.crop(box).save(dest)

def load():
    load_data()
    load_name()
    load_tran()
    load_icon()

def _get_tran(name: str) -> str:
    if name not in name_tran:
        return name
    return name_tran[name]

def get_cost_per_second(name: str, num: float, furnace: str, assembling_machine: str, drill: str, diff: str):
    rec = []
    ingres = []

    if name not in recipe_json:
        if name in ['stone', 'copper-ore', 'coal', 'iron-ore']:
            rec.append([_get_tran_name(name), num, _get_tran_name(drill), _get_mining_drill_num(num, drill)])
        else:
            rec.append([_get_tran_name(name), num, f'{name}-TODO', 1])
        return rec

    recipe = recipe_json[name]

    energy_required = 0.5
    if 'energy_required' in recipe:
        energy_required = recipe['energy_required']
    elif diff in recipe:
        if 'energy_required' in recipe[diff]:
            energy_required = recipe[diff]['energy_required']

    result_count = 1
    if 'result_count' in recipe:
        result_count = recipe['result_count']
    elif 'results' in recipe:
        result_count = recipe['results'][0]['amount']
    elif diff in recipe:
        if 'result_count' in recipe[diff]:
            result_count = recipe[diff]['result_count']

    if 'category' in recipe:
        # TODO other category
        if recipe['category'] == 'smelting':
            rec.append([_get_tran_name(name), num, _get_tran_name(furnace), _get_furnace_num(num, energy_required, result_count, furnace)])
        elif recipe['category'] == 'chemistry':
            rec.append([_get_tran_name(name), num, _get_tran_name('chemical-plant'), _get_chemical_plant_num(num, energy_required, result_count)])
        else:
            rec.append([_get_tran_name(name), num, _get_tran_name(assembling_machine), _get_assemble_mechine_num(num, energy_required, result_count, assembling_machine)])
    else:
        rec.append([_get_tran_name(name), num, _get_tran_name(assembling_machine), _get_assemble_mechine_num(num, energy_required, result_count, assembling_machine)])

    ingreJson = []
    if 'ingredients' in recipe :
        ingreJson = recipe['ingredients']
    elif diff in recipe:
        ingreJson = recipe[diff]['ingredients']
    else:
        return rec

    for i in ingreJson:
        ingredients_name = ''
        ingredients_num = 0
        if type(i) is list:
            ingredients_name = i[0]
            ingredients_num = i[1]
        elif type(i) is dict:
            ingredients_name = i['name']
            ingredients_num = i['amount']

        
        value = ingredients_num / result_count * num
        sub_ingredients = get_cost_per_second(ingredients_name, value, furnace, assembling_machine, drill, diff)
        ingres.append(sub_ingredients)

    if len(ingres) > 0:
        rec.append(ingres)
    return rec

def printRecipe(recipe, depth):
    item = dict()
    factory = dict()
    prefix = '-'*depth
    if len(recipe)  <= 0 or len(recipe[0]) <= 0: 
        return
    name = recipe[0][0]
    num = recipe[0][1]
    factory_name = recipe[0][2]
    factory_num = recipe[0][3]
    print(f'{prefix}{name} x {num:.2f} with {factory_name} x {factory_num:.2f}')
    item[name] = num
    factory[factory_name] = factory_num
    if len(recipe) > 1:
        for i in recipe[1]:
            sub_item, sub_factory = printRecipe(i, depth + 1)
            for k in sub_item:
                if k in item:
                    item[k] += sub_item[k]
                else:
                    item[k] = sub_item[k]
            for k in sub_factory:
                if k in factory:
                    factory[k] += sub_factory[k]
                else:
                    factory[k] = sub_factory[k]
    if depth == 0:
        print('Total Items:')
        for k in item:
            print(f'{k} x {item[k]:.2f}')
        print('Total Factories:')
        for k in factory:
            print(f'{k} x {factory[k]:.2f}')
    return item, factory

def _get_tran_name(name: str) -> str:
    return f'{_get_tran(name)}({name})'

def _get_furnace_num(item_num: float, energy_required: float, result_count: float, furnace: str) -> float:
    energy = 1
    if furnace == 'stone-furnace':
        energy = 1
    elif furnace == 'steel-furnace':
        energy = 2
    elif furnace == 'electric-furnace':
        energy = 2
    else:
        print('[ERROR] invalid furnace')
    return item_num / energy * energy_required / result_count

def _get_assemble_mechine_num(item_num: float, energy_required: float, result_count: float, machine: str) -> float:
    energy = 0.5
    if machine == 'assembling-machine-1':
        energy = 0.5
    elif machine == 'assembling-machine-2':
        energy = 0.75
    elif machine == 'assembling-machine-3':
        energy = 1.25
    else:
        print('[ERROR] invalid assembling machine')
    return item_num / energy * energy_required / result_count

def _get_mining_drill_num(item_num: float, drill: str) -> float:
    if drill == 'burner-mining-drill':
        return item_num / 0.25
    elif drill == 'electric-mining-drill':
        return item_num / 0.5
    else:
        print('[ERROR] invalid drill')
        return 0

def _get_chemical_plant_num(item_num: float, energy_required: float, result_count: float) -> float:
    return item_num * energy_required / result_count

if __name__ == '__main__':
    load()
    recipe = get_cost_per_second('production-science-pack', 1, 'steel-furnace', 'assembling-machine-1', 'electric-mining-drill', 'normal')
    printRecipe(recipe, 0)

