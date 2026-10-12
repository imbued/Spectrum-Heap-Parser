#!/usr/bin/env python3
"""
Majora's Mask actor heap dump cleaner (for mzxrules' Spectrum output).

Usage:
    python mm_heap.py dump.txt          # read a file
    python mm_heap.py -c                # read straight from the clipboard
    python mm_heap.py                   # paste the dump, then Ctrl-D (Ctrl-Z + Enter on Windows)

Actor names/descriptions are built in (from the CloudModding MM "Actor List (Variables)" page).
Optionally pass --actors PATH (saved wiki text) to override/extend them.
"""
import argparse
import os
import re
import sys
from collections import defaultdict

HEX = r"[0-9A-Fa-f]+"
RE_LINK = re.compile(rf"^\s*({HEX}):({HEX})\s+LINK\s+(F\s+)?SIZE\s+({HEX})\s+NEXT\s+({HEX})\s+PREV\s+({HEX})")
RE_AI = re.compile(
    rf"^\s*({HEX}):({HEX})\s+AI\s+({HEX}):\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+"
    rf"\(\s*(\S+)\s+(\S+)\s+(\S+)\s*\)\s+(\S+)\s+(\S+)\s+(\S+)"
)
RE_AF = re.compile(
    rf"^\s*({HEX}):({HEX})\s+AF\s+({HEX}):\s+(\S+)\s+(\S+)\s+FILE:\s*({HEX}):({HEX})\s+INIT\s+({HEX}):({HEX})"
)
RE_IDENT = re.compile(r"[A-Za-z_]\w*")


def h(s):
    return int(s, 16)


# "ID Name|Description"  (MM actor list, CloudModding wiki)
ACTOR_TABLE = """0000 player_actor|Player
0001 En_Test|
0002 En_GirlA|Shop Inventory Data
0003 En_Part|
0004 En_Light|Flame
0005 En_Door|Wooden Door
0006 En_Box|Treasure Chest
0007 En_Pametfrog|Gekko and Snapper Mini-Boss
0008 En_Okuta|Octorok (Enemy)
0009 En_Bom|Powder Keg
000A En_Wallmas|Wallmaster
000B En_Dodongo|Dodongo
000C En_Firefly|Keese
000D En_Horse|Child Epona (Cutscenes)
000E En_Item00|Collectible Items
000F En_Arrow|Arrow
0010 En_Elf|Healing Fairy & Tatl (Gameplay)
0011 En_Niw|Cucco (Friendly)
0012 En_Tite|Tektite
0014 En_Peehat|Peahat
0015 En_Butte|Butterfly
0016 En_Insect|Bug
0017 En_Fish|Fish
0018 En_Holl|Room Transition Plane
0019 En_Dinofos|Dinolfos
001A En_Hata|Flagpole
001B En_Zl1|Child Zelda [OoT]
001C En_Viewer|
001D En_Bubble|Shabom
001E Door_Shutter|Door Shutter
0020 En_Boom|Zora Fins
0021 En_Torch2|Elegy Statues
0022 En_Minifrog|Frog I [?]
0024 En_St|Skulltula
0026 En_A_Obj|Directional Sign & Square Sign [Early]
0027 Obj_Wturn|Stone Tower Temple Inverter
0028 En_River_Sound|Sound Effects I
002A En_Ossan|
002D En_Famos|Death Armos
002F En_Bombf|Bomb Flower
0032 En_Am|Armos
0033 En_Dekubaba|Deku Baba
0034 En_M_Fire1|Deku Nut Effect
0035 En_M_Thunder|Spin Attack & Sword Beam Effects
0036 Bg_Breakwall|
0038 Door_Warp1|Blue Warp
0039 Obj_Syokudai|Torch Stand (Generic)
003A Item_B_Heart|Heart Container (Boss Lairs)
003B En_Dekunuts|Mad Scrub (Field Enemy)
003C En_Bbfall|Red Bubble
003D Arms_Hook|Hookshot
003E En_Bb|Blue Bubble
003F Bg_Keikoku_Spr|Fountain Water
0041 En_Wood02|Trees & Bushes
0043 En_Death|Gomess
0044 En_Minideath|Gomess' Bats
0047 En_Vm|Beamos
0048 Demo_Effect|
0049 Demo_Kankyo|Environment Effects
004A En_Floormas|Floormaster
004C En_Rd|ReDead
004D Bg_F40_Flift|Stone Tower Temple Elevator [Early]
004E Bg_Heavy_Block|Golden Gauntlets Rock
004F Obj_Mure|Fish, Bugs, Butterflies
0050 En_Sw|Skullwalltula
0051 Object_Kankyo|
0054 En_Horse_Link_Child|Child Epona (Gameplay)
0055 Door_Ana|Grotto Hole
005B En_Encount1|
005C Demo_Tre_Lgt|Treasure Chest Glow
005F En_Encount2|Majora Balloon (Astral Observatory)
0060 En_Fire_Rock|Rock & Beam of Light [OoT]
0061 Bg_Ctower_Rot|Clock Tower Helix Path
0062 Mir_Ray|Mirror Shield Light Ray I [?]
0064 En_Sb|Shellblade
0065 En_Bigslime|Mad Jelly
0066 En_Karebaba|Wilted Deku Baba & Mini Baba
0067 En_In|Gorman Bros.
0069 En_Ru|Adult Ruto [OoT]
006A En_Bom_Chu|Bombchu
006B En_Horse_Game_Check|
006C En_Rr|Like Like
0073 En_Fr|
0079 En_Fishing|Fishing Pond & Proprietor [OoT]
007A Obj_Oshihiki|Pushblock
007B Eff_Dust|Spin Attack Charge Particles
007C Bg_Umajump|Horse Jumping Fence
007D Arrow_Fire|Fire Arrow
007E Arrow_Ice|Ice Arrow
007F Arrow_Light|Light Arrow
0080 Item_Etcetera|
0081 Obj_Kibako|Wooden Crate (Small)
0082 Obj_Tsubo|Pot
0084 En_Ik|Iron Knuckle
0089 Demo_Shd|
008A En_Dns|Deku Scrub Guard (Royal Chamber)
008B Elf_Msg|
008C En_Honotrap|
008D En_Tubo_Trap|Flying Pot
008E Obj_Ice_Poly|Ice Sparkle Effect
008F En_Fz|Freezard
0090 En_Kusa|Single Bush/Grass
0091 Obj_Bean|Magic Bean Plant
0092 Obj_Bombiwa|Bombable Rock
0093 Obj_Switch|Switches
0095 Obj_Lift|Dampé's House Elevator
0096 Obj_Hsblock|Stone Hookshot Pillar
0097 En_Okarina_Tag|Ocarina Song Spot
0099 En_Goroiwa|Snowball & Rolling Boulder [?]
009C En_Daiku|Carpenter (Clock Town)
009D En_Nwc|Cucco Chick
009E Item_Inbox|
009F En_Ge1|Pirate Lieutenant
00A0 Obj_Blockstop|
00A1 En_Sda|Dynamic Shadow
00A2 En_Clear_Tag|
00A4 En_Gm|Gorman
00A5 En_Ms|Magic Bean Seller
00A6 En_Hs|Grog
00A7 Bg_Ingate|Boat Cruise Canoe
00A8 En_Kanban|Square Sign
00AA En_Attack_Niw|Cucco (Attacking)
00AE En_Mk|Marine Scientist
00AF En_Owl|Owl
00B0 En_Ishi|Rock
00B1 Obj_Hana|Orange Graveyard Flower
00B2 Obj_Lightswitch|Sun Switch
00B3 Obj_Mure2|Grass & Rock Cluster
00B5 En_Fu|Honey & Darling (Gameplay)
00B8 En_Stream|Water Spout
00B9 En_Mm|Rock Sirloin
00BC En_Weather_Tag|
00BD En_Ani|Part-Timer
00BF En_Js|Moon Child
00C4 En_Okarina_Effect|Song of Storms Effect I [?]
00C5 En_Mag|Title Logo
00C6 Elf_Msg2|
00C7 Bg_F40_Swlift|Stone Tower Temple Platform [Early]
00CA En_Kakasi|Scarecrow
00CB Obj_Makeoshihiki|
00CC Oceff_Spot|Sun's Song Effect
00CE En_Torch|Treasure Chest (Grotto)
00D0 Shot_Sun|
00D3 Obj_Roomtimer|
00D4 En_Ssh|Cursed Skulltula Man
00D6 Oceff_Wipe|Song of Time Effect
00D7 Oceff_Storm|Song of Storms Effect II [?]
00D8 Obj_Demo|Cutscene Trigger
00D9 En_Minislime|Jelly Droplets
00DA En_Nutsball|Deku Nut Projectile
00DF Oceff_Wipe2|Epona's Song Effect
00E0 Oceff_Wipe3|Saria's Song Effect
00E2 En_Dg|Dog (Generic)
00E3 En_Si|Gold Skulltula Token
00E4 Obj_Comb|Beehive
00E5 Obj_Kibako2|Wooden Crate (Large)
00E7 En_Hs2|
00E8 Obj_Mure3|Rupee Cluster
00E9 En_Tg|Honey & Darling (Cutscenes)
00EC En_Wf|Wolfos (Field Enemy)
00ED En_Skb|Stalchild (Generic)
00EF En_Gs|Gossip Stone
00F0 Obj_Sound|Sound Effects II
00F1 En_Crow|Guay (Field Enemy)
00F3 En_Cow|Cow
00F6 Oceff_Wipe4|Scarecrow's Song Effect
00F8 En_Zo|Zora [Early]
00F9 Obj_Makekinsuta|Gold Skulltula in soft soil
00FA En_Ge3|Aveil
00FC Obj_Hamishi|Bronze Boulder
00FD En_Zl4|
00FE En_Mm2|Postman's Letter to Himself
0100 Door_Spiral|
0102 Obj_Pzlblock|Majora Pushblock
0103 Obj_Toge|Blade Trap
0105 Obj_Armos|Armos Statue
0106 Obj_Boyo|Bumper
0109 En_Grasshopper|Dragonfly
010B Obj_Grass|
010C Obj_Grass_Carry|
010D Obj_Grass_Unit|Grass Cluster
0110 Bg_Fire_Wall|
0111 En_Bu|
0112 En_Encount3|Circle of Light [?]
0113 En_Jso|Garo Master I [?]
0114 Obj_Chikuwa|Falling Block Row
0115 En_Knight|Igos du Ikana & Henchmen [?]
0116 En_Warp_tag|Warp to Trial Entrance
0117 En_Aob_01|Mamamu Yan
0118 En_Boj_01|
0119 En_Boj_02|
011A En_Boj_03|
011B En_Encount4|
011C En_Bom_Bowl_Man|Bomber I [?]
011D En_Syateki_Man|Shooting Gallery Proprietors [?]
011F Bg_Icicle|Icicle
0120 En_Syateki_Crow|Guay (Shooting Gallery)
0121 En_Boj_04|
0122 En_Cne_01|Thin Woman in Blue Dress [OoT]
0123 En_Bba_01|Bomb Shop Proprietor's Mother [Early]
0124 En_Bji_01|Shikashi
0125 Bg_Spdweb|Spiderweb
0128 En_Mt_tag|
0129 Boss_01|Odolwa
012A Boss_02|Twinmold
012B Boss_03|Gyorg
012C Boss_04|Wart
012D Boss_05|Bio Deku Baba
012E Boss_06|Igos du Ikana [?]
012F Boss_07|Majora
0130 Bg_Dy_Yoseizo|Great Fairy
0132 En_Boj_05|
0135 En_Sob1|
0138 En_Go|Goron (Generic) [?]
013A En_Raf|Carnivorous Lilypad
013B Obj_Funen|Stone Tower Smoke Plume [Early]
013C Obj_Raillift|Elevator (Deku Palace & Woodfall Temple) [?]
013D Bg_Numa_Hana|Wooden Flower
013E Obj_Flowerpot|Potted Plant
013F Obj_Spinyroll|Spiked Log (Horizontal)
0140 Dm_Hina|Boss Remains
0141 En_Syateki_Wf|Wolfos (Shooting Gallery)
0142 Obj_Skateblock|Ice Pushblock
0143 Obj_Iceblock|Frozen Enemy Ice Block
0144 En_Bigpamet|Snapper (Mini-Boss)
0145 En_Syateki_Dekunuts|Mad Scrub (Shooting Gallery)
0146 Elf_Msg3|
0147 En_Fg|Frog II [?]
0148 Dm_Ravine|Tree Trunk
0149 Dm_Sa|
014A En_Slime|Chuchu
014B En_Pr|Desbreko
014C Obj_Toudai|Clock Tower Spotlight
014D Obj_Entotu|Clock Town 2D Chimney Backdrop
014E Obj_Bell|Stock Pot Inn Bell
014F En_Syateki_Okuta|Octorok (Shooting Gallery)
0151 Obj_Shutter|West Clock Town Bank Shutter
0152 Dm_Zl|Child Zelda (Cutscenes)
0153 En_Elfgrp|Group of Stray Fairies
0154 Dm_Tsg|
0155 En_Baguo|Nejiron
0156 Obj_Vspinyroll|Spiked Log (Vertical)
0157 Obj_Smork|Romani Ranch Chimney Smoke
0158 En_Test2|
0159 En_Test3|Kafei
015A En_Test4|Three-Day Timer
015B En_Bat|Bad Bat
015C En_Sekihi|Mikau's Grave & Song Pedestals [Early]
015D En_Wiz|Wizzrobe
015E En_Wiz_Brock|Wizzrobe Warp Platform
015F En_Wiz_Fire|Wizzrobe Fire Attack
0160 Eff_Change|Camera Refocuser
0161 Dm_Statue|Elegy Statue Light Beam [?]
0162 Obj_Fireshield|Circle of Flames
0163 Bg_Ladder|Ladder
0164 En_Mkk|Black & White Boes
0165 Demo_Getitem|Great Fairy's Mask & Great Fairy's Sword
0167 En_Dnb|
0168 En_Dnh|Boat Cruise Target Spot
0169 En_Dnk|Hallucinatory Mad Scrubs
016A En_Dnq|Deku King
016C Bg_Keikoku_Saku|Spiked Iron Fence
016D Obj_Hugebombiwa|Powder Keg Boulder
016E En_Firefly2|
016F En_Rat|Real Bombchu
0170 En_Water_Effect|Dripping Water
0171 En_Kusa2|Keaton Grass Cluster
0172 Bg_Spout_Fire|Proximity-Activated Fire Wall
0174 Bg_Dblue_Movebg|Great Bay Temple Gears
0175 En_Dy_Extra|Great Fairy Healing Beam
0176 En_Bal|Tingle (Gameplay)
0177 En_Ginko_Man|Bank Teller
0178 En_Warp_Uzu|Pirates' Fortress Telescope
0179 Obj_Driftice|Drifting Ice Platform
017A En_Look_Nuts|Deku Scrub Guard (Palace Gardens)
017B En_Mushi2|
017C En_Fall|
017D En_Mm3|Postman (Counting Game)
017E Bg_Crace_Movebg|Deku Shrine Door Shutters
017F En_Dno|Deku Butler
0180 En_Pr2|Skullfish
0181 En_Prz|Skullfish (Defeated)
0182 En_Jso2|Garo Master II [?]
0183 Obj_Etcetera|Deku Flower
0184 En_Egol|Eyegore
0185 Obj_Mine|Spiked Metal Mine
0186 Obj_Purify|Poisoned/Purified Water Elements
0187 En_Tru|Koume (Gameplay) [?]
0188 En_Trt|Kotake (No Broom) [?]
018B En_Test5|Spring Water
018C En_Test6|Song of Time Cutscene Effects
018D En_Az|Beaver Bros.
018E En_Estone|Eyegore Rubble
018F Bg_Hakugin_Post|Snowhead Temple Central Pillar
0190 Dm_Opstage|Opening Cutscene Objects
0191 Dm_Stk|Skull Kid
0192 Dm_Char00|Tatl & Tael (Cutscenes) II [?]
0193 Dm_Char01|Woodfall Temple Rises Cutscene Objects
0194 Dm_Char02|Ocarina of Time & Majora's Mask (Clock Tower Roof) [?]
0195 Dm_Char03|Happy Mask Salesman (Cutscenes)
0196 Dm_Char04|Tatl & Tael (Cutscenes) I [?]
0197 Dm_Char05|Masks (Cutscenes)
0198 Dm_Char06|Mountain Village Cutscene Objects [?]
0199 Dm_Char07|Milk Bar Stage (Cutscenes)
019A Dm_Char08|Turtle (Cutscenes) [?]
019B Dm_Char09|Giant Bee (Cutscenes)
019C Obj_Tokeidai|Clock Tower & Light Beam
019E En_Mnk|Monkey
019F En_Egblock|Eyegore Block
01A0 En_Guard_Nuts|Deku Scrub Guard (Palace Entrance) [?]
01A1 Bg_Hakugin_Bombwall|Snowhead Temple Bombable Wall
01A2 Obj_Tokei_Tobira|Clock Tower Doors
01A3 Bg_Hakugin_Elvpole|Snowhead Temple Punchable Pillar Inserts
01A4 En_Ma4|Romani I [?]
01A5 En_Twig|Beaver Race Ring
01A6 En_Po_Fusen|Poe Balloon
01A7 En_Door_Etc|
01A8 En_Bigokuta|Big Octo
01A9 Bg_Icefloe|Ice Arrow Platform
01AA Obj_Ocarinalift|Triforce Elevator
01AB En_Time_Tag|
01AC Bg_Open_Shutter|Deku Emblem Door
01AD Bg_Open_Spot|Skull Kid Spotlights
01AE Bg_Fu_Kaiten|Honey & Darling's Shop Rotating Platform
01AF Obj_Aqua|Poured Water
01B0 En_Elforg|Stray Fairy
01B1 En_Elfbub|Stray Fairy Bubble
01B3 En_Fu_Mato|Honey & Darling's Shop Target
01B4 En_Fu_Kago|Honey & Darling's Shop Basket
01B5 En_Osn|Happy Mask Salesman (Gameplay)
01B6 Bg_Ctower_Gear|Clock Tower Gear
01B7 En_Trt2|Kotake (Broom) [?]
01B8 Obj_Tokei_Step|Clock Tower Roof Door
01B9 Bg_Lotus|Lilypad
01BA En_Kame|Snapper (Enemy)
01BB Obj_Takaraya_Wall|Treasure Chest Game Proximity-Activated Wall
01BC Bg_Fu_Mizu|Honey & Darling's Shop Moat
01BD En_Sellnuts|Business Scrub (Flying) [?]
01BE Bg_Dkjail_Ivy|Woodfall Prison Ivy
01C0 Obj_Visiblock|Lens of Truth Platform
01C1 En_Takaraya|Treasure Chest Game Employee
01C2 En_Tsn|Fisherman (Great Bay Village)
01C3 En_Ds2n|Potion Shop Proprietor (Updated) [OoT]
01C4 En_Fsn|Curiosity Shop Proprietor
01C5 En_Shn|Swamp Tourist Center Guide
01C7 En_Stop_heishi|Soldier (Gate Guard)
01C8 Obj_Bigicicle|Ice Block
01C9 En_Lift_Nuts|Deku Scrub Playground Employee
01CA En_Tk|Dampé
01CC Bg_Market_Step|West Clock Town Steps
01CD Obj_Lupygamelift|Deku Scrub Playground Elevator
01CE En_Test7|Song of Soaring Cutscene Activator
01CF Obj_Lightblock|Dissolvable Light Block
01D0 Mir_Ray2|Mirror Shield Reflectable Spotlight [?]
01D1 En_Wdhand|Dexihand
01D2 En_Gamelupy|Deku Scrub Playground Rupee
01D3 Bg_Danpei_Movebg|Dampé's House Objects
01D4 En_Snowwd|Snow-Covered Tree
01D5 En_Pm|Postman (Delivering Letters)
01D6 En_Gakufu|2D Music Staff
01D7 Elf_Msg4|
01D8 Elf_Msg5|
01D9 En_Col_Man|Piece of Heart
01DA En_Talk_Gibud|Gibdo (Ikana Well)
01DB En_Giant|Giant
01DC Obj_Snowball|Large Snowball
01DD Boss_Hakugin|Goht
01DE En_Gb2|Ghost Hut Proprietor
01DF En_Onpuman|Monkey Instrument Prompt
01E0 Bg_Tobira01|Goron Shrine Gate
01E1 En_Tag_Obj|
01E2 Obj_Dhouse|Dampé's House Facade
01E3 Obj_Hakaisi|Gravestone
01E4 Bg_Hakugin_Switch|Goron Switch
01E6 En_Snowman|Big & Small Eeno
01E7 TG_Sw|
01E8 En_Po_Sisters|Poe Sisters
01E9 En_Pp|Hiploop
01EA En_Hakurock|Goht Debris
01EB En_Hanabi|Fireworks
01EC Obj_Dowsing|
01ED Obj_Wind|Wind Funnel
01EE En_Racedog|Dog (Doggie Racetrack)
01EF En_Kendo_Js|Swordsman
01F0 Bg_Botihasira|Captain Keeta Race Gatepost
01F1 En_Fish2|Marine Research Lab Fish
01F2 En_Pst|Postbox
01F3 En_Poh|Poe
01F4 Obj_Spidertent|Tent-Shaped Spider Web
01F5 En_Zoraegg|Zora Egg
01F6 En_Kbt|Zubora
01F7 En_Gg|Darmani's Ghost I [?]
01F8 En_Maruta|Swordsman's School Practice Log
01F9 Obj_Snowball2|Small Snowball
01FA En_Gg2|Darmani's Ghost II [?]
01FB Obj_Ghaka|Darmani's Gravestone
01FC En_Dnp|Deku Princess
01FD En_Dai|Biggoron
01FE Bg_Goron_Oyu|Hot Spring Water
01FF En_Kgy|Gabora
0200 En_Invadepoh|
0201 En_Gk|Goron Elder's Son
0202 En_An|Anju (Gameplay)
0204 En_Bee|Giant Bee (Gameplay)
0205 En_Ot|Seahorse
0206 En_Dragon|Deep Python
0207 Obj_Dora|Swordsman's School Gong
0208 En_Bigpo|Big Poe
0209 Obj_Kendo_Kanban|Swordsman's School Wooden Board
020A Obj_Hariko|Cow Figurine
020B En_Sth|
020C Bg_Sinkai_Kabe|
020D Bg_Haka_Curtain|Beneath the Grave Curtain
020E Bg_Kin2_Bombwall|Oceanside Spider House Bombable Wall
020F Bg_Kin2_Fence|Oceanside Spider House Fireplace Grate
0210 Bg_Kin2_Picture|Oceanside Spider House Skull Kid Painting
0211 Bg_Kin2_Shelf|Oceanside Spider House Drawers & Bookshelf
0212 En_Rail_Skb|Circle of Stalchildren
0213 En_Jg|Goron Elder
0214 En_Tru_Mt|Koume (Boat Cruise) [?]
0215 Obj_Um|Cremia's Cart
0216 En_Neo_Reeba|Leever
0217 Bg_Mbar_Chair|Milk Bar Chair
0218 Bg_Ikana_Block|
0219 Bg_Ikana_Mirror|Stone Tower Temple Mirror
021A Bg_Ikana_Rotaryroom|Stone Tower Temple Rotating Room
021B Bg_Dblue_Balance|Great Bay Temple See-Saw
021C Bg_Dblue_Waterfall|Great Bay Temple Water Spout
021D En_Kaizoku|Pirate [?]
021E En_Ge2|Patrolling Pirate Guard
021F En_Ma_Yts|Romani II [?]
0220 En_Ma_Yto|Cremia
0221 Obj_Tokei_Turret|South Clock Town Objects
0222 Bg_Dblue_Elevator|Great Bay Temple Elevator
0223 Obj_Warpstone|Owl Statue
0224 En_Zog|Mikau
0225 Obj_Rotlift|Deku Moon Trial Rotating Platform
0226 Obj_Jg_Gakki|Goron Elder's Drum
0227 Bg_Inibs_Movebg|Twinmold's Lair Objects [?]
0228 En_Zot|Zora (Land)
0229 Obj_Tree|Fork-Branched Tree
022A Obj_Y2lift|Pirates' Fortress Mesh Elevator
022B Obj_Y2shutter|Pirates' Fortress Interior Door
022C Obj_Boat|Pirates' Fortress Boat
022D Obj_Taru|Barrel
022E Obj_Hunsui|Geyser
022F En_Jc_Mato|Boat Cruise Target
0230 Mir_Ray3|Mirror Shield Light Ray II [?]
0231 En_Zob|Japas
0232 Elf_Msg6|
0233 Obj_Nozoki|
0234 En_Toto|Toto
0235 En_Railgibud|Gibdo (Ikana Canyon)
0236 En_Baba|Bomb Shop Proprietor's Mother
0237 En_Suttari|Sakon
0238 En_Zod|Tijo
0239 En_Kujiya|Lottery Shop Kiosk
023A En_Geg|Don Gero
023B Obj_Kinoko|Mushroom Scent Cloud
023C Obj_Yasi|Palm Tree
023D En_Tanron1|Swarm of Moths
023E En_Tanron2|Wart's Bubbles
023F En_Tanron3|Gyorg's Fish
0240 Obj_Chan|Goron Village Chandelier
0241 En_Zos|Evan
0242 En_S_Goro|Goron (Goron Shrine & Bomb Shop) [?]
0243 En_Nb|Anju's Grandmother (Gameplay)
0244 En_Ja|Jugglers
0245 Bg_F40_Block|Stone Tower Temple Shifting Block
0246 Bg_F40_Switch|Elegy Statue Switch
0247 En_Po_Composer|Composer Brothers
0248 En_Guruguru|Guru-Guru
0249 Oceff_Wipe5|Sonata of Awakening Effect
024A En_Stone_heishi|Shiro
024B Oceff_Wipe6|Song of Soaring Effect
024C En_Scopenuts|Business Scrub (Telescope)
024D En_Scopecrow|Guay (Observatory Telescope)
024E Oceff_Wipe7|Song of Healing Effect
024F Eff_Kamejima_Wave|Turtle's Tsunami
0250 En_Hg|Pamela's Father (Cursed)
0251 En_Hgo|Pamela's Father (Normal)
0252 En_Zov|Lulu
0253 En_Ah|Anju's Mother (Gameplay)
0254 Obj_Hgdoor|Music Box House Cupboard Doors
0255 Bg_Ikana_Bombwall|Stone Tower Temple Bombable Floor Tile & Wall
0256 Bg_Ikana_Ray|Stone Tower Temple Light Ray [?]
0257 Bg_Ikana_Shutter|Stone Tower Temple Lattice Door
0258 Bg_Haka_Bombwall|Beneath the Grave Bombable Wall
0259 Bg_Haka_Tomb|Flat's Tomb
025A En_Sc_Ruppe|Large Rotating Green Rupee
025B Bg_Iknv_Doukutu|Sharp's Cave
025C Bg_Iknv_Obj|Ikana Canyon Objects
025D En_Pamera|Pamela
025E Obj_HsStump|Hookshot Stump
025F En_Hidden_Nuts|Mad Scrub (Sleeping)
0260 En_Zow|Zora (Water)
0261 En_Talk|
0262 En_Al|Madame Aroma (Gameplay)
0263 En_Tab|Mr. Barten
0264 En_Nimotsu|Bomb Shop Bag
0265 En_Hit_Tag|
0266 En_Ruppecrow|Guay (Circling Clock Town)
0267 En_Tanron4|Flock of Seagulls
0268 En_Tanron5|
0269 En_Tanron6|Swarm of Giant Bees
026A En_Daiku2|Carpenter (Milk Road)
026B En_Muto|Mutoh (Gameplay)
026C En_Baisen|Viscen
026D En_Heishi|Soldier (Mayor's House)
026E En_Demo_heishi|Soldier (Cutscenes) I [?]
026F En_Dt|Mayor Dotour (Gameplay)
0270 En_Cha|Laundry Pool Bell [?]
0271 Obj_Dinner|Cremia & Romani's Dinner
0272 Eff_Lastday|Moon Fall Effects
0273 Bg_Ikana_Dharma|Ancient Castle of Ikana Punchable Pillar Segments
0274 En_Akindonuts|Traveling Business Scrub
0275 Eff_Stk|Skull Kid Moon-Summoning Effects [?]
0276 En_Ig|Link the Goron
0277 En_Rg|Goron (Goron Racetrack)
0278 En_Osk|Igos du Ikana & Henchmen's Heads
0279 En_Sth2|
027A En_Yb|Kamaro
027B En_Rz|Rosa Sisters
027C En_Scopecoin|
027D En_Bjt|Hand in Toilet
027E En_Bomjima|Jim I [?]
027F En_Bomjimb|Jim II [?]
0280 En_Bombers|Bomber II [?]
0281 En_Bombers2|Bomber (Hideout Guard)
0282 En_Bombal|Majora Balloon (North Clock Town)
0283 Obj_Moon_Stone|Moon's Tear
0284 Obj_Mu_Pict|
0285 Bg_Ikninside|Ancient Castle of Ikana Objects [?]
0286 Eff_Zoraband|Blue Spotlight Effect
0287 Obj_Kepn_Koya|Gorman Track Buildings
0288 Obj_Usiyane|Cow Barn Roof (Exterior)
0289 En_Nnh|Deku Butler's Son
028A Obj_Kzsaku|Metal Portcullis
028B Obj_Milk_Bin|Chateau Romani Delivery Bottle
028C En_Kitan|Keaton
028D Bg_Astr_Bombwall|Astral Observatory Bombable Wall
028E Bg_Iknin_Susceil|Hot Checkered Ceiling [?]
028F En_Bsb|Captain Keeta
0290 En_Recepgirl|Mayor's Receptionist
0291 En_Thiefbird|Takkuri
0292 En_Jgame_Tsn|Fisherman (Fisherman's Jumping Game)
0293 Obj_Jgame_Light|Torch Stand (Fisherman's Jumping Game)
0294 Obj_Yado|Stockpot Inn Window
0295 Demo_Syoten|Ikana Canyon Curse Lifted Effects
0296 Demo_Moonend|Moon (Cutscenes)
0297 Bg_Lbfshot|Rainbow Hookshot Pillar
0298 Bg_Last_Bwall|Link Moon Trial Bombable & Climbable Walls
0299 En_And|Anju (Wedding Dress)
029A En_Invadepoh_Demo|
029B Obj_Danpeilift|Deku Shrine & Snowhead Temple Elevator [?]
029C En_Fall2|Falling Moon
029D Dm_Al|Madame Aroma (Cutscenes)
029E Dm_An|Anju Cutscene Animations
029F Dm_Ah|Anju's Mother (Cutscenes)
02A0 Dm_Nb|Anju's Grandmother (Cutscenes)
02A1 En_Drs|Wedding Dress Mannequin
02A2 En_Ending_Hero|Mayor Dotour (Cutscenes)
02A3 Dm_Bal|Tingle (Cutscenes)
02A4 En_Paper|Tingle Confetti
02A5 En_Hint_Skb|Stalchild (Oceanside Spider House)
02A6 Dm_Tag|
02A7 En_Bh|Brown Bird
02A8 En_Ending_Hero2|Viscen (Cutscenes)
02A9 En_Ending_Hero3|Mutoh (Cutscenes)
02AA En_Ending_Hero4|Soldier (Cutscenes) II [?]
02AB En_Ending_Hero5|Carpenter (Cutscenes)
02AC En_Ending_Hero6|
02AD Dm_Gm|
02AE Obj_Swprize|
02AF En_Invisible_Ruppe|
02B0 Obj_Ending|Epilogue Cutscene Objects
02B1 En_Rsn|Bomb Shop Proprietor
"""


def builtin_names():
    names = {}
    for line in ACTOR_TABLE.splitlines():
        line = line.strip()
        if not line:
            continue
        aid, rest = line.split(None, 1)
        name, _, desc = rest.partition("|")
        names[int(aid, 16)] = (name.strip(), desc.strip())
    return names


# ----------------------------------------------------------------- names
def load_names(path):
    names = {}
    if not path or not os.path.exists(path):
        return names
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^\s*Id:\s*([0-9A-Fa-f]{4})\s*$", line)
        if not m or i < 2:
            continue
        name, desc = lines[i - 2].strip(), lines[i - 1].strip()
        if not RE_IDENT.fullmatch(name):
            # blank lines may have been stripped from the copy: Name / Id
            if RE_IDENT.fullmatch(desc):
                name, desc = desc, ""
            else:
                continue
        names[int(m.group(1), 16)] = (name, desc)
    return names


def actor_label(names, aid):
    if aid in names:
        n, d = names[aid]
        return n, d
    return "?", ""


# ----------------------------------------------------------------- parse
def parse(text):
    nodes, content = [], {}
    for line in text.splitlines():
        m = RE_LINK.match(line)
        if m:
            s, e = h(m.group(1)), h(m.group(2))
            nodes.append(dict(start=s, bstart=e, hdr=e - s, free=bool(m.group(3)),
                              size=h(m.group(4)), next=h(m.group(5)), prev=h(m.group(6))))
            continue
        m = RE_AI.match(line)
        if m:
            content[h(m.group(1))] = dict(
                kind="AI", end=h(m.group(2)), id=h(m.group(3)), room=m.group(4),
                f1=m.group(5), f2=m.group(6), var=m.group(7),
                pos=(m.group(8), m.group(9), m.group(10)),
                rot=(m.group(11), m.group(12), m.group(13)))
            continue
        m = RE_AF.match(line)
        if m:
            content[h(m.group(1))] = dict(
                kind="AF", end=h(m.group(2)), id=h(m.group(3)), f1=m.group(4),
                count=h(m.group(5)), rom=(h(m.group(6)), h(m.group(7))),
                init=(h(m.group(8)), h(m.group(9))))
    nodes.sort(key=lambda n: n["start"])
    chains, cur = [], []
    for n in nodes:
        if n["prev"] == 0 and cur:
            chains.append(cur)
            cur = []
        cur.append(n)
    if cur:
        chains.append(cur)
    return chains, content


# ----------------------------------------------------------------- output
def sz(n):
    return f"0x{n:X}"


def render_chain(chain, content, names, out):
    stats = dict(used=0, free=0, free_blocks=0, largest_free=0, gaps=0)
    inst = defaultdict(lambda: dict(found=0, bytes=0, declared=None, ovl=None, rom=None))
    width = 64
    SIZE_COL = 6 + 2 + 4 + 2 + 4 + 2 + 22 + 1  # column where 'size' starts on AI/AF rows

    head = (f"CHAIN  nodes {chain[0]['start']:06X} .. {chain[-1]['bstart'] + chain[-1]['size']:06X}"
            f"   ({len(chain)} nodes)")
    out.append("=" * width)
    out.append(head)
    out.append("=" * width)

    for i, n in enumerate(chain):
        bs, be = n["bstart"], n["bstart"] + n["size"]
        c = content.get(bs)

        left = f"{n['start']:06X}  {'NODE':<4}  "
        left += "-" * (SIZE_COL - len(left) - 1) + " "
        out.append(left + f"size {sz(n['hdr'])} ".ljust(width - SIZE_COL, "-"))

        if n["free"]:
            body = f"------  ({sz(n['size'])} FREE)"
            stats["free"] += n["size"]
            stats["free_blocks"] += 1
            stats["largest_free"] = max(stats["largest_free"], n["size"])
        elif c:
            stats["used"] += n["size"]
            nm, desc = actor_label(names, c["id"])
            d = inst[c["id"]]
            if c["kind"] == "AI":
                d["found"] += 1
                d["bytes"] += n["size"]
                det = (f"{desc + ' | ' if desc else ''}room {c['room']} var {c['var']} "
                       f"pos ({c['pos'][0]}, {c['pos'][1]}, {c['pos'][2]}) "
                       f"rot {' '.join(c['rot'])}")
            else:
                d["declared"] = c["count"]
                d["ovl"] = n["size"]
                d["rom"] = c["rom"]
                det = desc
            body = (f"{bs:06X}  {c['kind']:<4}  {c['id']:04X}  {nm:<22} "
                    f"size {sz(n['size']):<8} {det}").rstrip()
        else:
            body = f"        ({sz(n['size'])})"
            stats["used"] += n["size"]
        out.append(body)

        if i + 1 < len(chain):
            nx = chain[i + 1]
            gap = nx["start"] - be
            if gap > 0:
                stats["gaps"] += gap
                out.append(f">>> GAP {be:06X}-{nx['start']:06X}  size {sz(gap)}")
            elif gap < 0:
                out.append(f">>> OVERLAP of {sz(-gap)} with next node")
            if n["next"] and (n["next"] & 0xFFFFFF) != nx["start"]:
                out.append(f">>> NEXT ptr {n['next']:08X} does not point at next node in dump "
                           f"({nx['start']:06X})")
    out.append("-" * width)
    return stats, inst


def render_summary(chain_stats, inst, names, out):
    out.append("")
    out.append("PER-ACTOR SUMMARY")
    out.append(f"{'ID':<5} {'NAME':<24} {'OVL SIZE':<16} {'INST':<9} {'INST BYTES':<16} NOTES")
    out.append("-" * 90)
    for aid in sorted(inst):
        d = inst[aid]
        nm, _ = actor_label(names, aid)
        ovl = sz(d["ovl"]) if d["ovl"] is not None else "-"
        decl = "?" if d["declared"] is None else str(d["declared"])
        notes = []
        if d["declared"] is not None and d["declared"] != d["found"]:
            notes.append("instance count != AF count (dump truncated?)")
        if d["ovl"] is None:
            notes.append("no AF in dump (gameplay_keep-style or not shown)")
        out.append(f"{aid:04X}  {nm:<24} {ovl:<16} {str(d["found"])+"/"+decl:<9} {sz(d['bytes']):<16} {'; '.join(notes)}")

    tot = defaultdict(int)
    for s in chain_stats:
        for k in ("used", "free", "free_blocks", "gaps"):
            tot[k] += s[k]
    largest = max((s["largest_free"] for s in chain_stats), default=0)
    out.append("")
    out.append(f"allocated blocks: {sz(tot['used'])}")
    out.append(f"free blocks     : {sz(tot['free'])} in {tot['free_blocks']} block(s), largest {sz(largest)}")
    out.append(f"unaccounted gaps: {sz(tot['gaps'])}")


# ----------------------------------------------------------------- main
def read_input(args):
    if args.clipboard:
        import tkinter
        r = tkinter.Tk()
        r.withdraw()
        try:
            return r.clipboard_get()
        finally:
            r.destroy()
    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as f:
            return f.read()
    if sys.stdin.isatty():
        print("Paste the dump, then press Ctrl-D (Ctrl-Z then Enter on Windows):", file=sys.stderr)
    return sys.stdin.read()


def main():
    ap = argparse.ArgumentParser(description="Clean up Spectrum MM actor heap dumps.")
    ap.add_argument("file", nargs="?", help="dump file (omit to read stdin)")
    ap.add_argument("-c", "--clipboard", action="store_true", help="read dump from clipboard")
    ap.add_argument("-a", "--actors", help="optional saved wiki actor list to override built-in names")
    ap.add_argument("--all", action="store_true", help="also print chains with no AI/AF entries")
    ap.add_argument("--summary", action="store_true", help="also print per-actor summary and heap totals")
    args = ap.parse_args()

    names = builtin_names()
    if args.actors:
        if os.path.exists(args.actors):
            names.update(load_names(args.actors))
        else:
            print(f"[!] {args.actors} not found, using built-in names.", file=sys.stderr)

    chains, content = parse(read_input(args))
    if not chains:
        sys.exit("No LINK nodes found in input.")

    out, all_stats = [], []
    all_inst = defaultdict(lambda: dict(found=0, bytes=0, declared=None, ovl=None, rom=None))
    for chain in chains:
        if not args.all and not any(content.get(n["bstart"]) for n in chain):
            continue
        stats, inst = render_chain(chain, content, names, out)
        out.append("")
        all_stats.append(stats)
        for aid, d in inst.items():
            t = all_inst[aid]
            t["found"] += d["found"]
            t["bytes"] += d["bytes"]
            if d["declared"] is not None:
                t["declared"], t["ovl"], t["rom"] = d["declared"], d["ovl"], d["rom"]
    if args.summary and all_stats:
        render_summary(all_stats, all_inst, names, out)
    print("\n".join(out))


if __name__ == "__main__":
    main()