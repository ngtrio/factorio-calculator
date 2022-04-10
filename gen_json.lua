require("dataloader")
require("util")

require("prototypes.item")
require("prototypes.fluid")
require("prototypes.recipe")

local json=require("lib.json")
local f = io.open("data.json", "w")

f:write(json.encode(data.raw))
f:close()