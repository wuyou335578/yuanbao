# -*- coding: utf-8 -*-
"""
快捷切换模组 —— 工具类型与方块匹配规则
单独抽出来方便你自己加规则，不用动主逻辑。
"""

# ---------- 工具类型 ----------
PICKAXE = "pickaxe"
AXE = "axe"
SHOVEL = "shovel"
SWORD = "sword"
SHEARS = "shears"

# ---------- 物品名后缀 -> 工具类型 ----------
# 注意顺序：_pickaxe 必须在 _axe 之前判断（虽然二者不冲突，保持清晰）
TOOL_SUFFIX = [
    ("_pickaxe", PICKAXE),
    ("_axe", AXE),
    ("_shovel", SHOVEL),
    ("_sword", SWORD),
    ("_hoe", None),      # 锄头不参与自动切换
    ("shears", SHEARS),
]

# ---------- 材质优先级（越大越好） ----------
MATERIAL_RANK = {
    "netherite": 6,
    "diamond": 5,
    "iron": 4,
    "golden": 3,
    "stone": 2,
    "wooden": 1,
}

# ---------- 方块关键字 -> 需要的工具 ----------
# 用「方块 identifier 的子串」匹配，例如 minecraft:stone 命中 "stone"
PICKAXE_BLOCKS = [
    "stone", "ore", "deepslate", "cobblestone", "andesite", "diorite",
    "granite", "brick", "nether_brick", "quartz", "obsidian", "netherrack",
    "basalt", "blackstone", "terracotta", "concrete", "anvil", "rail",
    "observer", "piston", "redstone_block", "iron_block", "gold_block",
    "diamond_block", "emerald_block", "lapis_block", "coal_block",
    "netherite_block", "prismarine", "purpur", "end_stone", "sandstone",
    "furnace", "hopper", "dropper", "dispenser", "cauldron", "lantern",
]

AXE_BLOCKS = [
    "log", "wood", "planks", "crafting_table", "chest", "barrel",
    "bookshelf", "fence", "door", "sign", "trapdoor", "ladder",
    "banner", "composter", "note_block", "jukebox", "lectern",
    "cartography_table", "smithing_table", "loom", "beehive",
]

SHOVEL_BLOCKS = [
    "dirt", "sand", "gravel", "clay", "grass", "snow", "soul_sand",
    "mud", "farmland", "podzol", "mycelium", "coarse_dirt",
    "rooted_dirt", "path",
]

SWORD_BLOCKS = [
    "cobweb", "bamboo",
]

SHEARS_BLOCKS = [
    "wool", "leaves", "vine", "glow_lichen",
]

# ---------- 武器（用于战斗自动切换） ----------
WEAPON_KEYWORDS = [
    "sword", "axe", "trident",
]

# 盾牌（可选：受伤时优先切盾——默认关闭，见 SWITCH_SHIELD_FIRST）
SHIELD_KEYWORDS = ["shield"]
