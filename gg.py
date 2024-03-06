import os 

os.system("pip install -U git+https://github.com/Rapptz/discord.py")
os.system("pip install git+https://github.com/oliver-ni/discord-ext-menus-views")
os.system("pip install git+https://github.com/oliver-ni/Flag-Parsing")

gg=["motor", 
"umongo",
"pymongo",
"durations-nlp",
"jishaku",
"suntime",
"structlog",
"dnspython",
"aioredis==1.3.1",
"fluent.runtime",
"expiringdict",
"aioredis_lock",
"geocoder",
"colorthief",
"pillow",
"jishaku",
"humanfriendly"
   ]

for i in gg:
  os.system(f"pip install {i}")
print("Done")