import json
from operator import ge
import os
from typing import List
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

def get_tran(name: str) -> str:
    if name not in name_tran:
        return name
    return name_tran[name]

def get_cost_per_second(name: str, num: float):
    rec = []
    ingres = []
    rec.append([f'{get_tran(name)}({name})', num])

    if name not in recipe_json:
        return rec

    recipe = recipe_json[name]
    ingreJson = []
    if 'ingredients' in recipe :
        ingreJson = recipe['ingredients']
    elif 'normal' in recipe:
        ingreJson = recipe['normal']['ingredients']
    else:
        return rec

    result_count = 1
    if 'result_count' in recipe:
        result_count = recipe['result_count']
    elif 'results' in recipe:
        result_count = recipe['results'][0]['amount']

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
        sub_ingredients = get_cost_per_second(ingredients_name, value)
        ingres.append(sub_ingredients)

    if len(ingres) > 0:
        rec.append(ingres)
    return rec

def printRecipe(recipe, depth):
    all = dict()
    prefix = '-'*depth
    if len(recipe)  <= 0 or len(recipe[0]) <= 0: 
        return
    name = recipe[0][0]
    num = recipe[0][1]
    print(f'{prefix}{name} x {num:.2f}')
    all[name] = num
    if len(recipe) > 1:
        for i in recipe[1]:
            sub = printRecipe(i, depth + 1)
            for k in sub:
                if k in all:
                    all[k] += sub[k]
                else:
                    all[k] = sub[k]
    if depth == 0:
        print('Total:')
        for k in all:
            print(f'{k} x {all[k]:.2f}')
    return all

if __name__ == '__main__':
    load()
    recipe = get_cost_per_second('production-science-pack', 1)
    printRecipe(recipe, 0)

